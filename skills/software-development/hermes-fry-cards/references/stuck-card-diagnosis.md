# 「处理中/卡住」消息的三种根因诊断

用户问「为什么这条消息还是处理中/卡住」时，**不要默认是卡片插件的问题**。飞书消息一直「处理中」有 3 个完全不同的根因，先按顺序区分，避免误修。

## 三种根因概览

| 根因 | 日志位置 | 关键信号 |
|------|----------|----------|
| ① 模型 hang（provider 无响应） | `~/.hermes/logs/gateway.log` | 入队后长时间（数分钟）**无 `response ready`** 记录 |
| ② Provider 502/429 限流 | `~/.hermes/sessions/request_dump_*.json` | `error.type=InternalServerError`，`code=502`，`[429] reason=solo_a reset after 21s` |
| ③ 卡片插件 CardKit 错误 | `~/.hermes/logs/errors.log`（**不是** gateway.log） | `hermes_fry_cards` 报 `code=300305 element exceeds the limit` 等 |

## 诊断步骤

### 1. 先看 gateway.log 是否有 response ready

```bash
grep -n "<HH:MM>" ~/.hermes/logs/gateway.log   # 该时段
```
- 收到 `inbound message` 后**没有对应 `response ready`** → 模型 hang（根因①）。
- 用户 `/stop` 后出现 `agent interrupted, session lock released` → 印证模型侧无输出。

**注意**：模型 hang 和卡片报错**会同时出现**（卡片在等模型流式输出，模型一直不吐 token，卡片停在创建/流式态）。先判定模型是否返回，再往下查卡片。

### 2. 查 request_dump 定位 provider 错误

```bash
cat ~/.hermes/sessions/request_dump_<session>_<ts>.json | python3 -c \
  "import json,sys; d=json.load(sys.stdin); e=d.get('error',{}); print(e.get('type'), e.get('message')[:300])"
```
- `InternalServerError` + `502` + `[429] reason=...` → provider 限流（根因②）。这是**上游模型服务**的问题，不是卡片或 Hermes 核心 bug。

### 3. 查 errors.log 定位卡片错误

fry-cards 的 CardKit 错误打到 `~/.hermes/logs/errors.log`，**不在** gateway.log：
```bash
grep -in "hermes_fry_cards\|cardkit\|element exceeds" ~/.hermes/logs/errors.log | tail
```

## 补充事实（2026-08-22 实测）

- `oc/x-preview-f-free` 模型对特定 prompt **静默 hang**：26 分钟无任何 token 返回，gateway 一直傻等，直到 `/stop`。这不是「思考链太长」——日志里没有 reasoning/token 增长记录，就是 provider 没吐。换模型（deepseek-v4-flash）后恢复正常。
- 300305 元素超限的**另一种形态**（区别于 card-element-overflow.md 的 reasoning 面板溢出）：
  ```
  cardkit_batch_update: code=300305 element exceeds the limit;
  seq=2107 elements=17 new=[answer_14] tool_updates=[tool_panel,tool_panel] add=[answer_14]
  ```
  单个 batch update 塞了 17 个元素、含**重复的 `tool_panel`**。这不是面板总数溢出，而是**单次 batch 请求本身元素过多/重复**——指向 `streaming/controller.py` 的 `_do_batch_update` 分批逻辑需要把重复 `tool_panel` 去重/拆分，而非 reasoning 上限问题。

## 排查顺序结论

排查「处理中」消息顺序：**gateway.log 看模型是否返回 → request_dump 看 provider 错误 → errors.log 看卡片错误**。只有模型正常返回且 provider 无错时，才值得深挖卡片插件。
