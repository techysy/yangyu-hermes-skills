# 🐟 yangyu-hermes-skills

> 洋芋的 Hermes Agent 技能集合 🚀
> YangYu's Hermes Agent Skills Hub

[![GitHub](https://img.shields.io/badge/GitHub-yangyu--hermes--skills-blue)](https://github.com/techysy/yangyu-hermes-skills)
[![Skills](https://img.shields.io/badge/skills-12-green.svg)](#-技能列表)

---

## 📦 安装 / Install

```bash
hermes skills install <skill-name> --repo techysy/yangyu-hermes-skills
# 无需注册，指定 --repo 即可直装 / No registration needed
```

**示例 / Examples:**
```bash
hermes skills install feishu-table-render --repo techysy/yangyu-hermes-skills
hermes skills install feishu-markdown --repo techysy/yangyu-hermes-skills
hermes skills install lark-streaming --repo techysy/yangyu-hermes-skills
hermes skills install strava-api --repo techysy/yangyu-hermes-skills
hermes skills install outdoor-trip-planner --repo techysy/yangyu-hermes-skills
hermes skills install hermes-voice-tts --repo techysy/yangyu-hermes-skills
hermes skills install xiaomi-mimo-audio --repo techysy/yangyu-hermes-skills
hermes skills install hermes-cost-management --repo techysy/yangyu-hermes-skills
hermes skills install 9router-currency-rmb --repo techysy/yangyu-hermes-skills
hermes skills install linux-proxy --repo techysy/yangyu-hermes-skills
hermes skills install git-project-lifecycle --repo techysy/yangyu-hermes-skills
hermes skills install git-release-troubleshooting --repo techysy/yangyu-hermes-skills
hermes skills install readme-structure --repo techysy/yangyu-hermes-skills
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
| `hermes-voice-tts` | 🎙️ hermes | Hermes TTS 配置与多平台语音投递 / TTS config & multi-platform voice delivery |
| `xiaomi-mimo-audio` | 🎤 mlops | 小米 MiMo 语音 API 接入（TTS/ASR）/ Xiaomi MiMo speech API |
| `hermes-cost-management` | 💰 mlops | Hermes 成本管理（余额查询 + 模型定价）/ cost management & model pricing |
| `9router-currency-rmb` | 💰 mlops | 9Router 定价本地货币补丁（¥/NT$/円/₫/₩）/ 9Router pricing local currency patch |
| `linux-proxy` | 🔗 networking | Linux 代理配置（Clash Meta/Mihomo 含 fnOS）/ Linux proxy setup |
| `git-project-lifecycle` | 🚀 software-development | Git 项目全生命周期（提交规范/版本/变更日志/发版）/ Git project lifecycle |
| `git-release-troubleshooting` | 🚀 software-development | Git 发布/版本流程故障排查 / Git release & version troubleshooting |
| `readme-structure` | 🚀 software-development | 开源项目 README 结构规范（中英分离/按读者分层）/ README structure convention |

---

## 📋 前置依赖 / Prerequisites

- `outdoor-trip-planner` 需要安装第三方 [12306 skill](https://github.com/techysy/yangyu-hermes-skills) — `hermes skills install 12306`
- `strava-api` 需要配置 Strava API 凭据 / needs Strava API credentials configured

---

## 🖥️ Hermes 相关 fnOS 应用 / Related fnOS Apps

以下是与 Hermes Agent 生态强关联、可部署到飞牛 NAS (fnOS) 的应用，与上方 skills 配套使用：

| 应用 / App | 仓库 / Repo | 说明 / Description |
|:-----------|:------------|:-------------------|
| Hermes WebUI | [hermes-webui-fnos](https://github.com/techysy/hermes-webui-fnos) | Hermes WebUI 轻量封装 — 浏览器访问 Hermes Agent |
| 9Router | [9router-fnos](https://github.com/techysy/9router-fnos) | FREE AI 路由器 / API 代理 — 连接 Claude Code/Codex 等工具到 40+ AI 提供商 |
| MetaCubeXD | [metacubexd-fnos](https://github.com/techysy/metacubexd-fnos) | Mihomo 网络代理面板 — 管理规则、节点、连接 |
| Strava Panel | [strava-panel-fnos](https://github.com/techysy/strava-panel-fnos) | Strava 骑行数据面板 — 凭据管理 + Token 自动刷新 + SQLite 缓存 + agent API |

> 💡 Hermes Agent 本身也可作为 fnOS 应用部署，配合上面的 WebUI / 路由器使用。

---

## 🤝 贡献 / Contribute

欢迎提交 [PR](https://github.com/techysy/yangyu-hermes-skills/pulls) 或 [Issue](https://github.com/techysy/yangyu-hermes-skills/issues)！
PRs and Issues are welcome!

---

## 🐛 问题排查 / FAQ

日常使用 Hermes Agent 遇到的问题与解决方案：[HERMES-FAQ.md](./HERMES-FAQ.md)
Pitfalls & fixes from daily Hermes usage: [HERMES-FAQ.md](./HERMES-FAQ.md)
