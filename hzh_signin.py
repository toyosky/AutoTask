import requests
import time
import re
import json
import os
from datetime import datetime

# ================= 配置区域 =================
USER_TOKEN = os.getenv("HZH_USER_TOKEN")
SK_VALUE = os.getenv("HZH_SK_VALUE")
USER_AGENT = "HUAZHU/android/PDRM00/13/8.10.2/RNWEBVIEW"
RAW_COOKIE = os.getenv("HZH_RAW_COOKIE")
PUSHPLUS_TOKEN = os.getenv("PUSHPLUS_TOKEN")
# ===========================================

def send_pushplus(title, content):
    """发送 PushPlus 通知"""
    if not PUSHPLUS_TOKEN:
        print("ℹ️ 未配置 PUSHPLUS_TOKEN，跳过微信推送。")
        return
    
    url = "http://www.pushplus.plus/send"
    payload = {
        "token": PUSHPLUS_TOKEN,
        "title": title,
        "content": content.replace("\n", "<br>"),
        "template": "html"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("🔔 微信推送成功")
        else:
            print(f"❌ 微信推送失败: {response.text}")
    except Exception as e:
        print(f"🚨 推送接口异常: {str(e)}")

def get_timestamp():
    now = time.time()
    return int(now), int(now * 1000)

def update_cookie(cookie, new_ms_ts):
    pattern = r'(ec=[^-]+-)(\d{13})(-[^;]*)'
    replacement = r'\g<1>' + str(new_ms_ts) + r'\g<3>'
    return re.sub(pattern, replacement, cookie)

def do_sign_in():
    ts_sec, ts_ms = get_timestamp()
    url = f"https://appgw.huazhu.com/game/sign_in?date={ts_sec}"
    current_cookie = update_cookie(RAW_COOKIE, ts_ms)
    
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
                year_count = content.get("yearSignInCount", 0)
                
                # 获取实际获得的奖励（awardGetType 为 "1" 的才是已获得）
                awards = content.get("award", [])
                obtained_awards = [a for a in awards if a.get("awardGetType") == "1"]
                
                # 构建标题：直观展示关键信息
                if obtained_awards:
                    award_names = ", ".join([a.get("awardName", "未知") for a in obtained_awards])
                    title = f"✅ 签到成功 | +{point}积分 +{act_point}活跃 | 🎁{award_names} | 年度{year_count}天"
                else:
                    title = f"✅ 签到成功 | +{point}积分 +{act_point}活跃 | 年度{year_count}天"
                
                # 详细内容
                report_list = []
                report_list.append(f"<b>📅 签到时间：</b>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                report_list.append(f"<b>💰 基础积分：</b>+{point}")
                report_list.append(f"<b>🌟 活跃分值：</b>+{act_point}")
                report_list.append(f"<b>📆 年度签到：</b>{year_count} 天")
                
                if obtained_awards:
                    report_list.append("<b>🎁 盲盒奖励：</b>")
                    for a in obtained_awards:
                        name = a.get("awardName", "未知")
                        value = a.get("awardValue", "")
                        if value:
                            report_list.append(f"  • {name}（{value}）")
                        else:
                            report_list.append(f"  • {name}")
                else:
                    report_list.append("<b>🎁 盲盒奖励：</b>今日无盲盒")
                
                final_report = "\n".join(report_list)
                print(title)
                print(final_report)
                send_pushplus(title, final_report)
                    
            elif code == 5004 or "已签到" in msg:
                title = f"ℹ️ 今日已签到"
                report_list = []
                report_list.append(f"<b>📅 检查时间：</b>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                report_list.append(f"<b>提示信息：</b>{msg}")
                final_report = "\n".join(report_list)
                print(title)
                print(final_report)
                send_pushplus(title, final_report)
            else:
                title = f"❌ 签到失败 (Code: {code})"
                report_list = []
                report_list.append(f"<b>📅 失败时间：</b>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                report_list.append(f"<b>错误原因：</b>{msg}")
                final_report = "\n".join(report_list)
                print(title)
                print(final_report)
                send_pushplus(title, final_report)
        else:
            title = f"⚠️ 网络异常 (状态码: {response.status_code})"
            report_list = []
            report_list.append(f"<b>📅 异常时间：</b>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report_list.append(f"<b>状态码：</b>{response.status_code}")
            final_report = "\n".join(report_list)
            print(title)
            print(final_report)
            send_pushplus(title, final_report)
            
    except Exception as e:
        title = f"🚨 脚本运行异常"
        report_list = []
        report_list.append(f"<b>📅 异常时间：</b>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_list.append(f"<b>错误细节：</b>{str(e)}")
        final_report = "\n".join(report_list)
        print(title)
        print(final_report)
        send_pushplus(title, final_report)

if __name__ == "__main__":
    do_sign_in()
