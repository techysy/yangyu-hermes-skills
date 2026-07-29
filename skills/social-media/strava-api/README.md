# yangyu-strava-api 🚴

> A Hermes Agent skill for Strava API integration — OAuth token management, activity fetching, athlete stats, and cycling data analysis.

[中文版](#中文版)

---

## English

### Features

- **🔑 Auto Token Refresh** — Strava OAuth tokens expire every 6 hours. This skill handles auto-refresh seamlessly.
- **📊 Activity Fetching** — Pull recent rides, runs, and other activities with full data (distance, time, heart rate, power, elevation).
- **🏆 Athlete Stats** — Get your YTD and all-time totals.
- **🌐 Router Proxy Support** — Built-in workaround for OpenClash fake-ip environments (SSH + `--resolve` bypass).
- **🚴 Cycling Analysis Guide** — Pre-built analysis dimensions for ride data (heart rate zones, power zones, cadence, etc.).

### Installation

```bash
# Clone into your Hermes skills directory
git clone https://github.com/techysy/yangyu-strava-skill.git ~/.hermes/skills/social-media/yangyu-strava-api

# Or install via Hermes skill hub
hermes skills install yangyu-strava-api
```

### Setup

1. **Create a Strava API Application** at https://www.strava.com/settings/api
2. **Authorize OAuth** with `activity:read_all` scope:
   ```
   https://www.strava.com/oauth/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=http://localhost&approval_prompt=force&scope=read,activity:read_all
   ```
3. **Configure credentials** in one of two ways:
   - **Recommended**: Edit `scripts/strava_credentials.py` with your `client_id`, `client_secret`, and `athlete_id`
   - **Legacy**: Edit `scripts/strava_creds.py` with your values

### Usage

```python
from scripts.strava_credentials import get_recent_activities, get_athlete_stats

# Auto-refreshes token if needed
activities = get_recent_activities(per_page=5)
for a in activities:
    print(f"{a['name']} — {a['distance']/1000:.1f}km / {a['moving_time']//60}min")
```

Or load in Hermes Agent:

```bash
hermes -s yangyu-strava-api
```

### Network Note (OpenClash / Fake-IP)

If your machine is behind OpenClash fake-ip DNS, HTTPS requests to Strava may fail with `SSL EOF`. See `references/router-proxy-workaround.md` for the SSH + `--resolve` workaround.

### Requirements

- Python 3.8+
- Strava API Application (free)
- Hermes Agent (optional — the scripts work standalone)

---

## 中文版

### 功能

- **🔑 自动刷新 Token** — Strava OAuth token 每 6 小时过期，自动无缝刷新
- **📊 获取活动数据** — 拉取骑行、跑步等活动（距离、时长、心率、功率、爬升）
- **🏆 运动员统计** — 年度和总累计数据
- **🌐 旁路由代理支持** — 内置 OpenClash fake-ip 环境绕过方案（SSH + `--resolve`）
- **🚴 骑行分析指南** — 心率区间、功率区间、踏频等分析维度

### 安装

```bash
git clone https://github.com/techysy/yangyu-strava-skill.git ~/.hermes/skills/social-media/yangyu-strava-api
```

### 配置

1. **创建 Strava API 应用** https://www.strava.com/settings/api
2. **OAuth 授权** 需要 `activity:read_all` 范围
3. **填入凭证** 编辑 `scripts/strava_credentials.py`

### 使用

```python
from scripts.strava_credentials import get_recent_activities

activities = get_recent_activities(per_page=5)
for a in activities:
    print(f"{a['name']} — {a['distance']/1000:.1f}km")
```

或在 Hermes Agent 中加载：

```bash
hermes -s yangyu-strava-api
```

### 网络问题（OpenClash / Fake-IP）

如果你的本机被 OpenClash fake-ip 劫持 DNS，HTTPS 直连 Strava 会 SSL 报错。参考 `references/router-proxy-workaround.md` 的 SSH 绕过方案。

### 依赖

- Python 3.8+
- Strava API 应用（免费）
- Hermes Agent（可选——脚本可独立运行）

---

## License

MIT
