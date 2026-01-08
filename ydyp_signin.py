import os
import random
import re
import time
import requests
import json
import hashlib
import uuid
import random
from datetime import datetime, timezone, timedelta

# ================= 配置区域 =================
# 格式要求：BasicAuth#手机号#Token#x-yun-uni
# 多个账号用 & 符号连接，或换行

# 环境变量覆盖 (兼容青龙/本地环境变量)
if os.getenv("YDYP_CK"):
    ydypCK = os.getenv("YDYP_CK")

# --- 游戏配置 ---
# 既然互助成功会有5次机会，这里设置稍微大一点(比如8次)
# 脚本内部会根据服务器返回的剩余次数(curr)自动提前停止，不用担心多跑
GAME_TARGET_SUCC = 8   
GAME_DURATION = random.randint(420,650)    # 每局模拟耗时(秒)，建议300以上，太快容易被风控
GAME_SALT = "seedMdYYLIZfbCxg" # 游戏加密盐值
# ===========================================

ua = 'Mozilla/5.0 (Linux; Android 13; PDRM00 Build/TP1A.220905.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/108.0.5359.128 Mobile Safari/537.36 MCloudApp/12.4.3'

class YP:
    def __init__(self, cookie):
        self.log_str = ""
        self.notebook_id = None
        self.note_token = None
        self.note_auth = None
        self.click_num = 15  # 抽奖/摇一摇次数
        self.draw = 1  # 剩余抽奖次数阈值
        self.session = requests.Session()
        self.timestamp = str(int(round(time.time() * 1000)))
        self.cookies = {'sensors_stay_time': self.timestamp}
        
        # 解析 CK
        try:
            parts = cookie.split("#")
            self.Authorization = parts[0]
            self.account = parts[1]
            self.auth_token = parts[2]
            
            if len(parts) > 3:
                self.yun_uni = parts[3]
            else:
                self.yun_uni = None
                self.log("⚠️ 警告: CK缺少 x-yun-uni，上传分享任务将失败！")
            
            self.encrypt_account = self.account[:3] + "****" + self.account[7:]
        except:
            self.Authorization = None
            self.account = "Unknown"
            self.auth_token = ""
            self.yun_uni = None
            self.encrypt_account = "格式错误"

        self.jwtHeaders = {
            'User-Agent': ua,
            'Accept': '*/*',
            'Host': 'caiyun.feixin.10086.cn:7071',
        }
        self.app_client_info = "4|127.0.0.1|1|12.4.3|OPPO|PDRM00|DF1290E08406BF121D2685BE1C3A50EA|02-00-00-00-00-00|android 13|1080X2245|zh||||013|0|"

    def log(self, msg):
        print(msg)
        self.log_str += msg + "\n"

    def sleep(self, min_delay=1, max_delay=1.5):
        time.sleep(random.uniform(min_delay, max_delay))

    def catch_errors(func):
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                self.log(f"❌ 错误: {str(e)}")
            return None
        return wrapper

    def send_request(self, url, headers=None, cookies=None, data=None, params=None, method='GET'):
        req_headers = self.session.headers.copy()
        if headers: req_headers.update(headers)
        if cookies: self.session.cookies.update(cookies)
        
        try:
            if method == 'POST':
                if isinstance(data, dict):
                    resp = self.session.post(url, headers=req_headers, json=data, params=params, timeout=10)
                else:
                    resp = self.session.post(url, headers=req_headers, data=data, params=params, timeout=10)
            else:
                resp = self.session.get(url, headers=req_headers, params=params, timeout=10)
            return resp
        except Exception as e:
            return None

    # ================= 认证模块 =================

    def sso(self):
        url = 'https://orches.yun.139.com/orchestration/auth-rebuild/token/v1.0/querySpecToken'
        headers = {
            'Authorization': self.Authorization,
            'User-Agent': ua,
            'Content-Type': 'application/json',
            'Host': 'orches.yun.139.com'
        }
        data = {"account": self.account, "toSourceId": "001005"}
        res = self.send_request(url, headers=headers, data=data, method='POST')
        if res:
            json_data = res.json()
            if json_data.get('success'):
                return json_data['data']['token']
            else:
                self.log(f"SSO失败: {json_data.get('message')}")
        return None

    def jwt(self):
        token = self.sso()
        if not token:
            self.log("- CK可能失效 (SSO Token获取失败)")
            return False
        
        url = f"https://caiyun.feixin.10086.cn:7071/portal/auth/tyrzLogin.action?ssoToken={token}"
        res = self.send_request(url, headers=self.jwtHeaders, method='POST')
        if res:
            json_data = res.json()
            if json_data.get('code') == 0:
                self.jwtHeaders['jwtToken'] = json_data['result']['token']
                self.cookies['jwtToken'] = json_data['result']['token']
                return True
            else:
                self.log(f"JWT获取失败: {json_data.get('msg')}")
        return False

    # ================= 互助模块 (核心新增) =================
    
    def _game_sign(self, req_id, ts, nonce):
        return hashlib.md5(f"{GAME_SALT}{req_id}{ts}{nonce}{GAME_SALT}".encode('utf-8')).hexdigest()

    @catch_errors
    def run_invite(self, target_list):
        """执行互助：遍历所有账号列表，给别人助力"""
        if not target_list or len(target_list) <= 1:
            return 

        self.log("\n🤝 正在执行账号互助...")
        url = "https://caiyun.feixin.10086.cn:7071/market/signin/hecheng1T/beinvite"

        for target_phone in target_list:
            # 1. 跳过自己
            if target_phone == self.account:
                continue
            
            # 2. 准备参数
            ts = str(int(time.time() * 1000))
            req_id = str(uuid.uuid4())
            nonce = str(uuid.uuid4())
            sign = self._game_sign(req_id, ts, nonce)

            # 3. 构造专用 Header
            headers = {
                'x-request-id': req_id,
                'x-timestamp': ts,
                'x-nonce': nonce,
                'x-signature': sign,
                'token': self.auth_token,
                'x-requested-with': 'com.chinamobile.mcloud',
                'referer': f'https://caiyun.feixin.10086.cn:7071/portal/synthesisonet/index.html?inviter={target_phone}&sourceid=1120',
                'User-Agent': ua
            }
            # 合并登录态
            headers.update(self.jwtHeaders)

            try:
                params = {"inviter": target_phone}
                res = self.session.get(url, headers=headers, params=params, cookies=self.cookies, timeout=5).json()
                
                if res.get('code') == 0:
                    self.log(f"   ✅ 助力 -> {target_phone[-4:]}: 成功")
                else:
                    msg = res.get('msg', '未知错误')
                    if "上限" in msg:
                        self.log(f"   ⚠️ 助力 -> {target_phone[-4:]}: 对方已满或你已达上限")
                    elif "自己" in msg:
                        pass
                    else:
                        self.log(f"   ❌ 助力 -> {target_phone[-4:]}: {msg}")
            except Exception as e:
                self.log(f"   ❌ 助力 -> {target_phone[-4:]}: 请求异常")
            
            time.sleep(2) # 间隔防止风控

    # ================= 游戏模块 =================

    def _game_headers(self, req_id, ts, nonce):
        sign = self._game_sign(req_id, ts, nonce)
        h = {
            'x-request-id': req_id, 'x-timestamp': ts, 'x-nonce': nonce, 'x-signature': sign, 
            'token': self.auth_token, 'x-requested-with': 'com.chinamobile.mcloud',
            'referer': 'https://caiyun.feixin.10086.cn:7071/portal/synthesisonet/index.html?sourceid=1120&enableShare=1'
        }
        return h

    def _game_init(self):
        url = "https://caiyun.feixin.10086.cn:7071/market/signin/hecheng1T/beinvite"
        ts, req_id, nonce = str(int(time.time() * 1000)), str(uuid.uuid4()), str(uuid.uuid4())
        headers = self._game_headers(req_id, ts, nonce)
        try:
            self.send_request(url, headers=headers)
            return True
        except: return False

    def _game_finish(self):
        url = "https://caiyun.feixin.10086.cn:7071/market/signin/hecheng1T/finish?flag=true"
        ts, req_id, nonce = str(int(time.time() * 1000)), str(uuid.uuid4()), str(uuid.uuid4())
        headers = self._game_headers(req_id, ts, nonce)
        try:
            res = self.send_request(url, headers=headers, params={"flag": "true"})
            return res.json()
        except Exception as e:
            return None

    @catch_errors
    def run_hecheng(self):
        self.log("\n🎮 正在检测游戏任务...")
        succ_count = 0
        
        # 只要没达到设定目标，且服务器没返回次数耗尽，就一直玩
        while succ_count < GAME_TARGET_SUCC:
            self.log(f"   [第 {succ_count + 1} 局] 准备开始...")
            self._game_init()
            self.log(f"   ⏳ 游戏进行中 (等待 {GAME_DURATION} 秒)...")
            time.sleep(GAME_DURATION)
            
            res = self._game_finish()
            if res and res.get('code') == 0:
                result = res.get('result', {})
                current_succ = result.get('succ', 0)
                remaining = result.get('curr', 0) 
                
                if result.get('flag') == True or current_succ > 0:
                      self.log(f"   🎉 胜利! 累计成功: {current_succ} | 剩余机会: {remaining}")
                      succ_count += 1
                      # 如果服务器明确返回剩余次数为0，直接跳出循环
                      if remaining <= 0:
                          self.log("   ⛔️ 游戏次数已耗尽 (Server Returns 0)，停止。")
                          break
                else:
                      self.log(f"   ⚠️ 结算无效: {res}")
                      if remaining <= 0:
                          self.log("   ⛔️ 游戏次数已耗尽，停止。")
                          break
            else:
                self.log(f"   ❌ 接口错误: {res}")
                break
            time.sleep(3)

    # ================= 日常任务逻辑 =================

    @catch_errors
    def run_upload_task(self):
        if not self.yun_uni: return
        file_id, file_name = self._step_1_upload()
        if file_id and file_name:
            self.sleep()
            self._step_2_share(file_id, file_name)

    def _step_1_upload(self):
        create_url = "https://personal-kd-njs.yun.139.com/hcy/file/create"
        file_name = f"reward_auto_{int(time.time())}_{random.randint(100,999)}.txt"
        tz_cn = timezone(timedelta(hours=8))
        local_created_at = datetime.now(tz_cn).strftime('%Y-%m-%dT%H:%M:%S.') + datetime.now(tz_cn).strftime('%f')[:3] + "+08:00"
        
        headers = {
            "x-yun-url-type": "1", "x-yun-op-type": "1", "x-yun-sub-op-type": "100", "x-yun-api-version": "v1",
            "x-yun-client-info": self.app_client_info, "x-yun-app-channel": "10000023", "x-huawei-channelsrc": "10000023",
            "accept-language": "zh-CN", "x-yun-uni": self.yun_uni, "authorization": self.Authorization, 
            "content-type": "application/json; charset=UTF-8", "user-agent": "okhttp/4.12.0"
        }
        payload = {
            "contentHash": "6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b",
            "contentHashAlgorithm": "SHA256", "contentType": "application/oct-stream", "fileRenameMode": "force_rename",
            "localCreatedAt": local_created_at, "name": file_name, "parallelUpload": True, "parentFileId": "/", 
            "partInfos": [{"partNumber": 1, "partSize": 1, "start": 0, "end": 1, "parallelHashCtx": {"partOffset": 0}}],
            "size": 1, "storyVideoFile": False, "type": "file", "userRegion": {"cityCode": "376", "provinceCode": "371"}
        }
        try:
            resp = requests.post(create_url, headers=headers, json=payload, timeout=10)
            if resp.status_code == 200 and resp.json().get("success"):
                fid = resp.json().get("data", {}).get('fileId')
                self.log(f"   ✅ 上传成功 (ID: {fid})")
                return fid, file_name
        except: pass
        return None, None

    def _step_2_share(self, file_id, file_name):
        url = "https://yun.139.com/orchestration/personalCloud-rebuild/outlink/v1.0/getOutLink"
        headers = {
            "Authorization": self.Authorization, "Cookie": f"ud_id={self.yun_uni}; token={self.auth_token};",
            "Content-Type": "application/json;charset=UTF-8", "User-Agent": "okhttp/4.12.0",
            "x-yun-client-info": self.app_client_info, "x-yun-app-channel": "10000023", "x-yun-uni": self.yun_uni
        }
        payload = {
            "getOutLinkReq": {
                "subLinkType": 0, "encrypt": 1, "coIDLst": [file_id], "caIDLst": [], "pubType": 1,
                "dedicatedName": file_name, "periodUnit": 1, "period": 7, "viewerLst": [],
                "extInfo": {"isWatermark": 0, "shareChannel": "10000023"},
                "commonAccountInfo": {"account": self.account, "accountType": 1}
            }
        }
        try:
            if requests.post(url, headers=headers, json=payload, timeout=10).json().get("success"):
                self.log("   ✅ 分享成功")
        except: pass

    @catch_errors
    def signin_status(self):
        url = 'https://caiyun.feixin.10086.cn/market/signin/page/info?client=app'
        res = self.send_request(url, headers=self.jwtHeaders, cookies=self.cookies).json()
        if res['msg'] == 'success':
            if not res['result'].get('todaySignIn'):
                self.log('   ❌ 未签到，尝试补签...')
                self.send_request('https://caiyun.feixin.10086.cn/market/manager/commonMarketconfig/getByMarketRuleName?marketName=sign_in_3', headers=self.jwtHeaders, cookies=self.cookies)
            else: self.log('   ✅ 已签到')

    @catch_errors
    def click(self):
        url = "https://caiyun.feixin.10086.cn/market/signin/task/click?key=task&id=319"
        for _ in range(self.click_num):
            self.send_request(url, headers=self.jwtHeaders, cookies=self.cookies)
            time.sleep(0.1)

    @catch_errors
    def get_tasklist(self, url_name, app_type):
        url = f'https://caiyun.feixin.10086.cn/market/signin/task/taskList?marketname={url_name}'
        res = self.send_request(url, headers=self.jwtHeaders, cookies=self.cookies).json()
        task_list = res.get('result', {})
        for task_type, tasks in task_list.items():
            if task_type in ["new", "hidden", "hiddenabc"]: continue
            if app_type in ['cloud_app', 'email_app'] and task_type in ['month', 'day']:
                for task in tasks:
                    if task.get('state') != 'FINISH':
                        self.do_task(task.get('id'), task_type, app_type)

    @catch_errors
    def do_task(self, task_id, task_type, app_type):
        if app_type == 'cloud_app' and task_id in [110, 113, 417, 409, 404]: return
        if app_type == 'email_app' and task_id in [1004, 1005, 1015, 1020]: return
        
        self.send_request(f'https://caiyun.feixin.10086.cn/market/signin/task/click?key=task&id={task_id}', headers=self.jwtHeaders, cookies=self.cookies)
        if app_type == 'cloud_app' and task_id == 106: self.run_upload_task()
        elif app_type == 'cloud_app' and task_id == 107: self.create_note_flow()

    def create_note_flow(self):
        # 简化的笔记逻辑，仅为完成任务
        try:
            note_url = 'http://mnote.caiyun.feixin.10086.cn/noteServer/api/authTokenRefresh.do'
            res = self.send_request(note_url, headers={'Content-Type':'application/json'}, data={"authToken": self.auth_token, "userPhone": self.account}, method="POST")
            note_token = res.headers.get('NOTE_TOKEN')
            app_auth = res.headers.get('APP_AUTH')
            
            headers = {'APP_NUMBER': self.account, 'APP_AUTH': app_auth, 'NOTE_TOKEN': note_token, 'Content-Type': 'application/json'}
            sync_res = self.send_request('http://mnote.caiyun.feixin.10086.cn/noteServer/api/syncNotebookV3.do', headers=headers, data={"addNotebooks": [], "delNotebooks": [], "notebookRefs": [], "updateNotebooks": []}, method='POST').json()
            notebook_id = sync_res['notebooks'][0]['notebookId']
            
            note_id = ''.join(random.choice('abcdef0123456789') for _ in range(32))
            ts = str(int(time.time() * 1000))
            payload = {"contents": [{"data": "Auto", "noteId": note_id, "type": "RICHTEXT"}], "createtime": ts, "noteid": note_id, "tags": [{"id": notebook_id, "text": "默认笔记本"}], "title": "Task", "updatetime": ts, "userphone": self.account}
            self.send_request('http://mnote.caiyun.feixin.10086.cn/noteServer/api/createNote.do', headers=headers, data=payload, method="POST")
            self.log("   ✅ 笔记任务完成")
        except: pass

    @catch_errors
    def wxsign(self):
        self.send_request('https://caiyun.feixin.10086.cn/market/playoffic/followSignInfo?isWx=true', headers=self.jwtHeaders, cookies=self.cookies)

    @catch_errors
    def shake(self):
        url = "https://caiyun.feixin.10086.cn:7071/market/shake-server/shake/shakeIt?flag=1"
        for _ in range(self.click_num):
            self.send_request(url, headers=self.jwtHeaders, cookies=self.cookies, method='POST')
            time.sleep(0.2)

    @catch_errors
    def surplus_num(self):
        res = self.send_request('https://caiyun.feixin.10086.cn/market/playoffic/drawInfo', headers=self.jwtHeaders).json()
        if res.get('msg') == 'success':
            remain = res['result'].get('surplusNumber', 0)
            if remain > 50 - self.draw:
                self.log(f"🎁 剩余抽奖: {remain}次, 执行抽奖...")
                for _ in range(self.draw):
                    self.send_request("https://caiyun.feixin.10086.cn/market/playoffic/draw", headers=self.jwtHeaders)
                    time.sleep(1)

    @catch_errors
    def backup_cloud(self):
        try:
            if self.send_request('https://caiyun.feixin.10086.cn/market/backupgift/info', headers=self.jwtHeaders).json().get('result', {}).get('state') == 0:
                self.send_request('https://caiyun.feixin.10086.cn/market/backupgift/receive', headers=self.jwtHeaders)
                self.log("   ✅ 领取备份奖励")
        except: pass

    @catch_errors
    def open_send(self):
        try:
            res = self.send_request('https://caiyun.feixin.10086.cn/market/msgPushOn/task/status', headers=self.jwtHeaders).json().get('result', {})
            if res.get('pushOn') == 1:
                url = 'https://caiyun.feixin.10086.cn/market/msgPushOn/task/obtain'
                if res.get('firstTaskStatus') != 3: self.send_request(url, headers=self.jwtHeaders, data={"type": 1}, method="POST")
                if res.get('secondTaskStatus') == 2: self.send_request(url, headers=self.jwtHeaders, data={"type": 2}, method="POST")
        except: pass

    @catch_errors
    def receive(self):
        self.send_request("https://caiyun.feixin.10086.cn/market/signin/page/receive", headers=self.jwtHeaders, cookies=self.cookies)
        res = self.send_request(f"https://caiyun.feixin.10086.cn/market/prizeApi/checkPrize/getUserPrizeLogPage?currPage=1&pageSize=15&_={self.timestamp}", headers=self.jwtHeaders, cookies=self.cookies).json()
        try:
            pending = [item.get('prizeName') for item in res.get('result', {}).get('result', []) if item.get('flag') == 1]
            if pending: self.log(f"🎁 待领奖品: {pending}")
        except: pass

    # ================= 主运行流程 =================

    def run(self, target_list=None, view_only=False):
        if not self.Authorization: 
            return f"❌ 账号 {self.encrypt_account} 配置错误\n"
        
        self.log(f"========== 用户 [{self.encrypt_account}] ==========")
        
        # --- 核心修改：登录校验熔断 ---
        # 如果登录失败，直接 return，不执行后续任何代码
        if not self.jwt():
            self.log("⛔️ 登录失败，跳过该账号所有后续任务")
            return self.log_str
        # ---------------------------
        
        if view_only:
            self.log("查看模式已省略，请使用正常模式运行")
            return self.log_str
        
        # 1. 执行日常任务
        self.log("👉 开始日常任务...")
        self.signin_status()
        self.click()
        self.wxsign()
        self.get_tasklist(url_name='sign_in_3', app_type='cloud_app')
        self.shake()
        self.surplus_num()
        self.backup_cloud()
        self.open_send()
        self.get_tasklist(url_name='newsign_139mail', app_type='email_app')
        self.receive()
        
        # 2. 执行互助 (日常完成后，增加游戏次数)
        if target_list:
            self.run_invite(target_list)

        # 3. 执行游戏 (此时次数已满，开始消耗)
        self.run_hecheng()
        
        return self.log_str

def run_ydyp(view_only=False):
    mode_text = "任务状态查看" if view_only else "任务执行"
    full_log = f"【移动云盘 - {mode_text}】\n"
    
    if not ydypCK:
        return full_log + "⛔️ 未配置 YDYP_CK (请设置为 Basic...#手机#Token#YunID 格式)\n"

    cookies = re.split(r'[&\n]', ydypCK)
    valid_cookies = [c for c in cookies if c.strip()]
    
    # --- 提取所有账号手机号用于互助 ---
    all_phones = []
    for c in valid_cookies:
        try:
            parts = c.split('#')
            if len(parts) >= 2: all_phones.append(parts[1])
        except: pass
    
    # --- 遍历执行 ---
    for i, account in enumerate(valid_cookies, 1):
        if not account.strip(): continue
        yp = YP(account)
        # 将手机号名单传入
        full_log += yp.run(target_list=all_phones, view_only=view_only) + "\n"
        time.sleep(3)
        
    return full_log

if __name__ == "__main__":
    print(run_ydyp())
