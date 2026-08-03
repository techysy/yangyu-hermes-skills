# 定价快照 — DeepSeek V4 & Xiaomi MiMo（2026-07-31）

用户提供官方定价页截图（xiaomi）与 DeepSeek 定价页截图（OCR 验证）。CNY ÷ 7.2 = USD 存内置表。

## DeepSeek V4（官方 https://api-docs.deepseek.com/quick_start/pricing）

| 模型 | 输入(缓存命中) | 输入(未命中) | 输出 |
|---|---|---|---|
| deepseek-v4-flash | ¥0.02/M | ¥1.00/M | ¥2.00/M |
| deepseek-v4-pro | ¥0.025/M | ¥3.00/M | ¥6.00/M |

USD 折算（÷7.2）：v4-flash → 0.1389 / 0.00278 / 0.2778；v4-pro → 0.4167 / 0.00347 / 0.8333

注意：旧内置表里 v4-pro 是 $1.74/$3.48（2026-05-12 快照，已过时），v4-flash 完全没有。

## Xiaomi MiMo（官方 https://platform.xiaomimimo.com）

| 模型 | 输入(缓存命中) | 输入(未命中) | 输出 |
|---|---|---|---|
| mimo-v2.5 | ¥0.02/M | ¥1.00/M | ¥2.00/M |
| mimo-v2.5-pro | ¥0.025/M | ¥3.00/M | ¥6.00/M |

USD 折算（÷7.2）：v2.5 → 0.1389 / 0.00278 / 0.2778；v2.5-pro → 0.4167 / 0.00347 / 0.8333

## 内置表条目样板（usage_pricing.py _OFFICIAL_DOCS_PRICING）

```python
    (
        "deepseek",
        "deepseek-v4-flash",
    ): PricingEntry(
        input_cost_per_million=Decimal("1.00") / Decimal("7.2"),
        output_cost_per_million=Decimal("2.00") / Decimal("7.2"),
        cache_read_cost_per_million=Decimal("0.02") / Decimal("7.2"),
        source="official_docs_snapshot",
        source_url="https://api-docs.deepseek.com/quick_start/pricing",
        pricing_version="deepseek-pricing-2026-07-31",
    ),
```

provider key：DeepSeek = `("deepseek", ...)`；MiMo = `("xiaomi", ...)`（config.yaml `providers.xiaomi` 的 name）。

## 验证基准

- deepseek-v4-flash 1000 in + 500 out → ¥0.0020
- deepseek-v4-pro 1000 in + 500 out → ¥0.0060
- mimo-v2.5 1000 in + 500 out → ¥0.0020
- mimo-v2.5-pro 1000 in + 500 out → ¥0.0060
