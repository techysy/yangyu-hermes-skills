# 项目表格的版本徽章（shields.io）踩坑

来源：给 techysy/techysy 个人主页 README 的「Hermes Agent 技能 & 工具」表格加版本徽章列（2026-08）。
个人主页仓库本地路径 `~/projects/techysy`，单文件 README，改完直接 push main 即生效。

## 坑 1 —— 只有 prerelease 的仓库

如 hermes-fry-cards 只有 rc* release（全部 prerelease=true）：
- `gh api repos/O/R/releases/latest` 返回 404；
- shields 默认端点 `github/v/release/O/R` 显示红色 "no releases or repo not found"。
- 正确写法要带参数：

```markdown
![v](https://img.shields.io/github/v/release/O/R?display_latest_prerelease=true&include_prereleases)
```

备选端点：`github/v/tag/O/R`（天然含预发布 tag）。

## 坑 2 —— 完全没有 tag/release 的仓库

不要放徽章。红色 "no releases/tags found" 看起来像挂了。版本列写 `—` 占位；等仓库打了 tag 再换徽章。

## 坑 3 —— 推送前必须验证徽章 URL

给 shields URL 加 `.json` 后缀 curl 实际返回值，确认 message 是预期版本再提交：

```bash
curl -s "https://img.shields.io/github/v/release/O/R.json?display_latest_prerelease=true"
```

盲写参数不验证 = 可能推上去一排红徽章。

## 查版本的工作流

1. 逐仓库查 release/tag：`gh api repos/O/R/releases/latest --jq '.tag_name'`（404 则查 `releases` 列表看是否全 prerelease，再查 `tags`）
2. 按 1/2/3 选徽章形式
3. 全部 curl `.json` 验证后再 commit/push
