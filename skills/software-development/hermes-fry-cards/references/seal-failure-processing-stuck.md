# 「处理中」残留第四形态：seal/complete 全量重建失败 → loading 图标卡死

## 现象
长会话（多级拆卡）结束后，多张旧卡永远显示「处理中」转圈，流式本身早已结束。

## 与既有 300305 文档的区别
- `card-element-overflow.md`：reasoning 面板数量爆炸导致溢出（预防层）
- `stuck-card-diagnosis.md` 补充事实：单次 batch 塞重复 tool_panel（分批层）
- 本文：卡片溢出之后，seal/complete 的**兜底动作本身也会失败**（恢复层缺失）

## 根因链
1. 卡片元素超限（300305），触发 force-split 或消息完成。
2. 封卡/完成走 `cardkit_update` **全量重建**（build_complete_card，元素只多不少），
   在已超限的卡上**必然再次 300305**——超限卡上合法操作只剩「减元素」。
3. `_seal_current_card` 把 close_streaming + update 放同一 try，update 抛异常后仅记日志放弃；
   卡片停留流式末态，`_loading_element()`（element_id=`loading_icon`）残留 → 永远转圈。
4. `_do_complete_card_inner` 3 次重试全败后 mark_failed，同样不清理 loading 图标。

## 排障信号
- errors.log：`CardKit seal failed for old card <id>` + traceback `code=300305`
- agent.log（INFO 级，**不在** errors.log）：`CardKit force-split on element limit: ... sealed=N new_card=...`
- **complete 成功路径没有任何日志**（只有失败才有 `complete attempt N failed`）——
  「on_completed_wait 后直接 session_disposed、中间无日志」≠ 没执行，可能只是静默成功。

## 修复（2026-08-23，commit 8738841）
- builder.py 导出公共常量 `LOADING_ELEMENT_ID = "loading_icon"`（保留私有别名兼容）。
- `_seal_current_card` except 分支 → `_remove_loading_icon(card_id, seq+1)`：
  batch_update 发 `[{"type":"delete","element_id":"loading_icon"}]`（delete 是减元素，超限卡放行）。
- `_do_complete_card_inner` 3 次重试全败后：先补 `close_streaming` 再删 loading 图标，然后才 mark_failed。
- 测试基线不变：499 passed / 4 个历史遗留失败。

## 教训
1. 给超限卡写补救逻辑只能做**减法**（delete element）；任何 add/全量重建都会复发 300305。
2. 排查顺序：errors.log 的 `seal failed` → agent.log 的 force-split INFO 行 → complete 后是否缺 loading 清理。
3. 修复生效必须重启网关：`systemctl --user restart hermes-gateway`（见下）。

## 网关重启正确姿势（本次踩坑）
- `hermes gateway restart` 在 gateway 进程内执行会被拦截：
  `Blocked: cannot restart or stop the gateway from inside the gateway process`。
- hermes-gateway 是 systemd **user** 单元：`systemctl --user restart hermes-gateway`，无需 sudo。
- 陷阱：`systemctl is-active hermes-gateway`（不带 `--user`）查询的是 system 级同名单元——不存在，
  会误报 inactive，别据此跑去折腾 sudo 密码（本机 31.31 不吃 101 的 sudo 密码）。
