import os
import random
import re
import time
import requests

# ================= 配置区域 =================
ydypCK = os.getenv("YDYP_CK") 
# ===========================================

ua = 'Mozilla/5.0 (Linux; Android 11; M2012K10C Build/RP1A.200720.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/90.0.4430.210 Mobile Safari/537.36 MCloudApp/10.0.1'

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
        
        try:
            parts = cookie.split("#")
            self.Authorization = parts[0]
            self.account = parts[1]
            self.auth_token = parts[2]
            self.encrypt_account = self.account[:3] + "****" + self.account[7:]
        except:
            self.Authorization = None
            self.account = "Unknown"
            self.auth_token = ""
            self.encrypt_account = "格式错误"

        self.jwtHeaders = {
            'User-Agent': ua,
            'Accept': '*/*',
            'Host': 'caiyun.feixin.10086.cn:7071',
        }

    # 日志记录辅助函数
    def log(self, msg):
        print(msg)
        self.log_str += msg + "\n"

    def sleep(self, min_delay=1, max_delay=1.5):
        time.sleep(random.uniform(min_delay, max_delay))

    # 装饰器：捕获异常
    def catch_errors(func):
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                self.log(f"❌ 错误: {str(e)}")
            return None
        return wrapper

    def send_request(self, url, headers=None, cookies=None, data=None, params=None, method='GET'):
        self.session.headers.update(headers or {})
        if cookies:
            self.session.cookies.update(cookies)
        
        try:
            if method == 'POST':
                if isinstance(data, dict):
                    resp = self.session.post(url, json=data, params=params)
                else:
                    resp = self.session.post(url, data=data, params=params)
            else:
                resp = self.session.get(url, params=params)
            resp.raise_for_status()
            return resp
        except Exception as e:
            # self.log(f"请求异常: {e}") # 过于啰嗦，关掉
            return None

    # ================= 核心逻辑 =================

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

    @catch_errors
    def signin_status(self):
        self.sleep()
        url = 'https://caiyun.feixin.10086.cn/market/signin/page/info?client=app'
        res = self.send_request(url, headers=self.jwtHeaders, cookies=self.cookies).json()
        if res['msg'] == 'success':
            if res['result'].get('todaySignIn'):
                self.log('✅ 已签到')
            else:
                self.log('❌ 未签到，尝试补签...')
                sign_url = 'https://caiyun.feixin.10086.cn/market/manager/commonMarketconfig/getByMarketRuleName?marketName=sign_in_3'
                sign_res = self.send_request(sign_url, headers=self.jwtHeaders, cookies=self.cookies).json()
                if sign_res['msg'] == 'success':
                    self.log('✅ 签到成功')
                else:
                    self.log(f"签到失败: {sign_res['msg']}")
        else:
            self.log(f"查询签到状态失败: {res['msg']}")

    @catch_errors
    def click(self):
        # 戳一下
        url = "https://caiyun.feixin.10086.cn/market/signin/task/click?key=task&id=319"
        success_count = 0
        for _ in range(self.click_num):
            res = self.send_request(url, headers=self.jwtHeaders, cookies=self.cookies).json()
            time.sleep(0.2)
            if 'result' in res:
                success_count += 1
        
        if success_count > 0:
            self.log(f"👉 戳一下成功: {success_count}次")

    @catch_errors
    def get_tasklist(self, url_name, app_type):
        url = f'https://caiyun.feixin.10086.cn/market/signin/task/taskList?marketname={url_name}'
        res = self.send_request(url, headers=self.jwtHeaders, cookies=self.cookies).json()
        self.sleep()
        task_list = res.get('result', {})

        for task_type, tasks in task_list.items():
            if task_type in ["new", "hidden", "hiddenabc"]: continue
            
            # 这里简化逻辑，只处理 cloud_app 和 email_app 的 month/day 任务
            if app_type in ['cloud_app', 'email_app'] and task_type in ['month', 'day']:
                prefix = "云盘" if app_type == 'cloud_app' else "邮箱"
                period = "月" if task_type == 'month' else "日"
                
                # self.log(f'\n📆 {prefix}{period}任务检查')
                for task in tasks:
                    task_id = task.get('id')
                    task_name = task.get('name', '')
                    task_state = task.get('state', '')
                    
                    # 过滤不需要做的任务ID (原脚本逻辑)
                    if app_type == 'cloud_app' and task_id in [110, 113, 417, 409, 404]: continue
                    if app_type == 'email_app' and task_id in [1004, 1005, 1015, 1020]: continue

                    if task_state != 'FINISH':
                        self.log(f'- 去完成: {task_name}')
                        self.do_task(task_id, task_type, app_type)
                        time.sleep(1)

    @catch_errors
    def do_task(self, task_id, task_type, app_type):
        task_url = f'https://caiyun.feixin.10086.cn/market/signin/task/click?key=task&id={task_id}'
        self.send_request(task_url, headers=self.jwtHeaders, cookies=self.cookies)
        
        if app_type == 'cloud_app' and task_type == 'day':
            if task_id == 106: # 上传文件
                self.log('- 执行上传任务...')
                self.upload_file()
            elif task_id == 107: # 创建笔记
                self.log('- 执行笔记任务...')
                self.refresh_notetoken()
                self.create_note_flow()

    @catch_errors
    def upload_file(self):
        url = 'http://ose.caiyun.feixin.10086.cn/richlifeApp/devapp/IUploadAndDownload'
        headers = {
            'APP_NUMBER': self.account,
            'Authorization': self.Authorization,
            'Host': 'ose.caiyun.feixin.10086.cn',
            'Content-Type': 'application/xml; charset=UTF-8'
        }
        payload = f'''<pcUploadFileRequest><ownerMSISDN>{self.account}</ownerMSISDN><fileCount>1</fileCount><totalSize>1</totalSize><uploadContentList length="1"><uploadContentInfo><comlexFlag>0</comlexFlag><contentDesc><![CDATA[]]></contentDesc><contentName><![CDATA[autotask.txt]]></contentName><contentSize>1</contentSize><contentTAGList></contentTAGList><digest>C4CA4238A0B923820DCC509A6F75849B</digest><exif/><fileEtag>0</fileEtag><fileVersion>0</fileVersion><updateContentID></updateContentID></uploadContentInfo></uploadContentList><newCatalogName></newCatalogName><parentCatalogID></parentCatalogID><operation>0</operation><path></path><manualRename>2</manualRename><autoCreatePath length="0"/><tagID></tagID><tagType></tagType></pcUploadFileRequest>'''
        
        try:
            requests.post(url, headers=headers, data=payload, timeout=5)
            self.log('  └ 上传成功')
        except:
            self.log('  └ 上传失败')

    def refresh_notetoken(self):
        note_url = 'http://mnote.caiyun.feixin.10086.cn/noteServer/api/authTokenRefresh.do'
        payload = {"authToken": self.auth_token, "userPhone": self.account}
        headers = {'Content-Type': 'application/json; charset=UTF-8', 'Host': 'mnote.caiyun.feixin.10086.cn'}
        try:
            res = self.send_request(note_url, headers=headers, data=payload, method="POST")
            self.note_token = res.headers.get('NOTE_TOKEN')
            self.note_auth = res.headers.get('APP_AUTH')
        except:
            pass

    def create_note_flow(self):
        # 1. Sync to get notebook ID
        sync_url = 'http://mnote.caiyun.feixin.10086.cn/noteServer/api/syncNotebookV3.do'
        headers = {
            'APP_NUMBER': self.account, 'APP_AUTH': self.note_auth, 'NOTE_TOKEN': self.note_token,
            'Host': 'mnote.caiyun.feixin.10086.cn', 'Content-Type': 'application/json; charset=UTF-8'
        }
        payload = {"addNotebooks": [], "delNotebooks": [], "notebookRefs": [], "updateNotebooks": []}
        try:
            res = self.send_request(sync_url, headers=headers, data=payload, method='POST').json()
            self.notebook_id = res['notebooks'][0]['notebookId']
            
            # 2. Create Note
            create_url = 'http://mnote.caiyun.feixin.10086.cn/noteServer/api/createNote.do'
            note_id = ''.join(random.choice('abcdef0123456789') for _ in range(32))
            ts = str(int(time.time() * 1000))
            note_payload = {
                "archived": 0, "attachmentdir": note_id, "attachments": [], 
                "contents": [{"data": "<font size=\"3\">AutoTask</font>", "noteId": note_id, "type": "RICHTEXT"}],
                "createtime": ts, "noteid": note_id, "tags": [{"id": self.notebook_id, "text": "默认笔记本"}],
                "title": "AutoTask", "updatetime": ts, "userphone": self.account
            }
            res_create = self.send_request(create_url, headers=headers, data=note_payload, method="POST")
            if res_create.status_code == 200:
                self.log('  └ 笔记创建成功')
        except:
            self.log('  └ 笔记创建失败')

    @catch_errors
    def wxsign(self):
        url = 'https://caiyun.feixin.10086.cn/market/playoffic/followSignInfo?isWx=true'
        res = self.send_request(url, headers=self.jwtHeaders, cookies=self.cookies).json()
        if res['msg'] == 'success' and res['result'].get('todaySignIn'):
            self.log('✅ 公众号已签到')
        else:
            self.log('ℹ️ 公众号未签到或未绑定')

    @catch_errors
    def shake(self):
        url = "https://caiyun.feixin.10086.cn:7071/market/shake-server/shake/shakeIt?flag=1"
        count = 0
        for _ in range(self.click_num):
            res = self.send_request(url, headers=self.jwtHeaders, cookies=self.cookies, method='POST').json()
            time.sleep(0.5)
            if res["result"].get("shakePrizeconfig"):
                count += 1
        if count > 0: self.log(f"👋 摇一摇中奖: {count}次")

    @catch_errors
    def surplus_num(self):
        # 抽奖逻辑
        info_url = 'https://caiyun.feixin.10086.cn/market/playoffic/drawInfo'
        draw_url = "https://caiyun.feixin.10086.cn/market/playoffic/draw"
        res = self.send_request(info_url, headers=self.jwtHeaders).json()
        if res.get('msg') == 'success':
            remain = res['result'].get('surplusNumber', 0)
            if remain > 50 - self.draw: # 这里的逻辑保留原作者意思
                self.log(f"🎁 剩余抽奖: {remain}次, 开始抽奖...")
                for _ in range(self.draw):
                    d_res = self.send_request(draw_url, headers=self.jwtHeaders).json()
                    if d_res.get("code") == 0:
                        self.log(f"  └ 获得: {d_res['result'].get('prizeName')}")
                    self.sleep()

    @catch_errors
    def backup_cloud(self):
        # 备份奖励
        url = 'https://caiyun.feixin.10086.cn/market/backupgift/info'
        res = self.send_request(url, headers=self.jwtHeaders).json()
        state = res.get('result', {}).get('state', -1)
        
        if state == 0:
            rec_url = 'https://caiyun.feixin.10086.cn/market/backupgift/receive'
            r = self.send_request(rec_url, headers=self.jwtHeaders).json()
            self.log(f"📥 领取备份奖励: {r.get('result', {}).get('result')}云朵")
        
        # 膨胀云朵
        exp_url = 'https://caiyun.feixin.10086.cn/market/signin/page/taskExpansion'
        exp_res = self.send_request(exp_url, headers=self.jwtHeaders, cookies=self.cookies).json()
        result = exp_res.get('result', {})
        if result.get('preMonthBackup') and not result.get('curMonthBackupTaskAccept'):
            date = result.get('acceptDate')
            rec_exp_url = f'https://caiyun.feixin.10086.cn/market/signin/page/receiveTaskExpansion?acceptDate={date}'
            r2 = self.send_request(rec_exp_url, headers=self.jwtHeaders, cookies=self.cookies).json()
            if r2.get("code") == 0:
                self.log(f"🎈 领取膨胀云朵: {r2['result'].get('cloudCount')}朵")

    @catch_errors
    def open_send(self):
        # 通知开启奖励
        url = 'https://caiyun.feixin.10086.cn/market/msgPushOn/task/status'
        res = self.send_request(url, headers=self.jwtHeaders).json()
        result = res.get('result', {})
        if result.get('pushOn') == 1:
            reward_url = 'https://caiyun.feixin.10086.cn/market/msgPushOn/task/obtain'
            if result.get('firstTaskStatus') != 3:
                self.send_request(reward_url, headers=self.jwtHeaders, data={"type": 1}, method="POST")
                self.log("🔔 领取通知奖励1")
            if result.get('secondTaskStatus') == 2:
                self.send_request(reward_url, headers=self.jwtHeaders, data={"type": 2}, method="POST")
                self.log("🔔 领取通知奖励2")

    @catch_errors
    def receive(self):
        # 领取云朵
        rec_url = "https://caiyun.feixin.10086.cn/market/signin/page/receive"
        res = self.send_request(rec_url, headers=self.jwtHeaders, cookies=self.cookies).json()
        
        # 查询总数
        prize_url = f"https://caiyun.feixin.10086.cn/market/prizeApi/checkPrize/getUserPrizeLogPage?currPage=1&pageSize=15&_={self.timestamp}"
        p_res = self.send_request(prize_url, headers=self.jwtHeaders, cookies=self.cookies).json()
        
        recv = res["result"].get("receive", 0)
        total = res["result"].get("total", 0)
        
        # 检查未领取的奖品
        pending = ""
        try:
            for item in p_res.get('result', {}).get('result', []):
                if item.get('flag') == 1:
                    pending += f" [{item.get('prizeName')}]"
        except: pass

        self.log(f"\n☁️ 待领: {recv} | 总云朵: {total}")
        if pending: self.log(f"🎁 未领奖品: {pending}")

    # ================= 流程入口 =================

    def run(self):
        if not self.Authorization: return f"❌ 账号 {self.encrypt_account} 配置错误\n"
        
        self.log(f"========== 用户 [{self.encrypt_account}] ==========")
        
        if self.jwt():
            # 1. 签到
            self.signin_status()
            # 2. 戳一戳
            self.click()
            # 3. 公众号签到
            self.wxsign()
            # 4. 做云盘任务
            self.get_tasklist(url_name='sign_in_3', app_type='cloud_app')
            # 5. 摇一摇
            self.shake()
            # 6. 抽奖
            self.surplus_num()
            # 7. 备份/通知奖励
            self.backup_cloud()
            self.open_send()
            # 8. 做邮箱任务
            self.get_tasklist(url_name='newsign_139mail', app_type='email_app')
            # 9. 统一领取云朵
            self.receive()
        else:
            self.log("❌ 登录失败 (SSO/JWT错误)")
            
        return self.log_str

# 模块导出函数
def run_ydyp():
    full_log = "【移动云盘任务】\n"
    if not ydypCK:
        return full_log + "⛔️ 未配置 YDYP_CK\n"

    cookies = re.split(r'[&\n]', ydypCK)
    for i, account in enumerate(cookies, 1):
        if not account.strip(): continue
        yp = YP(account)
        full_log += yp.run() + "\n"
        time.sleep(3)
        
    return full_log
