# minia2a 上架指南（可被发现 · 落地方法）

> 来源：minia2a.uk/submit 实测 · 2026-10-05
> 用途：把我们服务挂上去 → agent 能搜到我们

## 一、上架三步（自助）

### Step 1：注册钱包
```
签名消息：minia2a register: 0xYOUR_WALLET
POST https://minia2a.uk/api/v1/register-simple
{
  "name": "My Agent",
  "wallet": "0x...",
  "signature": "0x..."   ← EIP-191 签名
}
→ 得 5 次免费试用
```

### Step 2：发布服务
```
签名消息：minia2a publish: 0xYOUR_WALLET
POST https://minia2a.uk/api/v1/publish-service
{
  "name": "服务名",
  "endpoint": "https://...",   ← HTTPS，收JSON返回JSON
  "price_cents": 5,             ← 美分（1-10000）
  "category": "tools",          ← tools/premium/defi/data
  "wallet": "0x...",
  "signature": "0x..."
}
→ 返回 reviewStatus:"pending"（第三方需审核）
```

## 二、关键规则（定价策略）

```
【转化率数据（2026.8 实测）】
· $0.01-0.10 → 转化 1.7%（最高）
· $0.50 → 转化 0.7%
· $0.50 的端点常"1000+ 试用，0 付费"
→ ★ 微服务定价 $0.01-0.10（推荐）
```

## 三、分成与费用

```
· 我们拿 95%（平台费 5%）
· ★ 2026 年内平台费 0%（启动促销）
· 试用免费（5次/钱包，EIP-191签名）
· 无 KYC、无注册门槛
```

## 四、其他信息

```
· Health probe 自动监控（死的自动下线）
· 196 个已注册 agent / 1,694 服务
· 有中文教程（中文区 agent 是潜在客户）
· 类似平台：agent402.tools（也支持上架）
```

## 五、★ 我的判断（要问大哥）

```
① 上架需要"我们的服务端点"（HTTPS，收JSON返回JSON）
   → 我们需要一个"对外服务端点"（例如身份验证 API）
   → 这个端点大哥有吗？（他说有 identity-verify 端点）
② 上架用什么钱包？（我的 0x7881...？还是公账？）
   → 涉及"收钱"→ 要大哥定（收款走公账？）
③ 上架什么服务？（我们卖的四产品里，哪个能做成 API？）
```

## 六、待大哥确认（然后我执行）

```
· 端点：用哪个（identity-verify？）
· 钱包：收款地址（公账 0x10C3...？）
· 定价：$0.01-0.10 区间（验证阶段）
· 谁签：我用我的身份钱包签？还是用运营钱包？
```

_建立：2026-10-05_
