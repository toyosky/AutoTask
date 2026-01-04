import os
import requests
from hzh_signin import run_hzh
from ydyp_signin import run_ydyp

# 获取 PushPlus Token
PUSHPLUS_TOKEN = os.getenv("PUSHPLUS_TOKEN")

def send_pushplus(title, content):
    if not PUSHPLUS_TOKEN:
        print("ℹ️ 未配置 PUSHPLUS_TOKEN，跳过推送")
        return
    
    url = "http://www.pushplus.plus/send"
    payload = {
        "token": PUSHPLUS_TOKEN,
        "title": title,
        "content": content.replace("\n", "<br>"), # 换行转HTML
        "template": "html"
    }
    try:
        requests.post(url, json=payload, timeout=10)
        print("🔔 推送成功")
    except Exception as e:
        print(f"🚨 推送失败: {e}")

if __name__ == "__main__":
    print(">>> 开始执行任务...")
    
    # 1. 执行华住
    log_hzh = run_hzh()
    print(">>> 华住任务完成")
    
    # 2. 执行移动云盘
    log_ydyp = run_ydyp()
    print(">>> 移动云盘任务完成")
    
    # 3. 合并内容
    final_content = log_hzh + "\n" + "-"*20 + "\n" + log_ydyp
    
    # 4. 打印到控制台（方便Github Action日志查看）
    print(final_content)
    
    # 5. 统一推送
    send_pushplus("每日签到汇总", final_content)
