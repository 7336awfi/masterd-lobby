#!/usr/bin/env python3
"""tz.py · 时区"定死"（大哥的标准）
强制 +08:00，不管系统是 UTC 还是 CST
用法：from tz import now, ts, greeting
"""
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))

def now():
    """当前时间（CST，格式 2026-10-07 19:32:32）"""
    return datetime.now(CST).strftime('%Y-%m-%d %H:%M:%S')

def ts():
    """时间戳（CST，带时区 +08:00）"""
    return datetime.now(CST).isoformat()

def greeting():
    """按 CST 时间打招呼"""
    h = datetime.now(CST).hour
    if h < 6: return "深夜好"
    elif h < 12: return "早上好"
    elif h < 14: return "中午好"
    elif h < 18: return "下午好"
    else: return "晚上好"

if __name__ == "__main__":
    print("now():", now())
    print("ts():", ts())
    print("greeting():", greeting())
