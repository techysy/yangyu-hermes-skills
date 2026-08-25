# 热更新 vs 网关重启

## 区分两类配置变更

| 类型 | 配置项 | 生效方式 |
|------|--------|----------|
| **热更新**（无需重启） | `show_reasoning`、`show_tool_use`、`show_context`、`context_display_mode`、`max_reasoning_panels`、`unified_panel_min_duration`、`truncate_model_name` | 每次渲染从磁盘重读（`_reload()`），改完 config.yaml 下一条消息生效 |
| **需重启网关** | 插件代码改动、`streaming.enabled`、`header/footer/body/width_mode` 结构类配置、飞书凭据 app_id/app_secret | 运行中进程不热加载新代码，必须 `hermes gateway restart` |

## 常见错误

- 误以为 `show_reasoning` 修改需要重启网关 → 不需要，这是 display 类热更新配置
- 从 gateway 进程内部执行 `hermes gateway restart` → 会被 SIGTERM 杀掉，必须在**独立 shell** 执行

## config.py 的加载机制

- `_reload()` 方法：每次调用都从磁盘重读 → 热更新
- `_load()` 方法（带 `_raw` 缓存）：只在首次/重启时读取 → 需重启

## 网关重启的正确方式

```bash
# 在独立 shell 中执行（不能在 gateway 进程内部）
hermes gateway restart
```

系统提示：不能从 gateway 进程内部重启 gateway（会收到 "Cannot restart the gateway from within the gateway process" 错误）。
