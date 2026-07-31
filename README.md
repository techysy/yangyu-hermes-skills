# 🐟 yangyu-skills-hub

> 洋芋的 Hermes Agent 技能集合 🚀
> YangYu's Hermes Agent Skills Hub

[![GitHub](https://img.shields.io/badge/GitHub-yangyu--skills--hub-blue)](https://github.com/techysy/yangyu-skills-hub)
[![Skills](https://img.shields.io/badge/skills-4-green.svg)](#-技能列表)

---

## 📦 安装 / Install

```bash
hermes skills install <skill-name> --repo techysy/yangyu-skills-hub
# 无需注册，指定 --repo 即可直装 / No registration needed
```

**示例 / Examples:**
```bash
hermes skills install feishu-table-render --repo techysy/yangyu-skills-hub
hermes skills install feishu-markdown --repo techysy/yangyu-skills-hub
hermes skills install lark-streaming --repo techysy/yangyu-skills-hub
hermes skills install strava-api --repo techysy/yangyu-skills-hub
hermes skills install outdoor-trip-planner --repo techysy/yangyu-skills-hub
```

---

## 🛠️ 技能列表 / Skills

| Skill | Category | Description |
|:------|:---------|:------------|
| `feishu-table-render` | 📄 productivity | 修复飞书 Markdown 表格渲染 / Fix Feishu table rendering |
| `feishu-markdown` | 📄 productivity | 修复飞书 Markdown 渲染（表格/粗体/代码块）/ Fix Feishu markdown rendering |
| `lark-streaming` | 🔌 hermes | 飞书流式卡片插件安装指南 / Feishu streaming cards plugin install guide |
| `strava-api` | 🚴 social-media | Strava 骑行/活动查询 / Strava ride & activity query |
| `outdoor-trip-planner` | 🏔️ cycling | 户外出行规划（天气/高铁/路线）/ Outdoor trip planner |

---

## 📋 前置依赖 / Prerequisites

- `outdoor-trip-planner` 需要安装第三方 [12306 skill](https://github.com/techysy/yangyu-skills-hub) — `hermes skills install 12306`
- `strava-api` 需要配置 Strava API 凭据 / needs Strava API credentials configured

---

## 🤝 贡献 / Contribute

欢迎提交 [PR](https://github.com/techysy/yangyu-skills-hub/pulls) 或 [Issue](https://github.com/techysy/yangyu-skills-hub/issues)！
PRs and Issues are welcome!

---

## 🐛 问题排查 / Troubleshooting

日常使用 Hermes Agent 遇到的坑与解决方案：[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
Pitfalls & fixes from daily Hermes usage: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
