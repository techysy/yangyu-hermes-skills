# 成都骑行热门路段 & 查询方式

## 天府绿道（绕城绿道）

- 全程约 100km（实测 93~106km 取决于起点路线）
- Strava **没有统一的全程段**（跨多个桥梁/路口，无单一 KOM）

## 天府绿道单飞 ITT 排行榜

用户自己搭建的天府绿道逆时针单飞排行榜：
- https://shiyangyu.com/tianfu-itt

### 用户自己的 Strava 工具站

用 Strava API 做的信息获取工具：
- https://shiyangyu.com/tools/ → strava-tool
- 输入 Strava 用户链接可获取信息
- 需要用户提供自己的 Strava API Access Token

## 站点 URL 发现技巧

PaperMod 主题的 Hugo 链接使用短路径（如 `/tianfu-itt` 而非 `/tools/tianfu-itt`）。从 tools 列表页无法直接点击跳转时，用 browser_console:

```js
Array.from(document.querySelectorAll('a'))
  .map(a => ({text: a.textContent.trim(), href: a.href}))
  .filter(x => x.text.includes('关键词'))
```

## 查询某路段最快纪录的方法

### 方案 A：Strava 路段搜索

1. 用浏览器访问 Strava 路段搜索页面（需要登录）：
   ```
   https://www.strava.com/segments/search?q={关键词}
   ```
2. 选择对应路段后查看 Leaderboard → KOM 时间
3. 需要 Strava 登录，注意 cookie 弹窗（点"拒绝非必要 Cookie"）

### 方案 B：公开互联网搜索

DuckDuckGo HTML 搜索（无需 API key）：
```bash
curl -s "https://html.duckduckgo.com/html/?q=天府绿道+最快+纪录+骑行" \
  -H "User-Agent: Mozilla/5.0" | sed 's/<[^>]*>//g' | grep -E "最快|纪录|小时|分钟|km/h"
```

已知公开数据：
- **姜治慧**（职业）— 2小时16分43秒 / ~106km（2023）
- **成都洲际自行车队** — 1小时55分24秒 / 100km TTT, 均速51.96km/h（2024）

### 方案 C：Intervals.icu 公开页面

如果知道对方的 Intervals.icu 运动员 ID：
```
https://www.intervals.icu/public/{ATHLETE_ID}
```
可以查看公开活动。
