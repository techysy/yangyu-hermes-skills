# 🐛 yangyu-skills-hub — Hermes 使用 FAQ / FAQ

> 记录日常使用 Hermes Agent 遇到的问题和解决方案，持续更新。
> 覆盖两种部署场景：**飞牛原生 App**（hermes-core-fnos，容器化无需手动初始化）和 **虚拟机部署**（任何 VM 场景）。

---

## 1. 部署架构

### 两种部署模型

| 场景 | 说明 | 适用 |
|---|---|---|
| **飞牛原生 App** | Hermes Agent 封装为 fnOS 应用（hermes-core-fnos），自含内核 + 状态页 + Dashboard，安装即用，无需手动初始化 venv/pip | 飞牛 NAS |
| **虚拟机部署** | 任意 VM（Arch/Ubuntu 等），手动安装 Hermes Agent，配置 systemd 服务，管理 Gateway + Dashboard | 通用 VM 场景 |

### 飞牛原生 App 架构（hermes-core-fnos）

```
飞牛 fnOS
├── HermesCore App (:8642)       ← Hermes 内核 (gateway run)
├── Status Server (:8648)        ← 状态页 + 配置 + 聊天代理 (status_server.py)
└── Dashboard (:9119)            ← 原生管理界面 (可选, DASHBOARD_ENABLED=true)
```

- 配置统一管理：`gateway.env` → 启动时生成 `config.yaml`
- 状态页 UI 管理：模型供应商、API Key、Dashboard 开关、默认模型
- 每次启动自动重建 `config.yaml`，保留 `platforms` 段落（飞书/微信等）

---

## 2. 飞牛原生 App 问题（hermes-core-fnos）

### 2.1 内核安装后首次启动报 "hermes not installed"

**现象**：安装 fpk 后启动报 `ERROR: hermes kernel not installed`

**原因**：hermes-core-fnos 在 fnOS app 的 venv 中运行 Hermes Agent。首次安装后 venv 可能未创建完成（`install_init` 未完成或 `install_dep_apps` 未安装依赖）

**解决**：
```bash
# 检查 venv 是否存在
ls /vol4/@appdata/HermesCore/venv/bin/hermes

# 如不存在，手动创建并安装
python3 -m venv /vol4/@appdata/HermesCore/venv
/vol4/@appdata/HermesCore/venv/bin/pip install hermes-agent

# 重启应用
bash /var/apps/HermesCore/cmd/main restart
```

**备注**：v0.4.4+ 的 hermes-core-fnos 会在 `install_callback` 中自动创建 venv，但某些 fnOS 版本下 `install_dep_apps` 字段不被支持，需要手动安装依赖。

### 2.2 状态页打开但聊天报 "Internal server error"

**现象**：访问 :8648 状态页正常，但发消息返回 Internal server error

**排查**：
```bash
curl -sf http://127.0.0.1:8648/api/health/agent
# 检查 "alive" 字段是否为 true
```

**原因**：内核（:8642）未启动或 API_SERVER_KEY 不匹配。status_server.py 通过 127.0.0.1:8642 代理聊天请求，如果内核未运行则代理失败。

**解决**：
1. 确认内核已启动：`curl -sf http://127.0.0.1:8642/health`
2. 检查 `API_SERVER_KEY` 与内核一致（status_page 和 gateway.env 中的值）
3. 检查端口：`ss -tlnp | grep 8642`

### 2.3 每次重启后 platforms 配置丢失

**现象**：重启 HermesCore 后，飞书/微信等平台配置（`platforms` 段）从 config.yaml 中消失

**原因**：hermes-core-fnos 每次启动都会重建 `config.yaml`（根据 gateway.env 重新生成）。旧版本会覆盖整个文件。

**解决**：v0.4.4+ 的 `cmd/main` 已在启动前提取旧 config.yaml 的 `platforms` 段，写完新配置后追加回去。确保使用最新版 cmd/main。

### 2.4 Dashboard 启动后无法访问

**现象**：Dashboard (:9119) 无法访问，或报未授权

**排查**：
```bash
# 检查 Dashboard 是否在运行
ss -tlnp | grep 9119

# 检查 DASHBOARD_ENABLED 设置
grep DASHBOARD_ENABLED /vol4/@appdata/HermesCore/gateway.env
```

**原因**：Dashboard 默认关闭（`DASHBOARD_ENABLED=false`）。需要在状态页 UI 或 gateway.env 中开启。

**解决**：在状态页 (:8648) → 配置 → Dashboard，打开开关并设置用户名/密码。设置密码后 Dashboard 自动启用。

### 2.5 config.yaml 中 custom_providers 被覆盖

**现象**：手动修改了 config.yaml 的 custom_providers，重启后被重置

**原因**：cmd/main 每次启动都从 gateway.env 重新生成 config.yaml，手动修改会被覆盖。

**解决**：不要直接改 config.yaml。通过状态页 UI 管理供应商（MODEL_PROVIDERS 机制），或修改 gateway.env 后重启。

### 2.6 旧版本更新后端口占用

**现象**：更新 hermes-core-fnos 后，新版本无法启动，端口被旧进程占用

**原因**：fnOS 重装/升级不会自动杀掉旧进程。旧 cmd/main 进程可能还在运行。

**解决**：
```bash
# 找出占用端口的进程
ss -tlnp | grep 8642
ss -tlnp | grep 8648
ss -tlnp | grep 9119

# 杀掉旧进程
kill -9 $(pgrep -f 'hermes gateway run')
kill -9 $(pgrep -f 'status_server.py')
kill -9 $(pgrep -f 'hermes dashboard')

# 重启
bash /var/apps/HermesCore/cmd/main restart
```

---

## 3. 虚拟机部署问题（VM 场景）

> 适用于任何 VM（Arch/Ubuntu 等），手动安装 Hermes Agent 的场景。

### 3.1 API server 绑定 127.0.0.1 导致局域网不可达

**现象**：Dashboard 能打开，但聊天报 "Chat unavailable"

**原因**：`api_server.host` 默认 `127.0.0.1`，浏览器从局域网访问不到 API

**解决**：
```bash
# 修改 config.yaml
api_server:
  host: "0.0.0.0"

# 重启 gateway
hermes gateway restart
```

### 3.2 Gateway 进程树保护阻止重启

**现象**：`hermes gateway restart` 或 `systemctl --user restart` 被拦截

**原因**：Hermes Gateway 拦截 SIGTERM 信号传播，防止自身被意外重启

**解决**：必须从 gateway 进程树外执行（SSH 到另一台机器，或桌面终端直接执行）

### 3.3 修改 .env 后不生效

**现象**：改了 `~/.hermes/.env` 里的 API key，但行为不变

**原因**：`.env` 只在网关启动时加载一次，运行中修改不生效

**解决**：`hermes gateway restart`（从外部执行）

### 3.4 402 Insufficient account balance 但 key 明显换过

**现象**：重启后仍报 402，调试 ID 每次不同

**原因**：`.env` 和 `config.yaml` 有两份 API key。网关优先读 `.env` 的 key，只改了 config.yaml 的 key 不生效

**排查**：
```bash
grep '^XIAOMI_API_KEY=' ~/.hermes/.env | sed 's/=.*/=***/'
# 直接测 key 是否有余额（发真实 chat 请求，不是 /models）
```

**解决**：把 `.env` 的 key 同步成新 key，然后重启网关

### 3.5 "cannot restart or stop the gateway from inside the gateway process"

**现象**：在飞书/终端里执行 `hermes gateway restart` 报 Blocked

**原因**：Hermes 安全机制——从网关进程内重启会 SIGTERM 自己

**解决**：必须从网关外部的终端执行

---

## 4. 通用问题（两种部署场景）

### 4.1 Auxiliary 任务报 400 "The supported API model names are..."

**现象**：飞书话题标题生成失败，报模型名不支持

**原因**：`auxiliary.title_generation.provider: custom`（无后缀）会解析到默认 API，但模型名不匹配

**解决**：
```bash
hermes config set auxiliary.title_generation.provider auto
hermes config set auxiliary.web_extract.provider auto
hermes config set auxiliary.curator.provider auto
```

**要点**：`provider: custom` 和 `provider: custom:mimo` 是两个不同的东西——前者是"自定义默认"，后者是"名为 mimo 的自定义 provider"

### 4.2 卡片 cost 显示美元 $ 而不是人民币

**现象**：飞书卡片 footer 显示 `$0.021`

**原因**：Hermes 内核硬编码 USD 记账，无官方 currency 配置

**解决**：在 hermes-lark-streaming 插件做显示层换算（`usd_to_cny_rate` 配置，默认 7.2）

### 4.3 飞书群聊 @ 消息被拦截

**现象**：飞书群聊里 @机器人 不响应

**原因**：v0.19.0+ 的群聊 DM 策略默认拦截非配对用户

**解决**：`.env` 设置 `FEISHU_GROUP_POLICY=open`

### 4.4 飞书话题的模型切换不生效

**现象**：在飞书话题里 `/model` 切换模型，但重启网关后变回默认

**事实**：Hermes 按会话存储模型（`state.db`），重启网关**不会重置**。每个话题的 `/model` 只影响该会话，新话题用 config 默认模型

**排查**：
```bash
sqlite3 ~/.hermes/state.db "SELECT id, model FROM sessions ORDER BY started_at DESC LIMIT 5;"
```

### 4.5 模型显示 n/a 没有费用估算

**现象**：卡片 cost 显示 `n/a`

**原因**：模型不在 Hermes 内置定价表，且 provider 的 `/models` API 不返回 pricing 字段

**解决**：手动补内置表（`agent/usage_pricing.py`）。注意 `hermes update` 会覆盖此文件，升级后需重新补

### 4.6 群聊/钉钉消息格式

**偏好**：一屏内显示完，单行 20~25 字，不提冗余指标。不用 Pillow 做中文图。技术讨论简洁直接。

### 4.7 飞书表格渲染

`feishu-table-render` skill：飞书 Markdown 表格需 `post+md` 渲染，`final_response_markdown` 必须放在 `display:` 配置节下。

---

## 更新记录

- 2026-08-04：重构 FAQ — 新增飞牛原生 App (hermes-core-fnos) 场景、虚拟机部署场景、通用问题分类，更新架构说明
- 2026-07-31：初版，整理模型/API key/网关/插件/定价/话题 5 类 12 条
