import requests
import time
import re
import os
from datetime import datetime

# ================= 配置区域 =================
USER_TOKEN = os.getenv("HZH_USER_TOKEN")
SK_VALUE = os.getenv("HZH_SK_VALUE")
USER_AGENT = "HUAZHU/android/PDRM00/13/8.10.2/RNWEBVIEW"
RAW_COOKIE = os.getenv("HZH_RAW_COOKIE")
# ===========================================

def get_timestamp():
    now = time.time()
    return int(now), int(now * 1000)

def update_cookie(cookie, new_ms_ts):
    pattern = r'(ec=[^-]+-)(\d{13})(-[^;]*)'
    replacement = r'\g<1>' + str(new_ms_ts) + r'\g<3>'
    return re.sub(pattern, replacement, cookie)

def run_hzh():
    """运行华住签到并返回日志字符串"""
    log_content = "【华住会签到】\n"
    
    if not USER_TOKEN or not SK_VALUE:
        return log_content + "❌ 缺少环境变量 HZH_USER_TOKEN 或 HZH_SK_VALUE\n"

    ts_sec, ts_ms = get_timestamp()
    url = f"https://appgw.huazhu.com/game/sign_in?date={ts_sec}"
    current_cookie = update_cookie(RAW_COOKIE, ts_ms) if RAW_COOKIE else ""
    
    headers = {
        'Host': 'appgw.huazhu.com',
        'User-Agent': USER_AGENT,
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
                act_point = content.get("activityPoints", 0) # 新增：活跃度
                year_count = content.get("yearSignInCount", 0)
                
                # 优化奖励获取逻辑
                awards = content.get("award", [])
                # 筛选实际获得的奖励 (awardGetType 为 "1")
                obtained_awards = [a for a in awards if a.get("awardGetType") == "1"]
                
                log_content += f"✅ 签到成功 | 积分+{point} | 活跃+{act_point} | 年度:{year_count}天\n"
                
                if obtained_awards:
                    log_content += "🎁 盲盒奖励：\n"
                    for a in obtained_awards:
                        name = a.get("awardName", "未知")
                        value = a.get("awardValue", "")
                        # 格式化输出：如果有数值则显示数值
                        if value:
                            log_content += f"   • {name} ({value})\n"
                        else:
                            log_content += f"   • {name}\n"
                else:
                    log_content += "🎁 盲盒奖励：今日无盲盒\n"
                    
            elif code == 5004 or "已签到" in msg:
                log_content += f"ℹ️ 今日已签到: {msg}\n"
            else:
                log_content += f"❌ 失败: {msg} (Code: {code})\n"
        else:
            log_content += f"⚠️ 网络错误: {response.status_code}\n"
            
    except Exception as e:
        log_content += f"🚨 运行异常: {str(e)}\n"
    
    return log_content + "\n"
