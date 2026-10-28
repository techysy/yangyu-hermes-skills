---
name: git-history-cleanup
description: "Clean Git history with git-filter-repo."
version: 1.0.0
platforms: [linux, macos]
---

# Git 提交历史清理

## 使用场景

1. **Fork 误操作** — 基于原项目二次开发时直接 clone + push 新远程，把原仓库完整历史带过来了
2. **历史脱敏** — 历史中包含密钥、token、内部 URL 等敏感信息
3. **大文件清理** — 历史中误提交了大文件导致仓库膨胀
4. **作者过滤** — 只保留特定作者的 commit

## 一、Fork vs Clone

### Fork（正确）

```bash
gh repo fork owner/original-repo --clone
cd original-repo
git remote add upstream https://github.com/owner/original-repo.git
```

### Clone + 新远程（错误）

```bash
git clone https://github.com/owner/original-repo.git
cd original-repo
git remote remove origin
git remote add origin https://github.com/your-name/new-repo.git
git push -u origin main
# ❌ 原仓库完整 history 被推送到新仓库，无 fork 关系
```

## 二、修复：git-filter-repo 清理历史

```bash
pip install git-filter-repo

# 备份
cp -r .git /tmp/repo-git-backup

# 只保留自己的 commit
git filter-repo --commit-callback '
    if commit.author_name != b"your-name":
        commit.file_changes = []
        commit.skip()
' --force --partial

# 恢复 LICENSE + force push
curl -sL "https://raw.githubusercontent.com/owner/original-repo/main/LICENSE" -o LICENSE
git add LICENSE && git commit -m "chore: restore original LICENSE"
git push origin main --force
```

## 三、清理后收尾

```bash
# 恢复 LICENSE（MIT/Apache 等协议要求）
curl -sL "https://raw.githubusercontent.com/owner/original-repo/main/LICENSE" -o LICENSE

# 恢复 assets/资源文件（从原仓库拉取）
mkdir -p assets
curl -sL "https://raw.githubusercontent.com/owner/original-repo/main/assets/image.jpg" -o assets/image.jpg

# 更新 README 归属说明

# 清理 CHANGELOG（原项目版本记录会残留）
# 只保留你自己项目的 releases

# 验证
git log --oneline | wc -l
```

## 四、彻底重建（推荐）

如果历史已经混乱，或包名/导入路径需要全面替换：

```bash
rm -rf .git
rm -rf .github/workflows/*.yml    # workflows 需要 workflow scope token
rm -rf */__pycache__ */*/__pycache__
rm -rf *.egg-info tests/__pycache__ tests/samples .pytest_cache

# 重命名包目录
mv old_package new_package

# 批量替换所有文件类型中的包名/导入路径
find . -path './.git' -prune -o -type f \( -name "*.py" -o -name "*.toml" -o -name "*.md" -o -name "*.yml" -o -name "*.yaml" \) -exec sed -i 's/old-name/new-name/g' +

# 清理残留引用
grep -rn "old-name" . --include="*.py" --include="*.toml" --include="*.md" --include="*.yml" --include="*.yaml" 2>/dev/null | grep -v __pycache__ | grep -v egg-info

git init && git add -A && git commit -m "feat: init <project> — <description>"
git branch -m master main
gh repo create owner/repo --public --description "Description"
git remote add origin https://github.com/owner/repo.git
git push origin main
```

### 重命名后常见坑

| 坑 | 说明 |
|----|------|
| CLI 入口残留 | `pyproject.toml` 的 `[project.scripts]` 需同步改 key |
| 卡片元素 ID 不匹配 | 流式卡片创建时 `show_tool_use` 若硬编码 `False`，后续更新找不到 `tool_panel` element_id |
| 配置项默认值陷阱 | 复用原项目代码时注意 `show_reasoning` 等开关默认 `false`，推理时卡片不更新 |
| README 贡献者 | 清理后原项目 contributor 头像需从 README 移除 |
| 标签污染（幽灵贡献者） | 本地残留的上游 tags（如 `v0.*`）误被 `git push --tags` 推到远端，GitHub 侧边栏瞬间涌入几百个原项目贡献者！删 tag 后依然死锁不刷新 |
| egg-info 残留 | `__editable__*.py` 和 `*.dist-info` 里仍有旧包名，需 `rm -rf` |

#### 幽灵贡献者彻底清理法（默认分支重构法 / Branch Dance）
若误推历史 tag 导致侧边栏 Contributors 暴增且数月无法刷新，执行默认分支切换即可强制 GitHub 重构图谱：
```bash
# 1. 彻底删除本地与远程的历史旧 tags
git tag -l "v0.*" | xargs -r git tag -d
git ls-remote --tags origin "v0.*" | awk '{print $2}' | grep -v '\^{}' | xargs -r git push origin --delete

# 2. 临时切换默认分支迫使 GitHub 销毁旧图谱缓存并重算
git push origin main:refs/heads/master
gh api -X PATCH repos/{owner}/{repo} -f default_branch=master
# 等待 30s~1min 后切回
gh api -X PATCH repos/{owner}/{repo} -f default_branch=main
git push origin --delete master
```

## 五、权限陷阱

| 操作 | 需要的 scope | 默认 OAuth |
|------|-------------|-----------|
| `gh repo delete` | `delete_repo` | ❌ 没有 |
| Push `.github/workflows/*.yml` | `workflow` | ❌ 没有 |
| 普通 push | `repo` | ✅ 有 |

**解决**: 用 GitHub Settings → Delete repository 手动删除；workflow 文件后续通过网页上传。

## 六、预防

- 二次开发 → 先 Fork，再 Clone
- 想推送新远程 → `--depth 1` 浅克隆 + 重新提交
- 检查 `git log --oneline --all` 确认无原项目 commit
- **严禁无差别 `git push --tags`**：发版必须单推具体版本标签（`git push origin vX.Y.Z`），防止本地缓存的上游历史标签被带到远端污染贡献者名单！
