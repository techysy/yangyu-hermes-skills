# 户外出行规划

从"周末想去XX"到出完整出行方案的完整流程。适用骑行 🚴 / 徒步 🥾 / 越野跑 🏃

## 前置依赖

本 skill 需要以下第三方 skill 配合使用：

- **12306** — 查高铁票、余票、车次信息。安装：`hermes skills install 12306`
- **Open-Meteo** — 查天气（免费 API，无需 key）

> 12306 skill 由社区维护，非本仓库提供。未安装时车票查询功能不可用。

## 流程

### 1. 确认日期

先 `date` 确认当前时间，不要猜日期。

### 2. 查询目的地天气

```python
import urllib.request, json
from datetime import datetime, timedelta

w = {0:'☀️晴',1:'🌤晴间',3:'☁️多云',45:'🌫雾',
     51:'🌦毛毛雨',61:'🌦小雨',63:'🌧中雨',80:'🌦阵雨',95:'⛈雷暴'}

url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation_probability,precipitation,weathercode&timezone=Asia/Shanghai&forecast_days=7"
req = urllib.request.Request(url)
d = json.loads(urllib.request.urlopen(req, timeout=10).read())
```

优先查 **周末（周六+周日）** 的逐时数据，重点看6~18点运动窗口。

### 3. 查高铁票（需安装 12306 skill）

```bash
hermes skills install 12306
```

然后查询：

```bash
cd ~/.hermes/skills/12306
node scripts/query.mjs 成都东 松潘 -d YYYY-MM-DD -f md
node scripts/query.mjs 成都南 西昌西 -d YYYY-MM-DD -f md
```

**常用站点对照：**

| 目的地 | 出发站 | 到达站 |
|:------|:------|:------|
| 松潘站 | 成都东 | 松潘 |
| 黄龙九寨站 | 成都东 | 黄龙九寨 |
| 西昌邛海 | 成都南 | 西昌西 |
| 米易梯田 | 成都南 | 米易东 |
| 峨眉山 | 成都东 | 峨眉山 |

### 4. 查返程票

同样用12306 skill查返程，注意看晚间车次和余票情况。

### 5. 常用目的地数据

| 地点 | 海拔 | 高铁用时 | 骑行推荐 | 徒步推荐 |
|:----|:----:|:--------:|---------|---------|
| 松潘古城 | ~2850m | 成都东1h33min | 雪山梁·机场路环线80km/↑1241m | **郭学寨→跨石岩(阿岭扎嘎)**🏔 |
| 黄龙九寨站 | ~3100m | 成都东1h33min | 机场路拍红星岩 | 牟尼沟徒步 |
| 西昌邛海 | ~1500m | 成都南3h | 环邛海35km+乌龟山 | 泸山徒步 |
| 米易梯田 | ~1100m | 成都南4h | 新山梯田爬坡 | 梯田徒步 |
| 峨眉山零公里 | ~1300m | 成都东1h | 零公里→雷洞坪 | 峨眉山徒步登顶 |

### 6. 出发前提醒

🎒 **通用装备清单**
- 🧥 薄外套/风壳（高原温差大，早上~12°C）
- ☀️ 防晒霜+墨镜（高原紫外线强）
- 💧 多带水（沿途补给点少）
- 🔋 充电宝（拍照多）
- 🚴 骑行额外带：备胎+气筒+骑行裤
- 🥾 徒步额外带：登山杖+徒步鞋+头灯

🌡 **穿衣建议**
- 早上到站12°C → 运动服+薄外套
- 中午15~20°C → 可脱外套
- 傍晚返程站台10°C → 外套穿上
- 高海拔放坡/下山时体感更低，务必备风壳

### 7. 常用命令速查

```bash
# 查高铁
node ~/.hermes/skills/12306/scripts/query.mjs 成都东 松潘 -d YYYY-MM-DD -f md

# 查天气
python3 -c "import urllib.request,json;d=json.loads(urllib.request.urlopen(...))"
```

## Pitfalls

1. **日期判断** — 每次先 `date`，不要猜
2. **先装 12306 skill** — `hermes skills install 12306`，不然查不了车次
3. **返程票容易卖完** — 尤其晚上车次，查到时就要买
4. **先上车后补票可行** — 川青铁路常见操作
5. **高海拔注意** — 松潘2800m+，注意高反
6. **天气变化快** — 高原天气预报不准，出发前再看一次
