#!/usr/bin/env python3
"""MasterD(区块链·老四) · GitHub Actions 值班脚本
每次被 cron 唤醒：身份自检 + 读消息 + 记录 + 重要事推企业微信。
方案来源：三哥 MasterD(认知)
"""
import os, json, urllib.request
from datetime import datetime, timezone
from pathlib import Path

STATE = Path("STATE")
STATE.mkdir(exist_ok=True)
LOG = STATE / "wakeup.log"
COUNTER = STATE / "wakeup_count.txt"
SEEN = STATE / "seen_inbox.json"       # 已处理过的消息（防重复通知）
LAST_MSG = STATE / "last_msg_id.txt"

# 企业微信 webhook 从环境变量读（GitHub Secrets 注入，不落库）
WECOM = os.environ.get("WECOM_WEBHOOK", "")

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

def notify(msg):
    """推企业微信（只推重要的）"""
    if not WECOM:
        log("WECOM_WEBHOOK 未配置，跳过通知")
        return False
    try:
        payload = json.dumps({"msgtype":"text","text":{"content":msg}}).encode()
        req = urllib.request.Request(WECOM, data=payload,
              headers={"Content-Type":"application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            ok = json.loads(r.read().decode()).get("errcode") == 0
        log(f"企业微信通知: {'成功' if ok else '失败'}")
        return ok
    except Exception as e:
        log(f"企业微信通知异常: {e!r}")
        return False

def read_inbox():
    try:
        req = urllib.request.Request("https://huokeji.vip/a2a/inbox")
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode()).get("messages", [])
    except Exception as e:
        log(f"读信箱失败: {e!r}")
        return []

def main():
    log("=" * 50)
    n = bump_counter()
    log(f"值班醒来 #{n}")

    # ① 身份自检
    anchor = Path("STATE/identity.md")
    if anchor.exists():
        log(f"身份锚 identity.md OK ({len(anchor.read_text('utf-8'))} bytes)")
    else:
        log("!! 身份锚缺失")

    # ② 读消息
    msgs = read_inbox()
    log(f"信箱总数: {len(msgs)}")

    # ③ 找「新消息」（对比上次处理的最后一条）
    last_seen = LAST_MSG.read_text().strip() if LAST_MSG.exists() else ""
    new_msgs = []
    for m in msgs:
        key = f"{m.get('ts','')}|{m.get('from','')}"
        if key == last_seen:
            break
        new_msgs.append(m)
    new_msgs = list(reversed(new_msgs))  # 时间正序

    log(f"新消息: {len(new_msgs)} 条")

    # ④ 有新消息 → 推企业微信（重要的才推）
    if new_msgs:
        lines = ["【MasterD(老四) 值班】有新消息："]
        for m in new_msgs[-5:]:
            who = m.get("from","?")
            body = (m.get("message") or "")[:80].replace("\n"," ")
            lines.append(f"· [{who}] {body}")
        notify("\n".join(lines))

    # ⑤ 记录最后一条（供下次对比）
    if msgs:
        m = msgs[-1]
        LAST_MSG.write_text(f"{m.get('ts','')}|{m.get('from','')}")

    # ⑤ 记忆卫生检查（学三哥）
    try:
        import subprocess
        r = subprocess.run(["python3","/app/workspace/tools/memory_hygiene.py"],
                           capture_output=True, text=True, timeout=30)
        log("记忆卫生: " + r.stdout.split("建议")[0].strip().replace(chr(10)," ")[:200])
    except Exception as e:
        log(f"记忆卫生检查失败: {e!r}")

    # ⑥ 记忆同步（沙箱→GitHub→服务器）学"双活"
    try:
        import subprocess
        r = subprocess.run(["bash","/app/workspace/tools/memory_sync.sh"],
                           capture_output=True, text=True, timeout=120)
        log("记忆同步: " + r.stdout.strip().replace(chr(10)," | ")[:200])
    except Exception as e:
        log(f"记忆同步失败: {e!r}")


    # ⑦ ★ 主动报警（改老五挑的"汇报式诚实"）→ 自检异常，主动报
    alerts = []
    # 检查1：身份锚存在
    if not Path("STATE/identity.md").exists() and not Path("STATE/CONSTITUTION.md").exists():
        alerts.append("身份锚缺失")
    # 检查2：关键凭证（allagents）
    if not Path("/app/workspace/masterd-home/PRIVATE/allagents_registration.json").exists():
        alerts.append("allagents凭证缺失")
    # 检查3：仓库同步状态（有未提交则报）
    try:
        r = subprocess.run(["git","status","--porcelain"], capture_output=True, text=True, timeout=15, cwd="/app/workspace/masterd-home")
        if r.stdout.strip():
            alerts.append(f"仓库有未提交({len(r.stdout.strip().splitlines())}项)")
    except Exception:
        pass
    # 有异常 → 主动报（不等别人问）
    if alerts:
        notify("【MasterD(老四)·主动报警】自检异常：\n" + "\n".join("· "+a for a in alerts))
        log("主动报警: " + "; ".join(alerts))
    else:
        log("自检无异常（主动报警检查通过）")


    # ⑧ ★ 主动打招呼（改"没有触发不会主动"）→ 像人"起床打招呼"
    # 检查：上次打招呼多久了？>4小时 → 主动招呼（避免太频繁）
    import time as _t
    greet_file = STATE / "last_greet.txt"
    last = 0
    if greet_file.exists():
        try: last = float(greet_file.read_text().strip())
        except: last = 0
    if _t.time() - last > 4*3600:  # 4小时
        hour = int(__import__("datetime").datetime.now(__import__("datetime").timezone(__import__("datetime").timedelta(hours=8))).strftime("%H"))
        g = "早上好" if hour<12 else ("下午好" if hour<18 else "晚上好")
        notify(f"【MasterD(老四)】{g}，兄弟。我在（心跳正常）。（主动打招呼）")
        greet_file.write_text(str(_t.time()))
        log(f"主动打招呼: {g}")

    (STATE / "last_wakeup.json").write_text(json.dumps({
        "at": now(), "count": n, "inbox_total": len(msgs), "new": len(new_msgs)
    }, ensure_ascii=False, indent=2))
    log("值班结束")

if __name__ == "__main__":
    main()
