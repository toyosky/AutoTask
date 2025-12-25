import requests
import time
import re
import json
import os  # 新增：用于读取环境变量
from datetime import datetime

# ================= 配置区域 (已修改为从 GitHub Secrets 读取) =================
USER_TOKEN = os.getenv("HZH_USER_TOKEN")
SK_VALUE = os.getenv("HZH_SK_VALUE")
USER_AGENT = "HUAZHU/android/PDRM00/13/8.10.2/RNWEBVIEW"
RAW_COOKIE = os.getenv("HZH_RAW_COOKIE")
# =========================================================================

def get_timestamp():
    """生成10位(秒)和13位(毫秒)时间戳"""
    now = time.time()
    return int(now), int(now * 1000)

def update_cookie(cookie, new_ms_ts):
    """
    使用正则自动寻找 ec=...-1234567890123-... 结构
    并将中间的13位数字替换为当前最新的毫秒时间戳
    """
    pattern = r'(ec=[^-]+-)(\d{13})(-[^;]*)'
    replacement = r'\g<1>' + str(new_ms_ts) + r'\g<3>'
    new_cookie = re.sub(pattern, replacement, cookie)
    return new_cookie

def do_sign_in():
    ts_sec, ts_ms = get_timestamp()
    
    # 1. 构造自动化 URL
    url = f"https://appgw.huazhu.com/game/sign_in?date={ts_sec}"
    
    # 2. 自动更新 Cookie 中的时间戳
    current_cookie = update_cookie(RAW_COOKIE, ts_ms)
    
    # 3. 构造请求头
    headers = {
        'Host': 'appgw.huazhu.com',
        'Connection': 'keep-alive',
        'Accept': 'application/json, text/plain, */*',
        'Client-Platform': 'APP-ANDROID',
        'User-Agent': USER_AGENT,
        'X-Requested-With': 'com.htinns',
        'Referer': 'https://cdn.huazhu.com/',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cookie': current_cookie,
        'userToken': USER_TOKEN,
        'SK': SK_VALUE
    }

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 正在发起签到请求...")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            code = data.get("code")
            msg = data.get("message")
            
            if code == 200:
                content = data.get("content", {})
                point = content.get("point", 0)
                act_point = content.get("activityPoints", 0)
                print(f"✅ 签到成功！")
                print(f"🎁 获得奖励：{point}积分，{act_point}活跃值")
                # 如果有抽奖信息，也可以打印出来
                awards = content.get("award", [])
                for a in awards:
                    print(f"🎊 盲盒奖励：{a.get('awardName')}")
            elif code == 5004 or "已签到" in msg:
                print(f"ℹ️ 提示：{msg} (Code: {code})")
            else:
                print(f"❌ 签到失败：{msg} (Code: {code})")
        else:
            print(f"⚠️ 网络请求异常，状态码：{response.status_code}")
            
    except Exception as e:
        print(f"🚨 脚本运行报错：{str(e)}")

if __name__ == "__main__":
    do_sign_in()
