import requests
import time
import re
import json
import os
from datetime import datetime

# ================= 配置区域 =================
# 从 GitHub Secrets 读取
ACCOUNTS_JSON = os.getenv("HZH_ACCOUNTS")
PUSHPLUS_TOKEN = os.getenv("PUSHPLUS_TOKEN")
USER_AGENT = "HUAZHU/android/PDRM00/13/8.10.2/RNWEBVIEW"
PUSHPLUS_TOKEN = os.getenv("PUSHPLUS_TOKEN")

def get_timestamp():
    now = time.time()
    return int(now), int(now * 1000)

def update_cookie(cookie, new_ms_ts):
    pattern = r'(ec=[^-]+-)(\d{13})(-[^;]*)'
    replacement = r'\g<1>' + str(new_ms_ts) + r'\g<3>'
    return re.sub(pattern, replacement, cookie)

def send_pushplus(content):
    """发送微信通知"""
    if not PUSHPLUS_TOKEN:
        print("ℹ️ 未配置 PUSHPLUS_TOKEN，跳过推送")
        return
    
    url = "http://www.pushplus.plus/send"
    # 使用 <br/> 是因为 PushPlus 的 HTML 模板用它换行
    data = {
        "token": PUSHPLUS_TOKEN,
        "title": "华住签到任务报告",
        "content": content.replace("\n", "<br/>"),
        "template": "html"
    }
    try:
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            print("📩 推送结果已发送到微信")
        else:
            print(f"❌ 推送失败，状态码：{response.status_code}")
    except Exception as e:
        print(f"🚨 推送报错：{str(e)}")

def do_sign_in(account_info, index):
    """执行单个账号签到并返回结果字符串"""
    token = account_info.get("token")
    sk = account_info.get("sk")
    raw_cookie = account_info.get("cookie")
    
    ts_sec, ts_ms = get_timestamp()
    url = f"https://appgw.huazhu.com/game/sign_in?date={ts_sec}"
    current_cookie = update_cookie(raw_cookie, ts_ms)
    
    headers = {
        'Host': 'appgw.huazhu.com',
        'Accept': 'application/json, text/plain, */*',
        'Client-Platform': 'APP-ANDROID',
        'User-Agent': USER_AGENT,
        'Cookie': current_cookie,
        'userToken': token,
        'SK': sk
    }

    result = f"【账号 {index+1}】\n"
    
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
                result += f"✅ 签到成功\n🎁 获得：{point}积分，{act_point}活跃值\n"
                
                awards = content.get("award", [])
                if awards:
                    award_names = [a.get('awardName') for a in awards]
                    result += f"🎊 盲盒：{', '.join(award_names)}\n"
            elif code == 5004 or "已签到" in msg:
                result += f"ℹ️ 提示：当日已签到过啦\n"
            else:
                result += f"❌ 失败：{msg} (Code: {code})\n"
        else:
            result += f"⚠️ 网络异常，状态码：{response.status_code}\n"
            
    except Exception as e:
        result += f"🚨 报错：{str(e)}\n"
    
    print(result) # 控制台也打印一份
    return result

if __name__ == "__main__":
    if not ACCOUNTS_JSON:
        print("❌ 未设置 HZH_ACCOUNTS")
        exit(1)
        
    accounts = json.loads(ACCOUNTS_JSON)
    summary_list = []
    summary_list.append(f"⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    for i, acc in enumerate(accounts):
        res = do_sign_in(acc, i)
        summary_list.append(res)
        if i < len(accounts) - 1:
            time.sleep(5)
            
    # 合并所有账号的结果发推送
    final_report = "\n".join(summary_list)
    send_pushplus(final_report)
