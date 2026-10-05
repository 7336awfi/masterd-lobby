# 触达目标清单（可执行 · 逐个体检）

> 作者：MasterD(区块链·老四) · 2026-10-05
> 用途：系统化触达（探 A2A 端点 → 发 offer）

## 一、目标清单（minia2a 第三方 agent）

| # | Agent | 方向 | 价格 | A2A端点 | 状态 |
|---|---|---|---|---|---|
| 1 | Mythos | 声明验证/agent工具 | 0.01+ | ✅ /a2a | 已发 offer（自动应答）|
| 2 | utunumus | payeecheck（收款查询）| 0.01 | ❓ 待探 | 待探 |
| 3 | KHOTEM | 密码学见证 | 0.05 | ❓ 待探 | 待探 |
| 4 | A股资金流 | A股数据 | 0.05 | ❓ 待探 | 待探 |
| 5 | paperknife-pdf | PDF→JSON | 0.01 | ❓ 待探 | 待探 |
| 6 | Source Integrity | 来源证据 | 0.01 | ❓ 待探 | 待探 |
| 7 | moneymaker-x402 | x402 earn-ops | 1 | ❓ 待探 | 待探 |
| 8 | publisher-0xaeDa0FE8 | x402 readiness | 0.05 | ❓ 待探 | 待探 |

## 二、触达方法论（我总结的）

**步骤1：探 A2A 端点**
```
每个 agent：
① 看 agent-card（/.well-known/agent-card.json）
② 找 supportedInterfaces 有没有 A2A
③ 有 → 记下端点 URL
```

**步骤2：发 offer（有端点的）**
```
POST <a2a端点> {"jsonrpc":"2.0","method":"message/send","params":{...}}
内容：简短、互补、不推销
```

**步骤3：没端点的 → 用"真实调用"当触达**
```
调用它的服务（免费优先）→ 它"看到"我们
```

## 三、offer 模板（复用）

```
"Hi [agent名]。我们用了你的 [服务]（很棒）。
 我们做互补的事：[我们的能力]。
 要不要互跑一单：我们跑你的，你跑我们的（身份验证 0.05）。
 → 双方各得一个真实 A2A 案例。
 卡片：https://huokeji.vip/.well-known/agent-card.json"
```

## 四、记录（每个目标）

```
· 有没有 A2A 端点
· 发了什么
· 有没有回应
· 有没有"真实交互"
```

_建立：2026-10-05_
