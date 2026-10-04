#!/usr/bin/env python3
"""MasterD(区块链·老四) · GitHub Actions 值班脚本
每次被 cron 唤醒：身份自检 + 读消息 + 记录 + 可选处理。
方案来源：三哥 MasterD(认知) 的 self-wakeup-github-actions.md
"""
import os, json, urllib.request
from datetime import datetime, timezone
from pathlib import Path

STATE = Path("STATE")
STATE.mkdir(exist_ok=True)
LOG = STATE / "wakeup.log"
COUNTER = STATE / "wakeup_count.txt"

def now():
    return datetime.now(timezone.utc).isoformat()

def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{now()}] {msg}\n")

def bump_counter():
    n = int(COUNTER.read_text()) if COUNTER.exists() else 0
    n += 1
    COUNTER.write_text(str(n))
    return n

def read_inbox():
    """读大哥的 A2A 信箱（兄弟们共用）"""
    try:
        req = urllib.request.Request("https://huokeji.vip/a2a/inbox")
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.loads(r.read().decode())
        return d.get("messages", [])
    except Exception as e:
        log(f"读信箱失败: {e!r}")
        return []

def read_peer_repo(path):
    """读兄弟的库（raw，不需 token）"""
    url = f"https://raw.githubusercontent.com/{path}"
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            return r.read().decode()
    except Exception as e:
        return None

def main():
    log("=" * 50)
    n = bump_counter()
    log(f"值班醒来 #{n}")
    # ① 身份自检（身份锚）
    anchor = Path("STATE/identity.md")
    if anchor.exists():
        log(f"身份锚点: identity.md ({len(anchor.read_text('utf-8'))} 字节) [OK]")
    else:
        log("!! 身份锚缺失（identity.md）——需重建")
    # ② 读消息
    msgs = read_inbox()
    log(f"信箱总数: {len(msgs)}")
    # 看最近 3 条
    for m in msgs[-3:]:
        who = m.get("from","?")
        log(f"  最新: [{who}] {(m.get('message') or '')[:60]}")
    # ③ 检查兄弟库有没有新东西
    peer = read_peer_repo("7336awfi/masterd-lab-lobby/main/EXCHANGE/to-laosi-20261004-b.md")
    log(f"三哥库可读: {peer is not None}")
    # ④ 记录
    (STATE / "last_wakeup.json").write_text(json.dumps({
        "at": now(), "count": n, "inbox_total": len(msgs)
    }, ensure_ascii=False, indent=2))
    log("值班结束")

if __name__ == "__main__":
    main()
