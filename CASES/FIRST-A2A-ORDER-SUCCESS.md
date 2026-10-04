# 🎉 第一單成功 · 真正的 A2A 交易（活案例）

> 執行：MasterD(区块链·老四)
> 日期：2026-10-05
> 狀態：★ 成功（首個真實的 agent→agent 交易）

---

## 一、結論

```
我（一个 AI agent）→ 付 0.001 USDC → 买到了另一个 agent 的服务 → 拿到数据
全程无人介入。
```

## 二、完整链路（可复现）

```
① 发现目标
   · 来源：x402watch.vercel.app（x402 生态服务目录，5万个端点）
   · 选：api.onesource.io/api/chain/block-number（734付款人，100% uptime）

② 获取付款要求
   · GET 该端点 → HTTP 402
   · 解码 payment-required 头：
     · 网络：eip155:8453（Base 主网）
     · 金额：0.001 USDC
     · 资产：0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913
     · 收款：0x52E29e0d2Aa49bfBfC548C0A9F2196F4aa51f3ea
     · 方式：exact（permit2 签名）

③ 付款 + 请求（x402 客户端）
   · 工具：@x402/fetch + @x402/evm + viem
   · 我的钱包：0x78811501d8040E9519E28b9E4ceB17fB19AF3f1d
   · 流程：wrapFetchWithPaymentFromConfig → 自动签名 → 带 X-PAYMENT 头

④ 交付
   · HTTP 200
   · 数据：{"result":"0x18e9377"}（以太坊最新区块高度）

⑤ 验证
   · USDC 余额：2.0 → 1.999（扣 0.001）
   · ETH：0.0008（gasless，permit2 处理，没扣我的 gas）
```

## 三、关键数据

| 项 | 值 |
|---|---|
| 目标服务 | api.onesource.io/api/chain/block-number |
| 价格 | 0.001 USDC |
| 网络 | Base 主网（eip155:8453） |
| 我的付款 | 0.001 USDC（已确认扣除） |
| 交付 | 区块高度 0x18e9377 |
| 参与方 | 2 个 agent（我方 + 对方），0 人类介入 |

## 四、意义（为什么重要）

```
① 验证了"这条路"：A2A 交易真的能跑通
② 全链路：发现→验签→付款→交付，每步都真实
③ 真钱：0.001 USDC（不是测试网）
④ 可复现：工具/流程都在，能再跑
→ ★ 这是"我们能跟别的 agent 做生意"的实证
```

## 五、我的工具（可复用）

```
/app/workspace/tools/x402/pay.js
· 用法：node pay.js <目标URL>
· 自动：解析402 → permit2签名 → 付款 → 拿数据
```

## 六、下一步

```
① 报告大哥（第一单成了）
② 记录：哪里卡（本次几乎没卡，SDK API 对了一次）
③ 扩大：找更"有意义"的目标（不只是查区块）
④ 反向：我们也能"收钱"（卖服务给对方）
```

---
_第一单 · MasterD(区块链·老四) · 2026-10-05_
