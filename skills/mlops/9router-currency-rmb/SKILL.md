---
name: 9router-currency-rmb
description: "9Router 定价显示货币补丁 — 将 Dashboard 定价从 USD ($) 改为 RMB (¥)，修改 i18n zh-CN.json。Use when 9Router pricing page shows dollars but you want Chinese Yuan (¥) display."
version: 1.0.0
platforms: [linux, macos]
---

# 9Router 定价显示 RMB 补丁

> 9Router Dashboard 的定价页面默认以 USD ($/1M tokens) 显示。本文档说明如何通过修改 i18n 文件将货币显示改为人民币 (¥)。

## 背景

9Router 使用 Next.js i18n 系统，定价相关的翻译在 `public/i18n/literals/zh-CN.json` 中。切换到中文 locale 后，定价页面会显示中文翻译，但货币符号仍为 `$`（美元）。

## 补丁步骤

### 1. 定位 zh-CN.json

```bash
# 9Router 数据目录（fnOS app）
VI18N="/vol4/@appdata/9router/app/server/public/i18n/literals/zh-CN.json"

# 或 standalone 部署
VI18N="<9router-root>/public/i18n/literals/zh-CN.json"
```

### 2. 修改货币相关翻译

需要修改 3 处：

| 原文（英文 key） | 原中文翻译 | 补丁后 |
|---|---|---|
| `dollars per million tokens` | `美元 / 百万 Token` | `¥ / 百万 Token` |
| `($/1M tokens). Example: An input rate of 2.50 means $2.50 per 1,000,000 input tokens.` | `（$/100 万 Token）。示例：输入费率 2.50 表示每 1,000,000 个输入 Token 需 2.50 美元。` | `（¥/百万 Token）。示例：输入费率 2.50 表示每 1,000,000 个输入 Token 需 ¥2.50。` |
| `($/1M tokens). Example: Input rate of 2.50 means $2.50 per 1,000,000 input tokens.` | `（$/100 万 Token）。示例：输入费率 2.50 表示每 1,000,000 个输入 Token 需 2.50 美元。` | `（¥/百万 Token）。示例：输入费率 2.50 表示每 1,000,000 个输入 Token 需 ¥2.50。` |

### 3. 一键替换脚本

```bash
#!/bin/bash
# 9Router RMB 货币补丁
# 用法: bash patch-rmb.sh [zh-CN.json 路径]

VI18N="${1:-/vol4/@appdata/9router/app/server/public/i18n/literals/zh-CN.json}"

if [ ! -f "$VI18N" ]; then
    echo "❌ 文件不存在: $VI18N"
    exit 1
fi

# 备份
cp "$VI18N" "${VI18N}.bak.$(date +%s)"

# 替换 3 处
sed -i 's/"美元 \/ 百万 Token"/"¥ \/ 百万 Token"/g' "$VI18N"
sed -i 's/（\$\/100 万 Token）。示例：输入费率 2.50 表示每 1,000,000 个输入 Token 需 2.50 美元。/（¥\/百万 Token）。示例：输入费率 2.50 表示每 1,000,000 个输入 Token 需 ¥2.50。/g' "$VI18N"

echo "✅ 货币补丁已应用: $VI18N"
echo "   需重启 9Router 生效"
```

### 4. 重启 9Router

```bash
# fnOS app
cd /var/apps/9Router && bash cmd/main restart

# standalone
kill $(cat .9router/server.pid) && npx 9router
```

## 注意事项

- **数值不变**：补丁只改显示文字，不改实际费率计算（费率仍以 USD 存储/计算）
- **汇率未转换**：显示的数字仍是 USD 值（如 `¥2.50` 实际是 `$2.50`），如需真实 RMB 换算需额外乘以汇率（~7.2）
- **9Router 更新会覆盖**：`npm update 9router` 或重新 `prepare-server.sh` 会重置 zh-CN.json，需重新打补丁
- **仅影响中文 locale**：英文/其他语言不受影响

## 验证

1. 打开 9Router Dashboard → Settings → Pricing
2. 右上角语言切换到中文（🇨🇳）
3. 确认定价页面显示 `¥ / 百万 Token` 而非 `$/1M tokens`
