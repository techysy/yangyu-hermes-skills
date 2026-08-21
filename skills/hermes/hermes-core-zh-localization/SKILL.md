---
name: hermes-core-zh-localization
description: "汉化 Hermes 核心系统消息（网关状态、工具进度、错误提示）为中文。hermes update 后需重新应用。"
version: 1.0.0
author: techysy
platforms: [linux]
metadata:
  hermes:
    tags: [hermes, i18n, localization, chinese, zh-cn, core, patch]
---

# Hermes 核心汉化补丁

将 Hermes 核心代码中的英文硬编码系统消息替换为中文。适用于中文用户环境。

## ⚠️ 注意事项

- **每次 `hermes update` 后需重新运行此补丁**
- 补丁只修改用户可见的状态消息，不影响核心逻辑
- 建议更新前先 `uninstall` 恢复英文，更新后重新 `install`

## 安装 / 卸载

```bash
HERMES_PYTHON=~/.hermes/hermes-agent/venv/bin/python3

# 安装（汉化）
$HERMES_PYTHON ~/.hermes/skills/hermes/hermes-core-zh-localization/patch.py install

# 卸载（恢复英文）
$HERMES_PYTHON ~/.hermes/skills/hermes/hermes-core-zh-localization/patch.py uninstall

# 重启网关生效
hermes gateway restart
```

## 汉化内容

### 网关状态消息
| 英文 | 中文 |
|---|---|
| `Gateway is restarting` | `网关正在重启中` |
| `Gateway is shutting down` | `网关正在关闭中` |
| `not accepting new work right now` | `暂时无法处理新任务` |
| `queued for the next turn` | `恢复后将在下一轮处理` |

### 运行状态
| 英文 | 中文 |
|---|---|
| `⏳ Working — N min` | `⏳ 运行中 — N 分钟` |
| `iteration X/Y` | `迭代 X/Y` |
| `receiving stream response` | `正在接收流式响应` |
| `starting/completed API call` | `开始/完成 API 调用` |
| `executing tool / completed` | `执行工具 / 工具完成` |
| `stream retry` | `流式重试` |

### 忙碌/中断消息
| 英文 | 中文 |
|---|---|
| `Steered into current run` | `已引导至当前运行` |
| `Redirected current run` | `已重定向当前运行` |
| `Subagent working` | `子代理运行中` |
| `Compressing context` | `压缩上下文` |
| `Queued for the next turn` | `已排队等待下一轮` |
| `Interrupting current task` | `中断当前任务` |
| `Agent is running` | `代理正在运行` |

### 会话错误
| 英文 | 中文 |
|---|---|
| `Session storage temporarily unavailable` | `会话存储暂时不可用` |
| `Session too large for context window` | `会话内容超出上下文窗口限制` |
| `Message interrupted before processing` | `消息在处理前被中断` |
| `Processing stopped / no response` | `处理已停止 / 未生成响应` |

### 提供商错误
| 英文 | 中文 |
|---|---|
| `Provider authentication failed` | `提供商认证失败` |
| `Model provider rejected request` | `模型提供商拒绝了请求` |
| `Model provider rate-limiting` | `模型提供商正在限流` |
| `Model server not responding` | `模型服务器未响应` |

### 其他
| 英文 | 中文 |
|---|---|
| `Hermes update finished/failed` | `Hermes 更新完成/失败` |
| `Cron job interrupted` | `定时任务被中断` |
| `Steer failed/queued/rejected` | `引导失败/已排队/被拒绝` |
| `Agent draining for maintenance` | `代理正在维护中` |
| `Context compression timed out/aborted` | `上下文压缩超时/已中止` |

## 重新安装流程

```bash
# 1. 卸载旧补丁
$HERMES_PYTHON ~/.hermes/skills/hermes/hermes-core-zh-localization/patch.py uninstall

# 2. 更新 Hermes
hermes update

# 3. 重新安装补丁
$HERMES_PYTHON ~/.hermes/skills/hermes/hermes-core-zh-localization/patch.py install

# 4. 重启网关
hermes gateway restart
```
