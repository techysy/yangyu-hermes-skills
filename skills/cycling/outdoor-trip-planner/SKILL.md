---
name: outdoor-trip-planner
description: "户外出行规划（骑行/徒步）——查天气、查高铁票、查路线、组队买票指南一站式搞定"
platforms: [linux, macos]
---

# 户外出行规划

从"周末想去XX"到出完整出行方案的完整流程。适用骑行 🚴 / 徒步 🥾 / 越野跑 🏃

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

优先查**周末（周六+周日）**的逐时数据，重点看6~18点运动窗口。

### 3. 查高铁票（12306 Skill）

使用 `12306` skill（已安装）：

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

## 常用目的地数据

| 地点 | 海拔 | 高铁用时 | 骑行推荐 | 徒步推荐 |
|:----|:----:|:--------:|---------|---------|
| 松潘古城 | ~2850m | 成都东1h33min | 雪山梁·机场路环线80km/↑1241m | **郭学寨→跨石岩(阿岭扎嘎)**🏔 |
| 黄龙九寨站 | ~3100m | 成都东1h33min | 机场路拍红星岩 | 牟尼沟徒步 |
| 西昌邛海 | ~1500m | 成都南3h | 环邛海35km+乌龟山 | 泸山徒步 |
| 米易梯田 | ~1100m | 成都南4h | 新山梯田爬坡 | 梯田徒步 |
| 峨眉山零公里 | ~1300m | 成都东1h | 零公里→雷洞坪 | 峨眉山徒步登顶 |

## 松潘经典骑行路线

**GPX路线名：** 🚉松潘系列 「松潘站→雪山梁小路→机场路环线」
- 全程51.9~80km（根据起点不同）
- 爬升1037~1241m
- 海拔2900~3418m
- 松潘古城→川主寺→雪山梁(马宣观景台拍跨石岩📸)→机场路(拍红星岩📸)→环线回古城

## 松潘徒步路线

**🥇 郭学寨→跨石岩（阿岭扎嘎）🏔**
- 郭学寨上山→跨石岩，单程~8~10km
- 海拔3100→~3800m，用时~3h
- 从松潘包车到郭学寨约20km
- 7月高山草甸开花，风景绝了
- **天气要求更高**：下雨千万别上，山顶路滑危险

**🥈 牟尼沟轻徒步**
- 松潘古城→牟尼沟峡谷→二道海
- 往返~15km，爬升不大
- 适合一日轻徒步，有栈道

**🥉 七藏沟（重装）**
- 松潘→川主寺→七藏沟
- 2~3天重装或跟向导
- 高原草甸+海子+雪山
- 7~8月满山野花 🌸

### 8. 组队买票指南

```
**成都朋友买票**
去程：12306买 C5772/C5782 成都东→松潘
返程：12306买 C5814 松潘→成都东 21:31→23:12

**德阳/中江朋友**
去程：C5773 绵竹南→松潘 08:03→09:24 ¥96
返程：C5778 松潘→绵竹南 19:32→20:37

**先上车后补票**
返程没票时，买任意能进站的票→上目标车次→找列车员补票到目的地
```

### 9. 出发前提醒

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

## 常用命令速查

```bash
# 查高铁
node ~/.hermes/skills/12306/scripts/query.mjs 成都东 松潘 -d 2026-07-25 -f md

# 查天气
python3 -c "import urllib.request,json;d=json.loads(urllib.request.urlopen(urllib.request.Request('https://api.open-meteo.com/v1/forecast?latitude=32.66&longitude=103.60&hourly=temperature_2m,precipitation_probability&timezone=Asia/Shanghai&forecast_days=7'),timeout=10).read());print(d)"

# GPX路线详情
# 存于Strava: https://www.strava.com/routes/3511761776861339760
```

## 相关参考文档

（暂无）

## Pitfalls

1. **日期判断** — 每次先 `date`，不要猜
2. **返程票容易卖完** — 尤其晚上车次，查到时就要买
3. **先上车后补票可行** — 川青铁路常见操作，买短途票刷进站→上目标车→找列车员补
4. **12306 API限流** — 多次查询会变慢，耐心等
5. **小米/DeepSeek API选择** — DeepSeek更便宜更快，主模型用deepseek即可
6. **高海拔注意** — 松潘2800m+，雪山梁3400m+，注意高反
7. **天气变化快** — 高原天气预报不准，出发前再看一次
8. **路线工具** — GPX.studio 适合精细拖拽改路，Strava 适合探路看热图，两个互补
