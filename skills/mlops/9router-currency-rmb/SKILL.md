---
name: 9router-currency-rmb
description: "9Router 定价显示货币补丁 — 将 Dashboard 定价从 USD ($) 改为本地货币（¥/NT$/円/₫/₩），修改 i18n locale JSON + 前端 JS。Use when 9Router pricing page shows dollars but you want local currency display."
version: 1.3.0
platforms: [linux, macos]
---

# 9Router 定价显示本地货币补丁

> 9Router Dashboard 的定价页面默认以 USD ($/1M tokens) 显示。本文档说明如何通过修改 i18n 文件 + 前端 JS 将货币显示改为本地货币。

## ⚠️ 重要：两层补丁

9Router 的货币显示涉及**两个层面**，需要分别处理：

| 层面 | 位置 | 影响范围 | 补丁方式 |
|---|---|---|---|
| **i18n 翻译** | `public/i18n/literals/<locale>.json` | Pricing 设置页面的文字描述 | 修改 locale JSON |
| **前端 JS** | `.next-cli-build/static/chunks/` | Usage 页面的 `~¥0.95` 费用显示 | 修改 JS 文件中的硬编码符号 |

**只改 i18n 不够**——Pricing 页面的文字会变，但 Usage 页面的费用数字旁的货币符号（`¥`/`$`）是 JS 硬编码的。

## 支持的语言与货币

| Locale | 语言 | 货币符号 | i18n 补丁 | JS 补丁 |
|---|---|---|---|---|
| `zh-CN` | 简体中文 | ¥ | ✅ 已有翻译，改符号 | ✅ 需改 |
| `zh-TW` | 繁體中文 | NT$ | ✅ 注入翻译 | ✅ 需改 |
| `ja` | 日本語 | ¥ | ✅ 注入翻译 | ✅ 需改 |
| `vi` | Tiếng Việt | ₫ | ✅ 注入翻译 | ✅ 需改 |
| `ko` | 한국어 | ₩ | ✅ 注入翻译 | ✅ 需改 |

## 补丁一：i18n 翻译（Pricing 设置页）

### 需要修改的 3 个 key

| 英文 key | 作用 |
|---|---|
| `dollars per million tokens` | 定价单位标签 |
| `($/1M tokens). Example: An input rate of 2.50 means $2.50 per 1,000,000 input tokens.` | 定价格式说明（完整版） |
| `($/1M tokens). Example: Input rate of 2.50 means $2.50 per 1,000,000 input tokens.` | 定价格式说明（简略版） |

### 各语言翻译内容

#### zh-CN（简体中文）

```json
"dollars per million tokens": "¥ / 百万 Token",
"($/1M tokens). Example: An input rate of 2.50 means $2.50 per 1,000,000 input tokens.": "（¥/百万 Token）。示例：输入费率 2.50 表示每 1,000,000 个输入 Token 需 ¥2.50。",
"($/1M tokens). Example: Input rate of 2.50 means $2.50 per 1,000,000 input tokens.": "（¥/百万 Token）。示例：输入费率 2.50 表示每 1,000,000 个输入 Token 需 ¥2.50。"
```

#### zh-TW（繁體中文）

```json
"dollars per million tokens": "NT$ / 百萬 Token",
"($/1M tokens). Example: An input rate of 2.50 means $2.50 per 1,000,000 input tokens.": "（NT$/百萬 Token）。範例：輸入費率 2.50 表示每 1,000,000 個輸入 Token 需 NT$2.50。",
"($/1M tokens). Example: Input rate of 2.50 means $2.50 per 1,000,000 input tokens.": "（NT$/百萬 Token）。範例：輸入費率 2.50 表示每 1,000,000 個輸入 Token 需 NT$2.50。"
```

#### ja（日本語）

```json
"dollars per million tokens": "¥ / 百万トークン",
"($/1M tokens). Example: An input rate of 2.50 means $2.50 per 1,000,000 input tokens.": "（¥/百万トークン）。例：入力レート 2.50 は 1,000,000 の入力トークンにつき ¥2.50 です。",
"($/1M tokens). Example: Input rate of 2.50 means $2.50 per 1,000,000 input tokens.": "（¥/百万トークン）。例：入力レート 2.50 は 1,000,000 の入力トークンにつき ¥2.50 です。"
```

#### vi（Tiếng Việt）

```json
"dollars per million tokens": "₫ / triệu Token",
"($/1M tokens). Example: An input rate of 2.50 means $2.50 per 1,000,000 input tokens.": "₫/triệu Token. Ví dụ: tốc độ nhập 2.50 có nghĩa là ₫2.50 cho 1,000,000 token đầu vào.",
"($/1M tokens). Example: Input rate of 2.50 means $2.50 per 1,000,000 input tokens.": "₫/triệu Token. Ví dụ: tốc độ nhập 2.50 có nghĩa là ₫2.50 cho 1,000,000 token đầu vào."
```

#### ko（한국어）

```json
"dollars per million tokens": "₩ / 백만 토큰",
"($/1M tokens). Example: An input rate of 2.50 means $2.50 per 1,000,000 input tokens.": "₩/백만 토큰. 예: 입력 비율 2.50은 1,000,000 입력 토큰당 ₩2.50을 의미합니다.",
"($/1M tokens). Example: Input rate of 2.50 means $2.50 per 1,000,000 input tokens.": "₩/백만 토큰. 예: 입력 비율 2.50은 1,000,000 입력 토큰당 ₩2.50을 의미합니다."
```

### 一键 i18n 补丁脚本

```bash
#!/bin/bash
# 9Router i18n 货币补丁（Pricing 设置页）
# 用法: bash patch-i18n.sh <locale> [locale.json 路径]
# 示例: bash patch-i18n.sh zh-TW

set -euo pipefail

LOCALE="${1:-zh-CN}"

find_i18n() {
    local locale="$1"
    local fnos="/vol4/@appdata/9router/app/server/public/i18n/literals/${locale}.json"
    [ -f "$fnos" ] && echo "$fnos" && return
    local npm_global="$(npm prefix -g 2>/dev/null)/lib/node_modules/9router/app/public/i18n/literals/${locale}.json"
    [ -f "$npm_global" ] && echo "$npm_global" && return
    local npx="$(find ~/.npm/_npx -path "*/9router/app/public/i18n/literals/${locale}.json" 2>/dev/null | head -1)"
    [ -n "$npx" ] && [ -f "$npx" ] && echo "$npx" && return
    return 1
}

VI18N="${2:-$(find_i18n "$LOCALE")}"

if [ ! -f "$VI18N" ]; then
    echo "❌ 未找到 ${LOCALE}.json"
    exit 1
fi

echo "📄 i18n: $VI18N"
cp "$VI18N" "${VI18N}.bak.$(date +%s)"

python3 -c "
import json
with open('$VI18N', 'r', encoding='utf-8') as f:
    d = json.load(f)

CURRENCY = {
    'zh-CN': ('¥ / 百万 Token', '（¥/百万 Token）。示例：输入费率 2.50 表示每 1,000,000 个输入 Token 需 ¥2.50。'),
    'zh-TW': ('NT\$ / 百萬 Token', '（NT\$/百萬 Token）。範例：輸入費率 2.50 表示每 1,000,000 個輸入 Token 需 NT\$2.50。'),
    'ja': ('¥ / 百万トークン', '（¥/百万トークン）。例：入力レート 2.50 は 1,000,000 の入力トークンにつき ¥2.50 です。'),
    'vi': ('₫ / triệu Token', '₫/triệu Token. Ví dụ: tốc độ nhập 2.50 có nghĩa là ₫2.50 cho 1,000,000 token đầu vào.'),
    'ko': ('₩ / 백만 토큰', '₩/백만 토큰. 예: 입력 비율 2.50은 1,000,000 입력 토큰당 ₩2.50을 의미합니다.'),
}

unit, desc = CURRENCY.get('$LOCALE', CURRENCY['zh-CN'])
d['dollars per million tokens'] = unit
d['(\$\/1M tokens). Example: An input rate of 2.50 means \$2.50 per 1,000,000 input tokens.'] = desc
d['(\$\/1M tokens). Example: Input rate of 2.50 means \$2.50 per 1,000,000 input tokens.'] = desc

with open('$VI18N', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
print(f'✅ i18n 补丁已应用: $LOCALE')
"

echo "   重启 9Router 生效"
```

## 补丁二：前端 JS（Usage 页面费用显示）

### 问题

Usage 页面的 `~¥0.95` 费用显示，货币符号是前端 JS 硬编码的，不受 i18n 控制。

### 定位硬编码位置

```bash
# fnOS app
JS_DIR="/vol4/@appcenter/9router/server/.next-cli-build/static/chunks"

# macOS/npm
JS_DIR="$(npm prefix -g)/lib/node_modules/9router/app/.next-cli-build/static/chunks"

# 搜索货币符号（¥ 或 $）在 usage 相关 JS 中
grep -rn "~¥\|~\$\|estCost\|formatCost" "$JS_DIR"/app/\(dashboard\)/dashboard/usage/ --include="*.js" 2>/dev/null
```

### 替换货币符号

```bash
#!/bin/bash
# 9Router JS 货币符号补丁
# 用法: bash patch-js-currency.sh <新符号> [JS 目录]

set -euo pipefail

NEW_SYMBOL="${1:-¥}"

JS_DIR="${2:-/vol4/@appcenter/9router/server/.next-cli-build/static/chunks}"

if [ ! -d "$JS_DIR" ]; then
    echo "❌ JS 目录不存在: $JS_DIR"
    exit 1
fi

echo "🔍 搜索货币符号..."
HITS=$(grep -rl "~\\\$" "$JS_DIR"/app/ --include="*.js" 2>/dev/null | head -10)

if [ -z "$HITS" ]; then
    echo "⚠️  未找到硬编码的 \$ 符号（可能已是本地货币）"
    exit 0
fi

echo "📄 找到 $(echo "$HITS" | wc -l) 个文件需要修改"

for f in $HITS; do
    cp "$f" "${f}.bak.$(date +%s)"
    sed -i "s/~\\\$/${NEW_SYMBOL}/g" "$f"
    echo "  ✅ $f"
done

echo "✅ JS 货币符号补丁已应用: \$ → ${NEW_SYMBOL}"
echo "   重启 9Router 生效"
```

### 注意事项

- **JS 补丁是 hack**：直接修改构建产物，9Router 更新会覆盖
- **符号匹配要精确**：只替换 `~$` 格式（费用显示），不要误改其他 `$` 符号
- **备份很重要**：JS 文件被改坏会导致页面白屏

## 场景一：macOS / Linux（npm 直接安装）

```bash
# 定位
VI18N="$(npm prefix -g)/lib/node_modules/9router/app/public/i18n/literals/zh-CN.json"
JS_DIR="$(npm prefix -g)/lib/node_modules/9router/app/.next-cli-build/static/chunks"

# i18n 补丁
bash patch-i18n.sh zh-CN "$VI18N"

# JS 补丁（可选，改 Usage 页面费用符号）
bash patch-js-currency.sh "¥" "$JS_DIR"

# 重启
pkill -f "9router" && npx 9router
```

## 场景二：飞牛 fnOS App

```bash
# 定位
VI18N="/vol4/@appcenter/9router/server/public/i18n/literals/zh-CN.json"
JS_DIR="/vol4/@appcenter/9router/server/.next-cli-build/static/chunks"

# i18n 补丁
bash patch-i18n.sh zh-CN "$VI18N"

# JS 补丁（可选）
bash patch-js-currency.sh "¥" "$JS_DIR"

# 重启
cd /var/apps/9Router && bash cmd/main restart
```

## 注意事项

- **数值不变**：补丁只改显示文字，不改实际费率计算（费率仍以 USD 存储/计算）
- **汇率未转换**：显示的数字仍是 USD 值（如 `¥2.50` 实际是 `$2.50`），如需真实换算需额外乘以汇率（~7.2）
- **9Router 更新会覆盖**：`npm update` 或重新安装会重置所有文件，需重新打补丁
- **JS 补丁风险较高**：修改构建产物可能导致页面异常，建议先备份
- **仅影响指定 locale**：其他语言不受影响

## 验证

1. **Pricing 设置页**：打开 Dashboard → Settings → Pricing，切换到目标语言，确认文字显示本地货币
2. **Usage 页面**：打开 Dashboard → Usage，确认费用数字旁的货币符号正确（¥/NT$/₫/₩）
3. **两个页面都要检查**——i18n 只改文字，JS 改符号
