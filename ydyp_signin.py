import os
import random
import re
import time
import requests
import json
import hashlib
import uuid
from datetime import datetime, timezone, timedelta

# ================= 配置区域 =================
ydypCK = """
Basic cGM6MTY2ODQwNzAzMjU6T2tNbmcyNVp8MXxSQ1N8MTc3MDQ2NjkyODk2NnxMUE1mejlNaU5ZbmpxRjlMcXR6MV8wT0ZyZ2xUTXU5ZTV6UF93NV9fYzVzTUZtMzN0RTZQbHZFVVAzOEVCbGtrRWxZUlNKVl84MmhBalBqYkE1dFZ1Ukoxc3BFMWpZZHlzWjNiRG9kTS5CZkp1dEdEOVFzbkh4NE1wZFJhRlU3N1RQWDlyazZRclJVZklmYThWZUpxU0dQcVpkVngxZFBiNVZyZU1lWEJxMzgt#16684070325#eQXxQR02m9owzXA8pSCPZm7BV8yxVkOOT1ZJ9kZj+fJLjUxJOQ8K4pud0CwKDdSxCTi6HBnt8pxf5XeDO/tXsZ9zdxdJ6rqDk7JwYjn/237Ym7awhU1sOREcgIxZtN7DyAPtiTIVKFg6nkYUIIKrDWAqfPyz0NVvpcrGTrCY1SH5HSUPv/29GZGEXDqn8Jx+wn6rjqqSJ5AaEbw7unZ9kESO2UAR9WjEV6yt4kINyOVuOUu4s7DBWrWhLG29o5WQnNsAg/2qk67tvJMfQqcp8g==#1258564792203660005
Basic cGM6MTkwNTAyMTQ2NjA6NGtvemE4aEh8MXxSQ1N8MTc3MDQ2OTUyODcxOHxPXzYuZzFIYmNjakN5Q284MTc1Zmo1eXZJTFh5MjhneDQxWU1vOTQ3ZW4wMmlXU3huTTNBb2czaDRZbHVweWxlLjAzS295cTBTenU0cURrRFY0Q0wxUXZnQ1NCWHp5NGRzZEpwZ3FGNlpWV082N0FzeXhZNVJ6VjY2MGZxcGhJU0RQUE85eWwzNUIzeXB4YWVVRzZiYXBvOGV4OTAwcjRUbWlENWV2ZHVxRnct#19050214660#dwpm3o9X1pXy/jxhT+2Y5uud3b5HCai0dWm39U+X+SOmtVE9CjBxfdar2OBLtAkHJp3fxx+4IOJvT3YAXR0fGUIKtyi1W1z9DbdSb/Ank60fnoN9ePiLJEzu2pZ3BXxFz4E8LyeBV9ssqJCwTcIMTOp+F9DHCazMDruoBtLP22+iB18P+m/xzRJFXrwK7JjqgDq1GRzuOlQbSsFnNQITUHtXpXbz6KCcMT3K7uHGjcerG4LsQN1tVyxWS0EBtf4TBZBtLUB9MJbp6KaWmp6eDQ==#1258565601806899573
Basic cGM6MTg4NTE3NjExNzM6NEFLa09CaGF8MXxSQ1N8MTc3MDI2NDI4MDMzMnxCM2twQXJpV2pPZ1BRa1lpVGx6am1sODJ5SkVZdzA4QjQwamhFaTRxc0NETmFwZ2lnR3N5d1ZUNURDOUV3SllCZGU1YllzeG05SnRFNlB1Wk51UVR2dng0OWl2Mm1fTnhyTE1JamV3TEl4c0R6Y1hlZGtpYUZGMGRhQmJCUGFDRndGQ0Y4Z2gzNUJyTngyMEVDWkdtM3VrSjZZbG5Sblo1UDVDaTA2WnpBTlkt#18851761173#Fg0Q0F5SmNeFcSKvCw2dzjtLsTgnSY7rxAppBNOx4fepJyTKUFXC/GRGPS0alrMIGCpCp0EpwNqSxhlUF4PCk4o3WPvUbv7BEU4jTv54Q/n1UpikOA5TGHJdzSAufoyIvYVJr0rPnkMCb3x4gMCvcQwq/6pZNgeKebprL9beWt1vNC+gS9GjQstnnYc9c2O4usEjTMXSmoTtmRA44AQ9NoYjsVRDhL2+tQnPDNHnj44ADBzzkV6R2yPlMx3OE8XhLgMpADuE/o5Ywh4gFdgVuw==#1039842059450400648

"""

GAME_ENABLED = True
TARGET_SUCC = 5
PLAY_DURATION = 300
INVITE_ENABLED = True

GAME_SALT = "seedMdYYLIZfbCxg"
ua = 'Mozilla/5.0 (Linux; Android 13; PDRM00 Build/TP1A.220905.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/108.0.5359.128 Mobile Safari/537.36 MCloudApp/12.4.3'

# ================= 固定设备配置 =================
FIXED_DEVICE_ID = "A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6"
FIXED_MAC = "A1-B2-C3-D4-E5-F6"
FIXED_BRAND = "OPPO"
FIXED_MODEL = "PDRM00"
FIXED_ANDROID_VER = "13"

class YP:
    def __init__(self, cookie):
        self.log_str = ""
        self.notebook_id = None
        self.note_token = None
        self.note_auth = None
        self.click_num = 15
        self.draw = 1
        self.session = requests.Session()
        self.timestamp = str(int(round(time.time() * 1000)))
        self.cookies = {'sensors_stay_time': self.timestamp}
        
        try:
            parts = cookie.split("#")
            self.Authorization = parts[0]
            self.account = parts[1]
            self.auth_token = parts[2]
            self.yun_uni = parts[3] if len(parts) > 3 else None
            self.encrypt_account = self.account[:3] + "****" + self.account[7:]
            self.valid = True
        except:
            self.Authorization = None
            self.account = "Unknown"
            self.auth_token = ""
            self.yun_uni = None
            self.encrypt_account = "格式错误"
            self.valid = False
        
        # 使用固定UA和设备信息(回退到1月9日配置)
        self.dynamic_ua = ua
        self.app_client_info = f"4|127.0.0.1|1|12.4.3|{FIXED_BRAND}|{FIXED_MODEL}|{FIXED_DEVICE_ID}|{FIXED_MAC}|android {FIXED_ANDROID_VER}|1080X2245|zh||||013|0|"
        
        self.jwtHeaders = {
            'User-Agent': ua,
            'Accept': '*/*',
            'Host': 'caiyun.feixin.10086.cn:7071',
        }

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
        if headers:
            req_headers.update(headers)
        if cookies:
            self.session.cookies.update(cookies)
        try:
            if method == 'POST':
                if isinstance(data, dict):
                    resp = self.session.post(url, headers=req_headers, json=data, params=params, timeout=15)
                else:
                    resp = self.session.post(url, headers=req_headers, data=data, params=params, timeout=15)
            else:
                resp = self.session.get(url, headers=req_headers, params=params, timeout=15)
            return resp
        except:
            return None

    def sso(self):
        url = 'https://orches.yun.139.com/orchestration/auth-rebuild/token/v1.0/querySpecToken'
        headers = {'Authorization': self.Authorization, 'User-Agent': ua, 'Content-Type': 'application/json', 'Host': 'orches.yun.139.com'}
        data = {"account": self.account, "toSourceId": "001005"}
        res = self.send_request(url, headers=headers, data=data, method='POST')
        if res:
            try:
                json_data = res.json()
                if json_data.get('success'):
                    return json_data['data']['token']
            except:
                pass
        return None

    def jwt(self):
        token = self.sso()
        if not token:
            return False
        url = f"https://caiyun.feixin.10086.cn:7071/portal/auth/tyrzLogin.action?ssoToken={token}"
        res = self.send_request(url, headers=self.jwtHeaders, method='POST')
        if res:
            try:
                json_data = res.json()
                if json_data.get('code') == 0:
                    self.jwtHeaders['jwtToken'] = json_data['result']['token']
                    self.cookies['jwtToken'] = json_data['result']['token']
                    return True
            except:
                pass
        return False

    def _game_sign(self, req_id, ts, nonce):
        raw = f"{GAME_SALT}{req_id}{ts}{nonce}{GAME_SALT}"
        return hashlib.md5(raw.encode('utf-8')).hexdigest()

    def _get_game_headers(self, req_id, ts, nonce):
        sign = self._game_sign(req_id, ts, nonce)
        return {
            'User-Agent': ua,
            'Accept': 'application/json, text/plain, */*',
            'x-requested-with': 'com.chinamobile.mcloud',
            'Host': 'caiyun.feixin.10086.cn:7071',
            'referer': 'https://caiyun.feixin.10086.cn:7071/portal/synthesisonet/index.html?sourceid=1120&enableShare=1',
            'x-request-id': req_id,
            'x-timestamp': ts,
            'x-nonce': nonce,
            'x-signature': sign,
            'token': self.auth_token,
            'jwtToken': self.jwtHeaders.get('jwtToken')
        }

    def _encode_inviter(self, phone):
        """Base64 编码手机号（根据抓包，inviter参数是Base64编码的）"""
        import base64
        return base64.b64encode(phone.encode()).decode()

    @catch_errors
    def game_init(self):
        url = "https://caiyun.feixin.10086.cn:7071/market/signin/hecheng1T/beinvite"
        ts, req_id, nonce = str(int(time.time() * 1000)), str(uuid.uuid4()), str(uuid.uuid4())
        headers = self._get_game_headers(req_id, ts, nonce)
        try:
            self.session.get(url, headers=headers, cookies=self.cookies, timeout=10)
            return True
        except:
            return False

    @catch_errors
    def game_finish(self):
        url = "https://caiyun.feixin.10086.cn:7071/market/signin/hecheng1T/finish"
        ts, req_id, nonce = str(int(time.time() * 1000)), str(uuid.uuid4()), str(uuid.uuid4())
        headers = self._get_game_headers(req_id, ts, nonce)
        try:
            res = self.session.get(url, headers=headers, params={"flag": "true"}, cookies=self.cookies, timeout=10)
            return res.json()
        except Exception as e:
            self.log(f"❌ 结算请求异常: {e}")
            return None

    @catch_errors
    def run_game(self):
        self.log("\n🎮 ===== 合成游戏 =====")
        target_succ = TARGET_SUCC
        succ_count = 0
        
        while succ_count < target_succ:
            self.log(f"🎲 第 {succ_count + 1} / {target_succ} 局准备开始...")
            if not self.game_init():
                self.log("❌ 游戏初始化请求失败")
                break
            self.log(f"⏳ 游戏中... (等待 {PLAY_DURATION} 秒)")
            time.sleep(PLAY_DURATION)
            res = self.game_finish()
            
            if res and res.get('code') == 0:
                result = res.get('result', {})
                current_succ = result.get('succ', 0)
                remaining = result.get('curr', 0)
                if result.get('flag') == True or current_succ > 0:
                    self.log(f"🎉 胜利! 本月累计: {current_succ} 次 | 剩余机会: {remaining}")
                    succ_count += 1
                else:
                    self.log(f"⚠️ 结算无效: {res}")
                if remaining <= 0:
                    self.log("⛔️ 游戏次数已耗尽，停止运行。")
                    break
            else:
                self.log(f"❌ 结算接口错误: {res}")
                break
            time.sleep(2)
        self.log(f"📊 游戏结束，本次共完成 {succ_count} 次。")
        
    @catch_errors
    def do_invite(self, target_phone):
        """执行助力邀请（参数顺序修正版）"""
        self.log(f" 🔄 准备助力 {target_phone[:3]}****{target_phone[7:]}...")
        
        # 定义两种 Salt
        WEB_SALT = "sekaMdYYLIZfbCfm"  # 步骤1 和 步骤2
        APP_SALT = "seedMdYYLIZfbCxg"  # 步骤3
        
        browser_ua = "Mozilla/5.0 (Linux; Android 13; PDRM00 Build/TP1A.220905.001) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/108.0.5359.128 Mobile Safari/537.36"

        # ==================== 步骤1：获取 ssoToken ====================
        query_url = "https://caiyun.feixin.10086.cn:7071/ycloud/api/cloud/userdomain/v2/querySpecToken"
        ts, req_id, nonce = str(int(time.time() * 1000)), str(uuid.uuid4()), str(uuid.uuid4())
        
        # 签名公式: WEB_SALT + Req + Ts + Nonce + WEB_SALT
        raw_sign_str = f"{WEB_SALT}{req_id}{ts}{nonce}{WEB_SALT}"
        signature = hashlib.md5(raw_sign_str.encode('utf-8')).hexdigest()
        
        query_headers = {
            'Host': 'caiyun.feixin.10086.cn:7071',
            'User-Agent': browser_ua,
            'x-timestamp': ts,
            'x-nonce': nonce,
            'x-request-id': req_id,
            'x-signature': signature,
            'token': self.auth_token,
            'jwtToken': self.jwtHeaders.get('jwtToken'),
            'referer': f'https://caiyun.feixin.10086.cn:7071/portal/synthesisonet/index.html?inviter={self._encode_inviter(target_phone)}&sourceid=1120',
            'x-requested-with': 'mark.via'
        }
        
        try:
            resp1 = self.session.get(
                query_url, 
                headers=query_headers, 
                params={"targetSourceId": "001005"},
                timeout=10
            )
            json_res = resp1.json()
            sso_token = json_res.get('result')
            if not sso_token:
                self.log(f" ❌ ssoToken 为空: {json_res}")
                return False
            self.log(f" ✓ 已获取 ssoToken")
        except Exception as e:
            self.log(f" ❌ 获取 ssoToken 异常: {e}")
            return False
        
        # ==================== 步骤2：刷新 jwtToken ====================
        login_url = "https://caiyun.feixin.10086.cn:7071/portal/auth/v2/tyrzLogin.action"
        ts2, req_id2, nonce2 = str(int(time.time() * 1000)), str(uuid.uuid4()), str(uuid.uuid4())
        
        # 【关键修正点】构造签名用的参数字符串
        # JS 逻辑: n = {ssoToken: e, openAccount: 0}
        # 这里的 stringify 应该是按顺序拼接，而不是按字母排序
        # 正确顺序: ssoToken在前，openAccount在后
        param_str = f"ssoToken={sso_token}&openAccount=0"
        
        # 签名公式: WEB_SALT + Req + Ts + Nonce + 参数字符串 + WEB_SALT
        raw_sign_str2 = f"{WEB_SALT}{req_id2}{ts2}{nonce2}{param_str}{WEB_SALT}"
        signature2 = hashlib.md5(raw_sign_str2.encode('utf-8')).hexdigest()
        
        login_headers = {
            'Host': 'caiyun.feixin.10086.cn:7071',
            'User-Agent': browser_ua,
            'x-timestamp': ts2,
            'x-nonce': nonce2,
            'x-request-id': req_id2,
            'x-signature': signature2, 
            'token': self.auth_token,
            'jwtToken': self.jwtHeaders.get('jwtToken'),
            'referer': f'https://caiyun.feixin.10086.cn:7071/portal/synthesisonet/index.html?inviter={self._encode_inviter(target_phone)}&sourceid=1120',
            'x-requested-with': 'mark.via'
        }
        
        try:
            # 注意：发送请求时，params 字典的顺序不重要，requests 库会处理
            # 重要的是上面的 param_str 必须和 JS 生成的一模一样
            resp2 = self.session.get(
                login_url,
                headers=login_headers,
                params={"ssoToken": sso_token, "openAccount": "0"},
                timeout=10
            )
            
            # 调试打印
            # print(f"DEBUG Step2 ParamStr: {param_str}")
            # print(f"DEBUG Step2 Resp: {resp2.text}")
            
            new_jwt = resp2.json().get('result', {}).get('token')
            if not new_jwt:
                self.log(f" ❌ 新 jwtToken 为空: {resp2.text}")
                return False
            self.log(f" ✓ 已刷新 jwtToken")
        except Exception as e:
            self.log(f" ❌ 刷新 jwtToken 异常: {e}")
            return False
        
        # ==================== 步骤3：执行助力 ====================
        time.sleep(1) 
        url = "https://caiyun.feixin.10086.cn:7071/market/signin/hecheng1T/beinvite"
        ts3, req_id3, nonce3 = str(int(time.time() * 1000)), str(uuid.uuid4()), str(uuid.uuid4())
        
        # 签名公式: APP_SALT + Req + Ts + Nonce + APP_SALT (回归最简模式，确认无手机号)
        raw_sign_str3 = f"{APP_SALT}{req_id3}{ts3}{nonce3}{APP_SALT}"
        signature3 = hashlib.md5(raw_sign_str3.encode('utf-8')).hexdigest()
        
        invite_headers = {
            'Host': 'caiyun.feixin.10086.cn:7071',
            'User-Agent': browser_ua,
            'x-timestamp': ts3,
            'x-nonce': nonce3,
            'x-request-id': req_id3,
            'x-signature': signature3,
            'token': self.auth_token,
            'jwtToken': new_jwt, 
            'referer': f'https://caiyun.feixin.10086.cn:7071/portal/synthesisonet/index.html?inviter={self._encode_inviter(target_phone)}&sourceid=1120',
            'accept': '*/*',
            'x-requested-with': 'mark.via'
        }
        
        try:
            resp3 = self.session.get(url, headers=invite_headers, params={"inviter": target_phone}, timeout=10)
            data = resp3.json()
            if data.get('code') == 0:
                self.log(f" ✅ 助力成功 -> {target_phone[:3]}****{target_phone[7:]}")
                return True
            else:
                self.log(f" ⚠️ 助力失败: {data.get('msg')}") 
                return False
        except Exception as e:
            self.log(f" ❌ 助力异常: {e}")
            return False

    @catch_errors
    def run_upload_task(self):
        if not self.yun_uni:
            self.log("❌ 缺少 YUN_UNI 配置，跳过上传任务")
            return
        file_id, file_name = self._step_1_upload()
        if file_id and file_name:
            self.sleep()
            self._step_2_share(file_id, file_name)

    def _step_1_upload(self):
        create_url = "https://personal-kd-njs.yun.139.com/hcy/file/create"
        KNOWN_HASH = "6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b"
        KNOWN_SIZE = 1
        file_name = f"reward_auto_{int(time.time())}_{random.randint(100,999)}.txt"
        tz_cn = timezone(timedelta(hours=8))
        now = datetime.now(tz_cn)
        local_created_at = now.strftime('%Y-%m-%dT%H:%M:%S.') + now.strftime('%f')[:3] + "+08:00"
        headers = {
            "host": "personal-kd-njs.yun.139.com", "x-yun-url-type": "1", "x-yun-op-type": "1",
            "x-yun-sub-op-type": "100", "x-yun-api-version": "v1", "x-yun-client-info": self.app_client_info,
            "x-yun-app-channel": "10000023", "x-huawei-channelsrc": "10000023", "accept-language": "zh-CN",
            "x-yun-uni": self.yun_uni, "authorization": self.Authorization,
            "content-type": "application/json; charset=UTF-8", "user-agent": "okhttp/4.12.0"
        }
        payload = {
            "contentHash": KNOWN_HASH, "contentHashAlgorithm": "SHA256", "contentType": "application/oct-stream",
            "fileRenameMode": "force_rename", "localCreatedAt": local_created_at, "name": file_name,
            "parallelUpload": True, "parentFileId": "/",
            "partInfos": [{"partNumber": 1, "partSize": KNOWN_SIZE, "start": 0, "end": KNOWN_SIZE, "parallelHashCtx": {"partOffset": 0}}],
            "size": KNOWN_SIZE, "storyVideoFile": False, "type": "file",
            "userRegion": {"cityCode": "376", "provinceCode": "371"}
        }
        self.log(f'- 正在执行秒传: {file_name}')
        try:
            resp = requests.post(create_url, headers=headers, json=payload, timeout=10)
            if resp.status_code == 200:
                res_json = resp.json()
                if res_json.get("success"):
                    data = res_json.get("data", {})
                    file_id = data.get('fileId')
                    upload_type = "秒传" if data.get("rapidUpload") else "普通上传"
                    self.log(f" ✅ [上传成功] {upload_type} (ID: {file_id})")
                    return file_id, file_name
                else:
                    self.log(f" ❌ [上传失败] {res_json.get('message')}")
            else:
                self.log(f" ❌ [上传失败] HTTP {resp.status_code}")
        except Exception as e:
            self.log(f" ❌ [上传异常] {e}")
        return None, None

    def _step_2_share(self, file_id, file_name):
        self.log(f'- 正在分享文件: {file_id}...')
        url = "https://yun.139.com/orchestration/personalCloud-rebuild/outlink/v1.0/getOutLink"
        auth_cookie = f"ud_id={self.yun_uni}; token={self.auth_token};"
        headers = {
            "Authorization": self.Authorization, "Cookie": auth_cookie, "Content-Type": "application/json;charset=UTF-8",
            "User-Agent": "okhttp/4.12.0", "Origin": "https://yun.139.com", "Referer": "https://yun.139.com/w/",
            "x-yun-client-info": self.app_client_info, "x-yun-app-channel": "10000023",
            "x-huawei-channelsrc": "10000023", "x-yun-uni": self.yun_uni,
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
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            res_json = resp.json()
            if res_json.get("success"):
                self.log(" ✅ [分享成功] 已伪装APP渠道")
            else:
                self.log(f" ❌ [分享失败] {res_json.get('message')}")
        except Exception as e:
            self.log(f" ❌ [分享异常] {e}")

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

    @catch_errors
    def click(self):
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
            if app_type in ['cloud_app', 'email_app'] and task_type in ['month', 'day']:
                for task in tasks:
                    task_id = task.get('id')
                    task_name = task.get('name', '')
                    task_state = task.get('state', '')
                    if app_type == 'cloud_app' and task_id in [110, 113, 417, 409, 404]: continue
                    if app_type == 'email_app' and task_id in [1004, 1005, 1015, 1020]: continue
                    if task_state != 'FINISH':
                        self.log(f'- 去完成: {task_name} (ID: {task_id})')
                        self.do_task(task_id, task_type, app_type)
                        time.sleep(1)

    @catch_errors
    def do_task(self, task_id, task_type, app_type):
        task_url = f'https://caiyun.feixin.10086.cn/market/signin/task/click?key=task&id={task_id}'
        self.send_request(task_url, headers=self.jwtHeaders, cookies=self.cookies)
        if app_type == 'cloud_app' and task_type == 'day':
            if task_id == 106: self.run_upload_task()
            elif task_id == 107:
                self.log('- 执行笔记任务...')
                self.refresh_notetoken()
                self.create_note_flow()

    def refresh_notetoken(self):
        note_url = 'http://mnote.caiyun.feixin.10086.cn/noteServer/api/authTokenRefresh.do'
        payload = {"authToken": self.auth_token, "userPhone": self.account}
        headers = {'Content-Type': 'application/json; charset=UTF-8', 'Host': 'mnote.caiyun.feixin.10086.cn'}
        try:
            res = self.send_request(note_url, headers=headers, data=payload, method="POST")
            self.note_token = res.headers.get('NOTE_TOKEN')
            self.note_auth = res.headers.get('APP_AUTH')
        except: pass

    def create_note_flow(self):
        sync_url = 'http://mnote.caiyun.feixin.10086.cn/noteServer/api/syncNotebookV3.do'
        headers = {'APP_NUMBER': self.account, 'APP_AUTH': self.note_auth, 'NOTE_TOKEN': self.note_token, 
                   'Host': 'mnote.caiyun.feixin.10086.cn', 'Content-Type': 'application/json; charset=UTF-8'}
        payload = {"addNotebooks": [], "delNotebooks": [], "notebookRefs": [], "updateNotebooks": []}
        try:
            res = self.send_request(sync_url, headers=headers, data=payload, method='POST').json()
            self.notebook_id = res['notebooks'][0]['notebookId']
            create_url = 'http://mnote.caiyun.feixin.10086.cn/noteServer/api/createNote.do'
            note_id = ''.join(random.choice('abcdef0123456789') for _ in range(32))
            ts = str(int(time.time() * 1000))
            note_payload = {
                "archived": 0, "attachmentdir": note_id, "attachments": [], 
                "contents": [{"data": "AutoTask", "noteId": note_id, "type": "RICHTEXT"}],
                "createtime": ts, "noteid": note_id, "tags": [{"id": self.notebook_id, "text": "默认笔记本"}],
                "title": "AutoTask", "updatetime": ts, "userphone": self.account
            }
            res_create = self.send_request(create_url, headers=headers, data=note_payload, method="POST")
            if res_create.status_code == 200: self.log(' └ 笔记创建成功')
        except: self.log(' └ 笔记创建失败')

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
            if res["result"].get("shakePrizeconfig"): count += 1
        if count > 0: self.log(f"👋 摇一摇中奖: {count}次")

    @catch_errors
    def surplus_num(self):
        info_url = 'https://caiyun.feixin.10086.cn/market/playoffic/drawInfo'
        draw_url = "https://caiyun.feixin.10086.cn/market/playoffic/draw"
        res = self.send_request(info_url, headers=self.jwtHeaders).json()
        if res.get('msg') == 'success':
            remain = res['result'].get('surplusNumber', 0)
            if remain > 50 - self.draw:
                self.log(f"🎁 剩余抽奖: {remain}次, 开始抽奖...")
                for _ in range(self.draw):
                    d_res = self.send_request(draw_url, headers=self.jwtHeaders).json()
                    if d_res.get("code") == 0: 
                        self.log(f" └ 获得: {d_res['result'].get('prizeName')}")
                    self.sleep()

    @catch_errors
    def backup_cloud(self):
        url = 'https://caiyun.feixin.10086.cn/market/backupgift/info'
        res = self.send_request(url, headers=self.jwtHeaders).json()
        state = res.get('result', {}).get('state', -1)
        if state == 0:
            rec_url = 'https://caiyun.feixin.10086.cn/market/backupgift/receive'
            r = self.send_request(rec_url, headers=self.jwtHeaders).json()
            self.log(f"📥 领取备份奖励: {r.get('result', {}).get('result')}云朵")
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
        rec_url = "https://caiyun.feixin.10086.cn/market/signin/page/receive"
        res = self.send_request(rec_url, headers=self.jwtHeaders, cookies=self.cookies).json()
        prize_url = f"https://caiyun.feixin.10086.cn/market/prizeApi/checkPrize/getUserPrizeLogPage?currPage=1&pageSize=15&_={self.timestamp}"
        p_res = self.send_request(prize_url, headers=self.jwtHeaders, cookies=self.cookies).json()
        recv = res["result"].get("receive", 0)
        total = res["result"].get("total", 0)
        pending = ""
        try:
            for item in p_res.get('result', {}).get('result', []):
                if item.get('flag') == 1: 
                    pending += f" [{item.get('prizeName')}]"
        except: pass
        self.log(f"\n☁️ 待领: {recv} | 总云朵: {total}")
        if pending: self.log(f"🎁 未领奖品: {pending}")

    def run(self, view_only=False, skip_game=False):
        if not self.valid: return f"❌ 账号 {self.encrypt_account} 配置错误\n"
        self.log(f"========== 用户 [{self.encrypt_account}] ==========")
        if not self.jwt():
            self.log("❌ 登录失败 (SSO/JWT错误)")
            return self.log_str
        
        if view_only:
            self.log("查看模式已省略，请使用正常模式运行")
            return self.log_str
        
        # 3.1 跑游戏 (如果开启且不跳过)
        if GAME_ENABLED and not skip_game:
            self.run_game()
        
        # 3.2 跑日常
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
        
        return self.log_str

# ================= 🚀 主执行逻辑 =================
def run_all_accounts():
    """执行完整流程：互助(批量) -> 个人任务(游戏+日常合并)"""
    full_log = f"【移动云盘 - 全自动任务】\n"
    full_log += f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    full_log += "=" * 50 + "\n\n"
    
    if not ydypCK:
        return full_log + "⛔️ 未配置 YDYP_CK\n"
    
    # --- 步骤1：初始化并登录所有账号 ---
    cookies = [ck.strip() for ck in re.split(r'[&\n]', ydypCK) if ck.strip()]
    accounts = []
    phone_numbers = []
    
    print("⏳ 正在验证所有账号登录状态...") 
    for ck in cookies:
        yp = YP(ck)
        # 尝试登录
        if yp.valid and yp.jwt():
            accounts.append(yp)
            phone_numbers.append(yp.account)
            print(f"  ✅ 账号 {yp.encrypt_account} 登录成功")
        else:
            full_log += f"⚠️ 账号 {yp.encrypt_account} 登录失败(CK失效)，已跳过\n"
            print(f"  ❌ 账号 {yp.encrypt_account} 登录失败")
    
    if not accounts:
        return full_log + "\n⛔️ 没有可用的有效账号，请更新CK！\n"
    
    full_log += f"✅ 成功加载 {len(accounts)} 个有效账号\n\n"
    
    # --- 步骤2：执行互助 (必须先让所有人互助完，才能最大化游戏次数) ---
    if INVITE_ENABLED and len(accounts) > 1:
        full_log += "🤝 ===== 互助邀请阶段 =====\n"
        for i, helper in enumerate(accounts):
            full_log += f"[{helper.encrypt_account}] 开始助力他人...\n"
            for j, target_phone in enumerate(phone_numbers):
                if i != j:
                    helper.do_invite(target_phone)
            # 收集互助日志并清空
            full_log += helper.log_str + "\n"
            helper.log_str = "" 
            time.sleep(2.5)
        full_log += "✅ 互助阶段完成\n\n"
    
    # --- 步骤3：个人任务循环 (游戏 + 日常 放在一起跑) ---
    for i, account in enumerate(accounts):
        full_log += f"👤 ===== 账号 {i+1}: {account.encrypt_account} =====\n"
        
        # 3.1 跑游戏 (如果开启)
        if GAME_ENABLED:
            account.run_game()
            full_log += account.log_str
            account.log_str = ""
        
        # 3.2 跑日常 (跳过游戏参数设为True，因为上面刚跑过)
        full_log += account.run(view_only=False, skip_game=True)
        
        full_log += account.log_str
        account.log_str = ""
        
        full_log += "\n" 
        time.sleep(3) # 账号间休息
    
    full_log += "=" * 50 + "\n"
    full_log += f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    return full_log

if __name__ == "__main__":
    print(run_all_accounts())
