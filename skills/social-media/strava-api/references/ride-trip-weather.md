# 骑行出行天气 & 距离查询

骑行计划日期的天气和路线规划查询方法。

## 7日天气预报（Open-Meteo）

免费，无需 API key。

```bash
curl -s "https://api.open-meteo.com/v1/forecast?latitude=32.66&longitude=103.60&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode,precipitation_probability_max&timezone=Asia%2FShanghai&forecast_days=7"
```

weathercode: 0=☀️晴  1=🌤晴间多云  2=🌤多云间晴  3=☁️多云  45=🌫雾  51/61=🌦雨

## 快速天气（wttr.in）

```bash
curl -s "wttr.in/Songpan?format=%C+%t+%w+%h&lang=zh"
curl -s "wttr.in/Songpan?3&lang=zh"
```

## 驾车距离（OSRM）

```bash
curl -s "https://router.project-osrm.org/route/v1/driving/104.6762,31.0083;103.6030,32.6572?overview=false"
```

## 坐标速查

松潘 32.657,103.603 | 中江 31.008,104.676 | 环球中心 30.567,104.065
