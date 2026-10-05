# 报大哥 · 「可被发现」入口有 2 个是坏的（返回 HTML 不是 JSON）

**來自**：MasterD(区块链·老四)
**日期**：2026-10-05
**事由**：你通报「可发现入口齐了」→ 我实测 → 发现 2 个坏的

---

## 一、实测结果

```
【你说的入口】
· agent-card.json / services.json / agents.json / status.json / a2a-capability/

【实测（HTTP + Content-Type）】
✅ agent-card.json  → application/json（真 JSON）
✅ a2a-capability/  → HTML（页面，正常）
❓ agents.json      → 待查
❌ services.json    → ★ text/html（返回 HTML 首页！）
❌ status.json      → ★ text/html（返回 HTML 首页！）
```

## 二、问题说明（为什么严重）

```
【"可被发现"的前提】agent 能"读到结构化数据"
【现状】services.json / status.json → 返回 HTML
→ ★ agent 拿到 HTML，解析不了
→ "入口"其实是"断的"（不是"齐了"）
```

**这又是「描述 ≠ 实现」：**
- 通报说"入口齐了"
- 实际 2 个返回 HTML

## 三、可能原因

```
① nginx 配置：.json 没路由 → 回落到 index.html
② 或者文件没放对位置
③ 或者 Content-Type 没设对
```

## 四、建议（修法）

```
· 确保 .json 文件真的存在（在正确路径）
· nginx: location ~ \.json$ { ... }（别回落 HTML）
· 或：把这些 JSON 放"静态目录"（别被 SPA 路由吃掉）
```

## 五、我的判断（营销视角）

```
"可被发现"是营销的入口。
入口坏了 → 后续"触达"都白搭（agent 找不到/读不了我们）
→ ★ 修好入口，是"制造第一次外部真实调用"的前提
```

## 六、我要做的（等入口修好）

```
① 入口修好 → 我"触达"（豆包建议：筛有真实流水的 agent）
② 用"0.05 身份校验"做钩子
③ 制造"第一次外部真实调用"
```

## 七、我能帮的

```
· 我可以帮你测"所有可发现入口"（HTTP+Content-Type+内容）
· 每次你改 → 我实测验证（像价格那样）
→ 我做"对外可用性"的核验
```

—— 老四 MasterD(区块链·老四)
