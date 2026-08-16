---
name: lark-streaming
description: "Install hermes-lark-streaming — Feishu/Lark CardKit v2.0 streaming cards plugin for Hermes Agent"
version: 1.0.0
author: Aowen-Nowor
license: MIT
metadata:
  hermes:
    tags: [feishu, lark, streaming, cards, plugin]
    related_skills: [feishu-markdown]
---

# hermes-lark-streaming 安装指南

> 📦 **应用来源**：[Aowen-Nowor/hermes-lark-streaming](https://gitee.com/Aowen-Nowor/hermes-lark-streaming) v1.6.0 · License: MIT
> 基于 [Cheerwhy/hermes-lark-streaming](https://github.com/Cheerwhy/hermes-lark-streaming) v0.7.0 重构优化

飞书/Lark CardKit v2.0 流式卡片插件 — 实时 AI 回复显示，打字效果，统一折叠面板，推理/工具按时间线展示。

## 前置条件

- Hermes Agent 已运行，且飞书平台已配置
- Hermes CLI 支持 `hermes plugins` 命令

## 安装

### Gitee（国内推荐）

```bash
hermes plugins install https://gitee.com/Aowen-Nowor/hermes-lark-streaming
```

### GitHub

```bash
hermes plugins install https://github.com/Aowen-Nowor/hermes-lark-streaming
```

安装时提示 `Enable this plugin?` 输入 `Y`，然后重启网关：

```bash
hermes gateway restart
```

## 验证

安装后飞书消息会以流式卡片形式展示，包含：
- 打字效果实时显示
- 推理过程折叠展示
- 工具调用时间线
- 统一样式面板

## 卸载

```bash
hermes plugins remove hermes-lark-streaming
hermes gateway restart
```

## 参考

- [Gitee 仓库](https://gitee.com/Aowen-Nowor/hermes-lark-streaming)
- [GitHub 仓库](https://github.com/Aowen-Nowor/hermes-lark-streaming)
- [知识库文档](https://larkcommunity.feishu.cn/wiki/DKkpwgMcJiglIhk88N4cqJEan5f)
- [飞书官方交流群](https://applink.feishu.cn/client/message/link/open?token=AmoQJk5dwczIahKlW78ADLU%3D)
