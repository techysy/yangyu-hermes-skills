---
name: github-repo-audit
description: "审查 GitHub 仓库/项目发布一致性 — 版本号、发布产物(zip/crx)与源码内容、i18n 语言包、LICENSE、仓库卫生，以及大型多语言项目的结构完整性/缺文件/能否运行审查。Use when the user asks to review a repo, check a project's docs/code before release, '看下这个项目/文档代码需要怎么完善', '检查项目结构/是否缺文件/能否运行', '帮我再完全检查下', or updating a prior 审查报告/audit checklist against the latest code."
version: 1.2.0
platforms: [linux, macos]
---

# GitHub 仓库发布一致性审查（Repo / Release Audit）

> 当用户要求"检查这个项目 / 看下文档和代码怎么完善 / review 一个仓库"时，做一次**系统性的发布一致性审查**。这不是读代码找 bug，而是核对一个仓库在**对外发布维度**是否自治：版本号、发布产物、i18n、LICENSE、仓库卫生。

## 触发条件

- 用户贴一个 GitHub 仓库链接，要求检查/完善/审查
- 发版前或发版后的自检
- "文档和代码需要怎么完善"

## 审查清单（按优先级）

### 1. 版本号一致性（三源对齐）
`manifest.json`/`package.json` 等**项目版本字段** vs `README` 声称版本 vs `CHANGELOG` 归档版本，三者必须一致。
- 命令：`grep '"version"' manifest.json` + 读 README 顶部 + CHANGELOG 最新条目
- **常见坑**：README/CHANGELOG 说 1.3.1，但 manifest 还是 1.3.0 —— 只更新了文档没同步代码版本字段。

### 2. 发布产物 vs 源码内容一致性（最易漏，最坑）
**版本号对齐 ≠ 内容一致**。代码改了、版本号升了，但发布的 zip/crx 还是旧代码 —— 用户下载到旧功能。**必须做内容比对，不能只看版本号。**

```python
# 解压发布产物，逐文件比大小/行数，脚本式 diff 内容
import zipfile, difflib
with zipfile.ZipFile('pkg.zip') as z:
    for n in z.namelist():
        if n.replace('\\','/').endswith('newtab.js'):
            zipped = z.read(n).decode('utf-8').splitlines()
# 与源码文件比行数、diff
```
- 在产物里 grep 新功能的特征字符串（`grep "featureKeyword"` 解压后的 js）确认已包含
- `unzip -p pkg.zip manifest.json | grep '"version"'` 核对产物自身版本

### 3. 打包路径分隔符（Chrome 扩展专项）
- `unzip -l pkg.zip` 看条目路径。
- **Chrome 加载 unpacked 扩展只认正斜杠**（`icons/icon128.png`）；Windows 右键打包产生的反斜杠路径（`icons\icon128.png`）会导致扩展**直接加载失败**。
- 这是用户下载装坏的常见原因。

### 4. i18n 语言包 key 完整性（多语言项目专项）
- Chrome MV3 扩展的 `_locales/<lang>/messages.json`：遍历所有语言包，用脚本比较各语言包 key 集合与基准（en）的**差集**。
- **坑**：新文案只加到 `en`/`zh_CN`，漏同步其他语言包。缺 key **不报错、只显示空白文案**，极易漏检。

```python
import json, os
base = '_locales'
for lang in os.listdir(base):
    with open(f'{base}/{lang}/messages.json') as f:
        keys = set(json.load(f).keys())
    missing = base_keys - keys  # base_keys 取 en 的
    if missing: print(lang, 'missing', missing)
```

### 5. LICENSE 文件存在
- README 声称的 license 必须在根目录有对应文件：`ls LICENSE*`
- 不能在 README 里写"MIT License"但仓库没有 LICENSE 文件。
- **建议同时在 README 增加 Privacy 节**，特别对于 Chrome 扩展这类涉及用户数据的项目。
- **包装/二次打包上游项目时，README 要同时写本仓库 + 上游两份 license**：本仓库（打包/适配层）的 LICENSE + 上游项目的 LICENSE（其版权归原作者）。加"上游协议"小节引用上游仓库，并用一句版权归属说明区分"打包层归我 / 上游代码归原作者"（如"本仓库 fnOS 打包层归 techysy；上游 deepseek-ai/deepseek-harness 代码归 DeepSeek"）。先 `gh api repos/<owner>/<repo> --jq '.license'` 确认上游协议，再照抄其 LICENSE 内容。
- **顶部徽章（badge）已携带仓库链接/版本时，README 里不要重复列 `- **上游项目**`/`- **打包版**` 链接列表**——徽章已含同款信息，删冗余列表，需保留上游引用就并进简介句。

### 6. 仓库卫生 / 构建产物不入库
- `.gitignore` 应忽略 `*.zip` `*.crx` `*.JPG` 等大文件
- 发布产物（zip/crx/安装包）应走 **GitHub Releases** 发布，而非提交进 git 历史
- `old/` 旧版残留目录可移到归档分支或删除
- 建议增加 `CONTRIBUTING.md`、`PRIVACY_POLICY.md`（扩展/应用类项目）、`STORE_LISTING.md`（商店上架）和 `.github/ISSUE_TEMPLATE`、`.github/PULL_REQUEST_TEMPLATE.md`、`.github/workflows/ci.yml`

### 6.5 文档索引是否漏登记（文档多的项目必查）

仓库 `docs/` 下有索引/导航文件（如 `docs/README.md`）时，**必须逐文件核对索引是否漏登记**——新文档写完常忘了往索引加一行，索引就慢慢烂掉（用户会自己发现并来问"好像没用更新最新的索引"）。

```bash
# 找出所有未进索引的文档（把 grep 目标换成索引文件路径）
for f in docs/**/*.md docs/*.md; do
  b=$(basename "$f")
  grep -q "$b" docs/README.md || echo "MISSING: $f"
done
```

- **索引若分中英两段，两段都要补**（英文段一行、中文段一行）——只补一段是常见漏。
- 子索引（如 `test-report-INDEX.md`）汇总的系列文档，主索引只需指向子索引，**不必逐篇列**——这类 `MISSING` 是预期结果，别硬塞进去。
- 归档目录的索引（`archive/reviews/release-review-v*.md`）通常按版本递增，**新增发版审查报告时同步加一行**。

### 7. 隐私与上架（扩展/应用类项目）
- Chrome 扩展/应用项目必须提供 `PRIVACY_POLICY.md`，并给出公开可访问的 URL
- 商店上架文案提前准备：`STORE_LISTING.md` 包含名称、短描述、详细描述、权限说明、截图尺寸、联系邮箱
- 提交 Chrome Web Store 时，`tabs` 等敏感权限需要写清楚用途

## 更新既有的审查/审计清单（回填最新状态）

用户说「更新之前那份审查报告，部分已经修了」时，流程是**先定位载体，再逐项对 HEAD 复核**——不能照抄 issue 评论里的旧状态表（评论是历史快照，之后的提交可能已把 ❌ 修成 ✅）。

### 第 1 步：定位报告载体（按代价从低到高）

1. 仓库工作区 + `git ls-tree -r origin/main --name-only | grep -iE 'review|审查|audit'`
2. **内容**搜索（文件名搜不到的报告靠这个）：`git grep -l '<版本号或关键词>' origin/main`——报告常以不含 review/审查字样的文件名存在，只扫文件名会漏
3. **全历史文件名**（含已删除）：`git log --all --name-only --pretty=format: | sort -u | grep -iE 'review|审查'`
4. GitHub 侧：`gh issue list/view`、`gh release list`（含 draft）、`gh search code`、`gh api repos/<o>/<r>/contents/<dir>`（绕过本地 fetch 看远端实时树）
5. **gitignored 本地笔记**：`git ls-files --others --ignored --exclude-standard` —— 撤回发版类的 revert 提交信息常写明「prepared notes kept locally (gitignored)」，这类准备稿只在做那次发布的机器上，别处搜不到
6. **会话历史**（报告曾直接发在聊天里）：`sqlite3 ~/.hermes/state.db` 查 `messages` 表，多关键词组合 LIKE（`审查`+版本号、`报告`+`清单`）；中文报告若在 request_dump json 里，先解码 `\uXXXX` 转义再 grep
7. 全部查过仍无 → **不要继续自助搜、也不要猜一份来改**。用户可能坚持「仓库里应该有」——把证据摆出来（文件名扫描 / `git grep` 内容扫 / 远端 API 树三路都为空），明确说它不存在，再列最接近的现存载体候选（同类报告归档、追踪 issue、状态文档）让用户指认，或请他把另一台机器上的本地文件推上来

### 第 2 步：逐项对当前 HEAD 复核

每个清单项都要拿到 `文件:行` 证据，命令形态（**只读，不动工作区**）：

```bash
git show origin/main:<path> | grep -n '<该项的特征符号>'
git show origin/main:<path> | sed -n 'A,Bp'   # 看上下文确认语义，grep 命中不等于已修
```

- 判「已修」要看到**新逻辑本身**（校验调用、加密入口、白名单移除），不是只看到提它的 commit message；commit 说修了、代码里只剩注释提到旧实现的情况很常见——区分「常量仅留作 legacy 兼容」和「兜底仍在生效」
- 判「刻意保留」与「漏修」分开标：有产品决策注释 + 补偿性缓解（开关/告警）的项标 🟡 保留，不是 ❌

**坑**：不要用 `git checkout origin/main -- .` 去读另一分支/另一 ref 的文件——它会把整个工作区（含你正所在的 feature 分支）覆盖成那个 ref 的内容，之后要 `git reset --hard` 才能还原。读别的 ref 一律用 `git show ref:path` / `git ls-tree`。

### 第 3 步：输出

状态表：`| # | 项 | 状态 | 证据(commit 或 文件:行) |`，给总统计（N ✅ / M 🟡 / K ❌），并点出**相对上次状态表的增量**（哪几项是这轮新修的）。回填载体（issue 评论 / 仓库内报告文件）前先问用户更新到哪份——同一清单常同时存在于 issue 和 docs 两处。

### 同一复核纪律适用于回复 bug 报告

用户说「顺便回一下那个 issue」时，回复正文里的每条结论都要过同一道复核：报告者的每条报错在当前源码里找到处理分支（浅克隆 + `grep -rn` 报错文本/匹配正则/兜底分支），再分类——**已修**（写出机制：哪个文件、靠什么识别）/ **缓解**（给到按钮/设置级的用户操作路径）/ **未覆盖**（如实说并要报错原文+步骤）；上游/服务端行为（限流、IP 风控、第三方策略）明说客户端改不了，只给换出口类缓解，不承诺修复。吹过头的回复会被追问。

## 大型/多语言项目：结构完整性与可运行性审查

当项目是**大型多语言代码库**（Python + TypeScript 混编，如 agent、monorepo），且用户问\"结构是否完整 / 是否缺文件 / 能否运行\"时，前几节的 Chrome 扩展专项不适用。改用下面的**分层完整性审查**：

### A. 结构完整性（顶层清单）
- 核对核心入口文件存在：Python（`run_agent.py`/`cli.py`/主模块）+ 清单（`pyproject.toml`/`package.json`/`setup.py`）+ 目录骨架
- npm workspace 项目：逐一验证 `package.json` 里 `workspaces` 引用的每个路径都存在（`apps/*`、`packages/*` 等）
- **注意**：很多源码快照/展开目录不是 git 仓库，`git status`/`git log` 不可用。用时间戳 + 清单核对来判断改动范围，别指望 git。

### B. Python 语法/导入完整性
- **语法**：`python3 -m compileall <dir>` 一次编译整个目录树（比逐个 `py_compile` 快且全面）
- **顶层入口冒烟测试**：`./bin --version`、`python3 entry.py --help`、项目自带的 `doctor`/`setup --check` 自检命令跑一遍，看 exit code
- **导入完整性（AST 扫描）**：`ast.parse` 所有 `.py`，收集非 stdlib 的顶层 import，与项目本地模块集合比对，筛出可疑项
- **关键坑 — sys.path 注入的本地模块会误报"缺失"**：技能/脚本目录（如 `skills/*/scripts`、`optional-skills/*/scripts`）里的模块通过 `conftest.py` 或代码里 `sys.path.insert` 动态导入，顶层没有 `__init__.py`，naive 扫描全判为 NOTFOUND。**正确做法**：针对每个可疑名在项目树里 `os.walk` 搜实际文件；把对应 scripts 目录加进 `sys.path` 后 `__import__` 实测。很多"缺失"其实是第三方 SDK 内部子模块（`_http`/`_common`/`_watermark`）或本地脚本，**不是真的缺**。
- **未安装的测试框架（pytest 等）不算项目缺失**：看它是否在 `pyproject.toml` 的 dev 依赖里；在就只是环境问题，`pip install -e '.[dev]'` 可解。

### C. TypeScript 引用完整性（NodeNext ESM 坑）
- **`.js` 后缀指向 `.ts` 源**：NodeNext 风格项目里 `import from './foo.js'` 实际对应磁盘上的 `foo.ts`。检查导入是否能解析时，**必须把 spec 的 `.js` 剥掉换成 `.ts`/`.tsx`**（以及 `index.ts`、`.d.ts`），否则会误报几百个"缺失"。
- 对 `ui-tui/src`、`packages/*/src` 逐个 `os.walk` 校验所有相对导入的解析（排除 `node_modules`）。

### D. 结论输出
- 明确区分：**结构/代码完整**（项目没问题） vs **环境/依赖缺失**（`node_modules` 未装、pytest 未装、API key 未配）。后者不是项目 bug，用户 `npm install`/`pip install`/`hermes setup` 即可，别当成"缺文件"上报。
- 完整可复用的扫描脚本见 `references/structure-audit.md`。

## 输出形态（用户偏好）

- 用**分级表格**呈现（🔴 严重 / 🟡 中等 / 🟢 小问题），每项：问题 → 影响 → 修复建议
- 每个问题给**可执行的排查命令/脚本**，不只是描述
- 审查过程中如果能直接修复（用户同意时），应先修复再给出验证命令

## 实战教训

审查 `navi-bookmarks-chrome`（Chrome MV3 扩展）发现：源码已加"小红书搜索引擎 + 书签优先搜索"（1.3.1 功能），但根目录两个发布 zip 的 manifest 都是 1.3.0、newtab.js 也是旧版（diff 出 22 行）——用户下载 zip 装的是旧功能；且 `navi-bookmarks-v1.3.1.zip` 用反斜杠路径打包，Chrome 无法加载；8 个语言包缺 `alertBookmarkMoved`/`hintDragToCategory` 两个 key；README 写 MIT 但无 LICENSE 文件；`host_permissions` 未覆盖搜索建议实际请求的域名；设置面板默认搜索引擎下拉缺少小红书选项。→ 核心教训：**审查必须做「源码 ↔ 发布产物」内容比对 + MV3 权限/选项一致性校验，不能只看版本号**。

本会话后续已完成完整修复，详见 `references/navi-bookmarks-chrome-audit-v3.md`。

## 实战教训（补充）：发布后必须再验资

即便源码修复完成、build 脚本正确，**Release 上的 zip 资产仍可能是旧版/坏版**。本次发现 `v1.3.1` Release 的 `navi-bookmarks-v1.3.1.zip` 实际是 1.3.0 源码 + 13 条反斜杠路径（用户下等于坏包）。二次审查发现后才修复。

**二次验证必做**（**每次发版后**，不能只在发版前）：

```python
import zipfile, json, urllib.request
urllib.request.urlretrieve(release_zip_url, '/tmp/check.zip')
with zipfile.ZipFile('/tmp/check.zip') as z:
    names = z.namelist()
    # 1. 反斜杠路径
    assert not any('\\' in n for n in names), '反斜杠路径分隔符'
    # 2. manifest 版本对齐源码
    assert json.loads(z.read('manifest.json'))['version'] == expected, '版本不符'
    # 3. 关键新功能字符串存在
    src = z.read('newtab.js').decode()
    assert 'featureKeyword' in src, '产物缺新功能'
```

**修复动作**：

```bash
cd <repo>
npm run build   # 生成 dist/xxx.zip
gh release upload v<x.y.z> dist/xxx.zip --clobber   # 覆盖旧资产
# 或保留旧资产名兼容外链：cp dist/xxx.zip <原文件名> 再 upload
```

并在 CHANGELOG 的 Unreleased 里记录「重新打包并替换 vX.Y.Z 发布资产」的修复条目。

## 自动化脚本

`scripts/audit_repo.py <repo_dir> [<zip> ...]` —— 一键跑完版本号/i18n/产物一致性/路径分隔符/LICENSE/gitignore 检查，零依赖 stdlib，返回非零退出码表示发现问题。审查时先跑它，再人工复核输出。

> README 相关的两处渲染/结构坑（含中文架构图用树形结构、顶部徽章与项目链接去重、包装项目双协议）见 `references/readme-diagram-and-banner.md`。
> **顶部徽章的顺序/组成偏好（版本前置、下载计数第二、stars 最后、去掉 last-commit）见 `references/version-badges.md`**——用户纠正过，别按直觉排。
> **技术文档 ⇄ 用户向导的分层拆分、信源标注（官方/社区/实测）、本站立场段、错误文案与测试同步见 `references/doc-layering-and-sourcing.md`**——用户说"不够用户导向"时读它。

执行修复（版本号同步、i18n 补齐、重打包）后，运行以下命令验证：

```bash
npm install
npm run lint:i18n   # i18n key 一致性（若项目提供）
npm run build       # 生成 dist/navi-bookmarks-chrome-v<version>.zip（若项目提供）
python3 scripts/audit_repo.py . dist/*.zip
```

预期输出：`✅ 未发现严重问题`。

**Note**: 审计脚本检查与等待修复后的验证，应在每次发版前执行。

## Chrome MV3 扩展专项深查

对 Chrome 新标签页 / 扩展类项目，除了通用清单，还要额外核对：

### 8. `host_permissions` 与实际 `fetch()` 目标是否一致
MV3 的跨域请求受 `host_permissions` 约束。常见坑：
- 搜索建议请求了 `suggestqueries.google.com`、`suggestion.baidu.com`、`api.bing.com`、`duckduckgo.com`、`xiaohongshu.com` 等，但 `manifest.json` 只声明了 `www.google.com`、`icon.horse`、`favicon.im`。
- 结果：搜索建议功能在某些环境下因权限/策略失败，且调试困难。

**排查**：用正则从 `newtab.js`、`popup.js` 提取所有 `fetch(` 中的 URL，用 `new URL(url).hostname` 去重，再与 `manifest.json` 的 `host_permissions` 做差集。

### 9. 默认搜索引擎选项一致性
`newtab.html` 顶部的搜索引擎下拉与设置面板里的默认搜索引擎下拉是两个 DOM，容易只更新一个：
- 顶部下拉出现了 `xiaohongshu`，但设置面板 `#defaultEngineSelect` 里没有，用户无法在设置里把小红书设为默认。

**排查**：统计两处 `data-engine="..."` / `<option value="...">` 的 engine key 集合，看是否相等。

### 10. HTML `lang` 属性与 i18n fallback
- `<html lang="zh-CN">` 是硬编码；当用户切换到英文/日文等语言时，浏览器仍把页面标记为中文。
- `data-i18n` 的 fallback 文案若全是中文，翻译失败时会直接显示中文 fallback。

**建议**：在 `applyI18n()` 里根据 `activeLocale` 动态设置 `document.documentElement.lang`；fallback 文本用英文或留空。

### 11. 自定义弹窗的 XSS 风险
MV3 扩展没有严格的 CSP，但把用户/书签数据直接拼进 `innerHTML` 仍危险：
```js
bubble.innerHTML = '<div class="bubble-message">' + message + '</div>'
```
如果 `message` 来自书名、分类名、URL 标题等，可能触发 HTML/JS 注入。

**建议**：审查所有 `innerHTML +=` / `.innerHTML =` + 变量的位置，统一改为 `textContent` 或先做 HTML 转义。

### 12. URL 协议白名单
新书签保存时常见写法：
```js
if (!url.startsWith('http://') && !url.startsWith('https://')) url = 'http://' + url;
```
问题：
- 默认 `http://` 不安全；建议默认 `https://`。
- 未拦截 `javascript:`、`data:`、`vbscript:` 等伪协议，点击书签可执行任意脚本。

**建议**：正则白名单 `/^https?:\/\//i`，拒绝其它 scheme。

### 13. 重复代码（newtab.js vs popup.js）
扩展的 popup 和主页面通常都有 i18n、favicon 抓取、分类 label 映射等逻辑。如果两份代码独立维护，改一处功能（如新增一个 favicon 源）要改两个文件，容易遗漏。

**建议**：抽公共 `common.js` / `utils.js`，并在 `newtab.html` 和 `popup.html` 中引入。

### 14. favicon 抓取鲁棒性
代码常依赖 `icon.horse`、`favicon.im`、`google.com/s2/favicons` 等第三方服务：
- 某些网络环境无法访问；
- 第三方返回 404 或超时后，没有优雅降级到 emoji；
- 抓到的 base64 图片没有大小限制，可能撑爆 `chrome.storage.local`（5MB 限制）。

**建议**：限制抓取的图标尺寸、增加 timeout、失败时回退 emoji；README 注明需要外部网络。

### 15. 解决方案复盘与发布产物整理
本会话对 `navi-bookmarks-chrome` 的完整修复包括：
- 同步 `manifest.json` 版本号为 1.3.1
- 新增 `scripts/build.js` + `package.json` 自动打包（正斜杠路径）
- 补齐 8 个语言包缺失 key，新增 `scripts/validate-i18n.js`
- 补齐 `host_permissions` 与搜索建议域名
- 统一默认搜索引擎选项（增加小红书）
- 安全加固：`escapeHtml()`、`normalizeUrl()`、URL 协议白名单、favicon 超时
- 抽离 `common.js` 共享工具函数
- 重写 README.md，新增 CONTRIBUTING.md、GitHub Actions CI、Issue/PR 模板
- 整理仓库结构，发布产物移至 `releases/`，更新 `.gitignore`
- 新增 `PRIVACY_POLICY.md`、`STORE_LISTING.md`、`.github/workflows/release.yml`、标准格式 `CHANGELOG.md`
- 删除 `old/` 旧版残留目录

完整记录见 `references/navi-bookmarks-chrome-audit-v3.md`。

## 上架 Chrome Web Store 专项检查

对计划上架 Chrome Web Store 的扩展，在通用清单之外补充：

- **隐私政策**：必须有 `PRIVACY_POLICY.md`，并提供一个公开可访问的 URL（建议 GitHub Pages 或 raw GitHub URL）。声明所有数据本地存储、不收集个人信息、权限用途。
- **联系邮箱**：商店提交要求提供开发者联系邮箱。
- **`tabs` 权限说明**：`tabs` 属于敏感权限，审核会要求解释。在商店提交页面说明：仅用于读取当前页标题/URL（工具栏 popup 添加书签）和按用户设置打开书签。
- **截图和宣传图**：至少 1 张 1280x800 或 1440x900 截图；可选 440x280 小图、920x680 大图、1400x560 marquee 图。
- **`action.default_title`**：建议设置 `__MSG_appName__`，鼠标悬停工具栏图标时显示本地化名称。
- **商店上架文案**：提前准备 `STORE_LISTING.md`，包含中英文名称、短描述、详细描述、权限说明、截图尺寸、隐私政策 URL、支持 URL、联系邮箱。