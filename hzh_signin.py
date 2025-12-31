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

def send_pushplus(content):
    """发送 PushPlus 通知"""
    if not PUSHPLUS_TOKEN:
        print("ℹ️ 未配置 PUSHPLUS_TOKEN，跳过微信推送。")
        return
    
    url = "http://www.pushplus.plus/send"
    payload = {
        "token": PUSHPLUS_TOKEN,
        "title": "华住签到调试报告", # 修改标题以便区分
        "content": content.replace("\n", "<br>"), # 将换行符转为 HTML 换行
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

    # 用于累积通知内容
    report_list = []
    report_list.append(f"<b>📅 运行时间：</b>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()

            # ================= 调试代码开始 =================
            # 无论成功失败，先把原始 JSON 格式化并加入报告
            # ensure_ascii=False 保证中文正常显示
            raw_json_debug = json.dumps(data, ensure_ascii=False, indent=2)
            report_list.append("<br><b>🐛 [调试] 原始响应数据：</b>")
            report_list.append(f"<pre>{raw_json_debug}</pre>") # 使用 pre 标签保持 JSON 缩进格式
            # ================= 调试代码结束 =================

            code = data.get("code")
            msg = data.get("message")
            
            if code == 200:
                content = data.get("content", {})
                point = content.get("point", 0)
                act_point = content.get("activityPoints", 0)
                report_list.append("<b>✅ 状态：签到成功！</b>")
                report_list.append(f"💰 获得积分：{point}")
                report_list.append(f"🌟 活跃分值：{act_point}")
                
                # 盲盒/额外奖励处理 (旧逻辑保留，方便对比)
                awards = content.get("award", [])
                if awards:
                    report_list.append("🎁 <b>盲盒奖励：</b>")
                    for a in awards:
                        # 尝试增加鲁棒性，打印整个 award 对象
                        report_list.append(f"  - {str(a)}")
                else:
                    report_list.append("🎁 盲盒奖励：无 (根据当前逻辑)")
                    
            elif code == 5004 or "已签到" in msg:
                report_list.append(f"<b>ℹ️ 状态：任务已完成</b>")
                report_list.append(f"提示信息：{msg}")
            else:
                report_list.append(f"<b>❌ 状态：签到失败</b>")
                report_list.append(f"原因：{msg} (Code: {code})")
        else:
            report_list.append(f"<b>⚠️ 网络异常</b>")
            report_list.append(f"状态码：{response.status_code}")
            
    except Exception as e:
        report_list.append(f"<b>🚨 脚本运行报错</b>")
        report_list.append(f"错误细节：{str(e)}")

    # 打印到控制台（GitHub Action 日志可见）
    final_report = "\n".join(report_list)
    print(final_report)
    
    # 发送到微信
    send_pushplus(final_report)

if __name__ == "__main__":
    do_sign_in()
