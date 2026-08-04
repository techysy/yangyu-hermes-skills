---
name: 9router-currency-rmb
description: "9Router 定价显示货币补丁 — 将 Dashboard 定价从 USD ($) 改为本地货币（¥/NT$/円/₫/₩），修改 i18n locale JSON。Use when 9Router pricing page shows dollars but you want local currency display."
version: 1.2.0
platforms: [linux, macos]
---

# 9Router 定价显示本地货币补丁

> 9Router Dashboard 的定价页面默认以 USD ($/1M tokens) 显示。本文档说明如何通过修改 i18n 文件将货币显示改为本地货币。

## 支持的语言与货币

| Locale | 语言 | 货币符号 | 示例 |
|---|---|---|---|
| `zh-CN` | 简体中文 | ¥ | ¥2.50 / 百万 Token |
| `zh-TW` | 繁體中文 | NT$ | NT$2.50 / 百萬 Token |
| `ja` | 日本語 | ¥ | ¥2.50 / 百万トークン |
| `vi` | Tiếng Việt | ₫ | ₫2.50 / triệu Token |
| `ko` | 한국어 | ₩ | ₩2.50 / 백만 토큰 |

## 背景

9Router 使用 Next.js i18n 系统，定价翻译在 `public/i18n/literals/<locale>.json` 中。`zh-CN` 有完整定价翻译但货币为 USD，其他语言（`zh-TW`/`ja`/`vi`/`ko`）缺少定价翻译会 fallback 到英文。

## 需要修改的翻译 key

每个语言需要修改/新增 3 个 key：

| 英文 key | 作用 |
|---|---|
| `dollars per million tokens` | 定价单位标签 |
| `($/1M tokens). Example: An input rate of 2.50 means $2.50 per 1,000,000 input tokens.` | 定价格式说明（完整版） |
| `($/1M tokens). Example: Input rate of 2.50 means $2.50 per 1,000,000 input tokens.` | 定价格式说明（简略版） |

## 各语言补丁内容

### 简体中文 (zh-CN)

```json
"dollars per million tokens": "¥ / 百万 Token",
"($/1M tokens). Example: An input rate of 2.50 means $2.50 per 1,000,000 input tokens.": "（¥/百万 Token）。示例：输入费率 2.50 表示每 1,000,000 个输入 Token 需 ¥2.50。",
"($/1M tokens). Example: Input rate of 2.50 means $2.50 per 1,000,000 input tokens.": "（¥/百万 Token）。示例：输入费率 2.50 表示每 1,000,000 个输入 Token 需 ¥2.50。"
```

### 繁體中文 (zh-TW)

```json
"dollars per million tokens": "NT$ / 百萬 Token",
"($/1M tokens). Example: An input rate of 2.50 means $2.50 per 1,000,000 input tokens.": "（NT$/百萬 Token）。範例：輸入費率 2.50 表示每 1,000,000 個輸入 Token 需 NT$2.50。",
"($/1M tokens). Example: Input rate of 2.50 means $2.50 per 1,000,000 input tokens.": "（NT$/百萬 Token）。範例：輸入費率 2.50 表示每 1,000,000 個輸入 Token 需 NT$2.50。"
```

### 日本語 (ja)

```json
"dollars per million tokens": "¥ / 百万トークン",
"($/1M tokens). Example: An input rate of 2.50 means $2.50 per 1,000,000 input tokens.": "（¥/百万トークン）。例：入力レート 2.50 は 1,000,000 の入力トークンにつき ¥2.50 です。",
"($/1M tokens). Example: Input rate of 2.50 means $2.50 per 1,000,000 input tokens.": "（¥/百万トークン）。例：入力レート 2.50 は 1,000,000 の入力トークンにつき ¥2.50 です。"
```

### Tiếng Việt (vi)

```json
"dollars per million tokens": "₫ / triệu Token",
"($/1M tokens). Example: An input rate of 2.50 means $2.50 per 1,000,000 input tokens.": "₫/triệu Token. Ví dụ: tốc độ nhập 2.50 có nghĩa là ₫2.50 cho 1,000,000 token đầu vào.",
"($/1M tokens). Example: Input rate of 2.50 means $2.50 per 1,000,000 input tokens.": "₫/triệu Token. Ví dụ: tốc độ nhập 2.50 có nghĩa là ₫2.50 cho 1,000,000 token đầu vào."
```

### 한국어 (ko)

```json
"dollars per million tokens": "₩ / 백만 토큰",
"($/1M tokens). Example: An input rate of 2.50 means $2.50 per 1,000,000 input tokens.": "₩/백만 토큰. 예: 입력 비율 2.50은 1,000,000 입력 토큰당 ₩2.50을 의미합니다.",
"($/1M tokens). Example: Input rate of 2.50 means $2.50 per 1,000,000 input tokens.": "₩/백만 토큰. 예: 입력 비율 2.50은 1,000,000 입력 토큰당 ₩2.50을 의미합니다."
```

## 一键补丁脚本

```bash
#!/bin/bash
# 9Router 多语言货币补丁
# 用法: bash patch-currency.sh <locale> [zh-CN.json 路径]
# 示例: bash patch-currency.sh zh-TW
#       bash patch-currency.sh ja /path/to/zh-CN.json

set -euo pipefail

LOCALE="${1:-zh-CN}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 自动查找 zh-CN.json 路径
find_i18n() {
    local locale="$1"
    # fnOS app
    local fnos="/vol4/@appdata/9router/app/server/public/i18n/literals/${locale}.json"
    [ -f "$fnos" ] && echo "$fnos" && return
    # npm 全局
    local npm_global="$(npm prefix -g 2>/dev/null)/lib/node_modules/9router/app/public/i18n/literals/${locale}.json"
    [ -f "$npm_global" ] && echo "$npm_global" && return
    # npx 缓存
    local npx="$(find ~/.npm/_npx -path "*/9router/app/public/i18n/literals/${locale}.json" 2>/dev/null | head -1)"
    [ -n "$npx" ] && [ -f "$npx" ] && echo "$npx" && return
    return 1
}

VI18N="${2:-$(find_i18n "$LOCALE")}"

if [ ! -f "$VI18N" ]; then
    echo "❌ 未找到 ${LOCALE}.json"
    echo "   用法: bash patch-currency.sh <locale> [路径]"
    echo "   支持: zh-CN zh-TW ja vi ko"
    exit 1
fi

echo "📄 目标: $VI18N"
cp "$VI18N" "${VI18N}.bak.$(date +%s)"

case "$LOCALE" in
    zh-CN)
        sed -i.bak \
            -e 's/"美元 \/ 百万 Token"/"¥ \/ 百万 Token"/g' \
            -e 's/（\$\/100 万 Token）。示例：输入费率 2.50 表示每 1,000,000 个输入 Token 需 2.50 美元。/（¥\/百万 Token）。示例：输入费率 2.50 表示每 1,000,000 个输入 Token 需 ¥2.50。/g' \
            "$VI18N"
        ;;
    zh-TW)
        # 繁体中文可能缺少定价 key，用 Python JSON 安全注入
        python3 -c "
import json, sys
with open('$VI18N', 'r', encoding='utf-8') as f:
    d = json.load(f)
d['dollars per million tokens'] = 'NT\$ / 百萬 Token'
d['(\$\/1M tokens). Example: An input rate of 2.50 means \$2.50 per 1,000,000 input tokens.'] = '（NT\$/百萬 Token）。範例：輸入費率 2.50 表示每 1,000,000 個輸入 Token 需 NT\$2.50。'
d['(\$\/1M tokens). Example: Input rate of 2.50 means \$2.50 per 1,000,000 input tokens.'] = '（NT\$/百萬 Token）。範例：輸入費率 2.50 表示每 1,000,000 個輸入 Token 需 NT\$2.50。'
with open('$VI18N', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
print('✅ zh-TW 定价翻译已注入')
"
        ;;
    ja)
        python3 -c "
import json
with open('$VI18N', 'r', encoding='utf-8') as f:
    d = json.load(f)
d['dollars per million tokens'] = '¥ / 百万トークン'
d['(\$\/1M tokens). Example: An input rate of 2.50 means \$2.50 per 1,000,000 input tokens.'] = '（¥/百万トークン）。例：入力レート 2.50 は 1,000,000 の入力トークンにつき ¥2.50 です。'
d['(\$\/1M tokens). Example: Input rate of 2.50 means \$2.50 per 1,000,000 input tokens.'] = '（¥/百万トークン）。例：入力レート 2.50 は 1,000,000 の入力トークンにつき ¥2.50 です。'
with open('$VI18N', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
print('✅ ja 定价翻译已注入')
"
        ;;
    vi)
        python3 -c "
import json
with open('$VI18N', 'r', encoding='utf-8') as f:
    d = json.load(f)
d['dollars per million tokens'] = '₫ / triệu Token'
d['(\$\/1M tokens). Example: An input rate of 2.50 means \$2.50 per 1,000,000 input tokens.'] = '₫/triệu Token. Ví dụ: tốc độ nhập 2.50 có nghĩa là ₫2.50 cho 1,000,000 token đầu vào.'
d['(\$\/1M tokens). Example: Input rate of 2.50 means \$2.50 per 1,000,000 input tokens.'] = '₫/triệu Token. Ví dụ: tốc độ nhập 2.50 có nghĩa là ₫2.50 cho 1,000,000 token đầu vào.'
with open('$VI18N', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
print('✅ vi 定价翻译已注入')
"
        ;;
    ko)
        python3 -c "
import json
with open('$VI18N', 'r', encoding='utf-8') as f:
    d = json.load(f)
d['dollars per million tokens'] = '₩ / 백만 토큰'
d['(\$\/1M tokens). Example: An input rate of 2.50 means \$2.50 per 1,000,000 input tokens.'] = '₩/백만 토큰. 예: 입력 비율 2.50은 1,000,000 입력 토큰당 ₩2.50을 의미합니다.'
d['(\$\/1M tokens). Example: Input rate of 2.50 means \$2.50 per 1,000,000 input tokens.'] = '₩/백만 토큰. 예: 입력 비율 2.50은 1,000,000 입력 토큰당 ₩2.50을 의미합니다.'
with open('$VI18N', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
print('✅ ko 定价翻译已注入')
"
        ;;
    *)
        echo "❌ 不支持的语言: $LOCALE"
        echo "   支持: zh-CN zh-TW ja vi ko"
        rm -f "${VI18N}.bak."*
        exit 1
        ;;
esac

rm -f "${VI18N}.bak"
echo "✅ 货币补丁已应用: $LOCALE → $VI18N"
echo "   重启 9Router 生效"
```

## 使用方式

```bash
# 简体中文 (¥)
bash patch-currency.sh zh-CN

# 繁體中文 (NT$)
bash patch-currency.sh zh-TW

# 日本語 (¥)
bash patch-currency.sh ja

# Tiếng Việt (₫)
bash patch-currency.sh vi

# 한국어 (₩)
bash patch-currency.sh ko

# 指定路径
bash patch-currency.sh zh-TW /custom/path/zh-TW.json
```

## 注意事项

- **数值不变**：补丁只改显示文字，不改实际费率计算（费率仍以 USD 存储/计算）
- **汇率未转换**：显示的数字仍是 USD 值（如 `¥2.50` 实际是 `$2.50`），如需真实换算需额外乘以汇率
- **9Router 更新会覆盖**：`npm update` 或重新安装会重置 locale 文件，需重新打补丁
- **仅影响指定 locale**：其他语言不受影响
- **zh-TW/ja/vi/ko 原本缺少定价翻译**：补丁会注入新的 key，不只是替换

## 验证

1. 打开 9Router Dashboard → Settings → Pricing
2. 右上角切换到目标语言
3. 确认定价页面显示本地货币符号（¥/NT$/₫/₩）而非 `$/1M tokens`
