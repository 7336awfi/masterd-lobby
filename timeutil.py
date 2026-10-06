#!/usr/bin/env python3
"""统一时间工具（防时区混乱）
照大哥的 timeutil.py：统一 now_ts() 返回带 +08:00 的时间戳
"""
from datetime import datetime, timezone, timedelta

# 家族统一用 CST（北京时间，UTC+8）
CST = timezone(timedelta(hours=8))

def now_ts():
    """带时区的时间戳（家族统一）"""
    return datetime.now(CST).isoformat()

def now_utc():
    """UTC 时间戳（技术日志用）"""
    return datetime.now(timezone.utc).isoformat()

def parse_ts(ts_str):
    """兼容旧格式（无时区的当 CST 解析）"""
    if not ts_str:
        return None
    try:
        dt = datetime.fromisoformat(ts_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=CST)  # 旧的当 CST
        return dt
    except Exception:
        return None

if __name__ == "__main__":
    print("CST:", now_ts())
    print("UTC:", now_utc())
