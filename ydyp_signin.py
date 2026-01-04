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
        self.log_str = "" # 存储当前账号的日志
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
            self.encrypt_account = self.account[:3] + "****" + self.account[7:]
        except:
            self.Authorization = None
            self.encrypt_account = "格式错误账号"

        self.jwtHeaders = {'User-Agent': ua, 'Host': 'caiyun.feixin.10086.cn:7071'}

    def log(self, msg):
        print(msg)
        self.log_str += msg + "\n"

    def catch_errors(func):
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                self.log(f"❌ 错误: {str(e)}")
            return None
        return wrapper

    def send_request(self, url, headers=None, cookies=None, data=None, method='GET'):
        self.session.headers.update(headers or {})
        if cookies: self.session.cookies.update(cookies)
        try:
            if method == 'POST':
                resp = self.session.post(url, json=data) if isinstance(data, dict) else self.session.post(url, data=data)
            else:
                resp = self.session.get(url, params=data)
            return resp
        except:
            return None

    def sso(self):
        url = 'https://orches.yun.139.com/orchestration/auth-rebuild/token/v1.0/querySpecToken'
        headers = {'Authorization': self.Authorization, 'User-Agent': ua, 'Content-Type': 'application/json', 'Host': 'orches.yun.139.com'}
        data = {"account": self.account, "toSourceId": "001005"}
        res = self.send_request(url, headers=headers, data=data, method='POST')
        if res and res.json()['success']: return res.json()['data']['token']
        return None

    def jwt(self):
        token = self.sso()
        if not token: 
            self.log("- CK可能失效")
            return False
        url = f"https://caiyun.feixin.10086.cn:7071/portal/auth/tyrzLogin.action?ssoToken={token}"
        res = self.send_request(url, headers=self.jwtHeaders, method='POST')
        if res and res.json().get('code') == 0:
            self.jwtHeaders['jwtToken'] = res.json()['result']['token']
            return True
        return False

    @catch_errors
    def signin_status(self):
        url = 'https://caiyun.feixin.10086.cn/market/signin/page/info?client=app'
        res = self.send_request(url, headers=self.jwtHeaders).json()
        if res.get('msg') == 'success':
            if res['result'].get('todaySignIn'): self.log('✅ 已签到')
            else:
                s_url = 'https://caiyun.feixin.10086.cn/market/manager/commonMarketconfig/getByMarketRuleName?marketName=sign_in_3'
                self.send_request(s_url, headers=self.jwtHeaders)
                self.log('✅ 签到操作完成')

    @catch_errors
    def receive_cloud(self):
        # 简单只做查询云朵总数
        url = "https://caiyun.feixin.10086.cn/market/signin/page/receive"
        res = self.send_request(url, headers=self.jwtHeaders).json()
        if res and 'result' in res:
             self.log(f"☁️ 当前云朵: {res['result'].get('total', '未知')}")
             if res['result'].get('receive') > 0: self.log(f"   (待领取: {res['result'].get('receive')})")

    def run(self):
        if not self.Authorization: return f"账号 {self.encrypt_account} 配置错误\n"
        self.log(f"用户 [{self.encrypt_account}] 开始任务")
        if self.jwt():
            self.signin_status()
            self.receive_cloud()
            # 这里省略了复杂的任务逻辑以精简代码，如需完整任务可把之前的逻辑贴回来
        else:
            self.log("登录失败")
        return self.log_str

def run_ydyp():
    """运行移动云盘任务并返回日志"""
    full_log = "【移动云盘任务】\n"
    if not ydypCK:
        return full_log + "⛔️ 未配置 YDYP_CK 环境变量\n"

    cookies = re.split(r'[&\n]', ydypCK)
    for i, account in enumerate(cookies, 1):
        if not account.strip(): continue
        yp = YP(account)
        full_log += yp.run() + "\n"
        time.sleep(2)
        
    return full_log
