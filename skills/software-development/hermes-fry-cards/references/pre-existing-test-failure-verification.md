# 确认「基线测试失败」的标准手法

当改动后跑测试出现失败，判断失败是否由本次改动引入时，**不要凭「看起来相关」臆断**。

## 手法

```bash
cd <repo>
git stash          # 暂存你的改动，回到 HEAD
# 跑同一组失败测试
pytest <failed_tests> -q
git stash pop      # 恢复改动
```

若 **stash 前后失败集合一致**，则这些是基线失败，与本次改动无关。

## 本项目基线失败（4 个，非本次引入）

- `test_multiple_tool_segments_merged_into_single_bottom_panel`
- `test_footer_present_by_default`
- `test_split_flushes_pending_actions_then_moves_to_next_card`
- `test_batch_update_recovers_stale_segment_on_missing_element`

> 注意：`git stash` 默认只暂存已跟踪文件的改动；stash 前先 `git add -A`（或用 `git stash -u` 含未跟踪文件）确保完整暂存。stash 后 `git stash pop` 恢复。
