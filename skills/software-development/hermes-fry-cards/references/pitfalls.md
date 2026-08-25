# hermes-fry-cards 踩坑记录

## 2026-08-21：重写 builder.py 导致 150+ 测试失败

**现象**：测试从 4 个失败变成 152 个失败
**原因**：用 `write_file` 重写了整个 `builder.py`，破坏了原有结构和测试兼容性
**修复**：`git checkout 473dd58 -- hermes_fry_cards/cardkit/builder.py` 恢复原始文件
**教训**：**永远不要重写文件，只做 targeted patch**

## 2026-08-21：config.py 覆盖导致测试失败

**现象**：`AttributeError: 'Config' object has no attribute 'card_duration_sec'`
**原因**：重写 `config.py` 时丢失了原有属性
**修复**：恢复原始文件，只添加新属性
**教训**：配置文件也要增量修改

## 2026-08-21：导入路径错误

**现象**：`ModuleNotFoundError: No module named 'hermes_fry_cards.cardkit.streaming'`
**原因**：重写 builder.py 后，相对导入路径写错（`.streaming` → `..streaming`）
**修复**：恢复原始文件
**教训**：注意 Python 包的相对导入路径

## 2026-08-21：i18n key 不匹配

**现象**：`KeyError: 'completed'`
**原因**：`_HEADER_STATES` 中用了 `completed`，但 i18n.py 中的 key 是 `status_completed`
**修复**：改为 `status_completed`、`status_error`、`status_stopped`
**教训**：新增代码时先检查已有的常量定义

## 2026-08-21：重复函数定义

**现象**：LSP 报错 `Function declaration "_context_progress_bar" is obscured`
**原因**：用 patch 添加函数时，原函数已存在
**修复**：删除重复定义
**教训**：添加新函数前先 grep 确认是否已存在

## 2026-08-22：config.py 不接受 block/block_text 模式

**现象**：用户配置 `context_display_mode: block`，但卡片仍显示纯文本（text 模式）
**原因**：`config.py` 的 `context_display_mode` 只接受 `text/bar/text_bar` 三种，`block/block_text` 被静默忽略，回退到默认 `text`
**修复**：扩展 config.py 接受 `block` 和 `block_text`
**教训**：配置项枚举值必须与代码实现一致，新增显示模式后需同步更新 config 校验

## 2026-08-22：配置修改 vs 代码修改的重启策略

**现象**：用户修改 `config.yaml` 后以为需要重启 Hermes gateway 才能生效
**原因**：误以为所有配置变更都需要重启
**修复**：区分两种情况：
- **配置变更**（`config.yaml`）：每次请求通过 `_reload()` 读磁盘，**实时生效，无需重启**
- **代码变更**（`builder.py`/`config.py` 逻辑层）：需要 `hermes gateway restart` 重新加载 hook
**教训**：不要让用户不必要的重启网关

## 2026-08-22：show_reasoning: false 完全移除推理内容

**现象**：用户想关闭思考面板以解决移动端卡顿，设置 `show_reasoning: false` 后，即使展开面板也看不到推理内容
**原因**：`show_reasoning: false` 是不渲染推理内容到卡片（不是折叠），展开也看不到
**修复**：如果用户需要"折叠但可展开"的效果，应保持 `show_reasoning: true` + `panel_expanded: false`
**教训**：区分"不渲染"和"折叠"两种语义，用户说"关闭"时需确认是完全移除还是折叠

## 2026-08-22：进度条渐变风格偏好

**现象**：将进度条从 `█▓▒░`（渐变阴影）改为 `▪▫`（简单方块）
**原因**：认为 `█` 字符视觉吸引力过强
**修复**：用户决定恢复渐变风格（"还是 使用渐变吧"）
**教训**：进度条使用渐变阴影（`█▓▒░`）是用户偏好，不要擅自改为简单符号

## 2026-08-24：hfc (hermes-feishu-card) 插件残留导致卡片冲突/降级

**现象**：日志反复报 `[hermes-feishu-card] hook failed: ModuleNotFoundError: No module named 'hermes_feishu_card'`，卡片行为异常/降级。

**根因**：hfc 插件曾 AST patch 了 `gateway/platforms/base.py`（2 处 hook：`finalize_exact_base_no_text` + `prepare_exact_base_final_delivery`）和 `gateway/run.py`。即使 hfc 的 pip 包已卸载，**base.py 里的 patch 代码仍会触发 import**，每次飞书消息到达都报错。fry-cards 只 patch `run.py` + `cron/scheduler.py`，不覆盖 base.py——两插件 patch 位置不同，卸载 pip 包清不掉 base.py 残留。

**排查**：
```bash
grep -n 'hermes_feishu_card' ~/.hermes/hermes-agent/gateway/platforms/base.py   # 有输出 = 有残留
ls ~/.hermes/hermes-agent/.hermes_feishu_card_manifest                          # hfc manifest
ls ~/.hermes/plugins/hermes-lark-streaming/                                     # 旧 Cheerwhy 插件目录
```

**修复**：
1. 删除 base.py 中 `HERMES_FEISHU_CARD_*_PATCH_BEGIN/END` 标记之间的整块 try/except（用 patch 工具，改前备份）
2. 删 `.hermes_feishu_card_manifest`、3 个 `*.hermes_feishu_card.bak`
3. 删 `~/.hermes/plugins/hermes-lark-streaming/` 目录
4. 重启 gateway（外部终端/systemd-run 脚本法）

**教训**：装 fry-cards 前先查 hfc/旧 lark-streaming 残留；两个卡片插件绝不能同时存在。此坑已写入项目仓库 `docs/TROUBLESHOOTING.md`（commit 83cb195）。

## 2026-08-24：改默认值必须三方同步

**现象**：把 `show_reasoning` 默认值 false→true、`truncate_model_name` false→true 时，只改了 config.py。
**正确做法**：config.py fallback 值 + `tests/test_config.py` 全部相关断言（5 处）+ README 配置表 + `docs/CONFIGURATION.md` 四处一起改，否则测试挂或文档与代码不一致。
**验证方式**：stash 改动后跑失败用例，确认失败是基线遗留还是本次引入（本次 4 个失败在干净 main 上同样失败 = 存量问题）。
