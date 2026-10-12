# GitHub → Gitee Release 镜像（Mirror GitHub releases to Gitee）

把 GitHub 的 release 及其产物（fpk / tar.gz / 等二进制附件）同步到 Gitee 镜像站的完整流程。用场景：项目有 Gitee 镜像站（如 techysy 系仓库），用户要求"产物传到 gitee" / "gitee releases 补上附件"。

## 核心认知（避免踩坑）

- **`git push gitee` 只同步代码和 tag，不会创建 Gitee Release 页面**。Gitee 的 tag 存在 ≠ Release 存在。`GET /api/v5/repos/{owner}/{repo}/releases` 返回 `[]` 就是没有 Release。
- **创建 Gitee Release + 上传附件必须用 Gitee API**，需要**私人令牌（access token）**。`POST .../releases` 必须要 `target_commitish` 参数，否则返回 `{"messages":["target_commitish is missing"]}`。
- 本机通常只有 Gitee SSH（`git@gitee.com`）认证，没有 HTTP token；创建 Release 需向用户索要私人令牌（gitee.com → 设置 → 私人令牌，权限含 projects/releases）。

## 一、同步代码 + tag 到 Gitee

```bash
cd <repo>
git fetch origin && git pull --ff-only origin main   # 先确保本地最新
git remote add gitee git@gitee.com:<user>/<repo>.git 2>/dev/null || true
git push gitee main
git push gitee --tags
```

验证三端一致：
```bash
git rev-parse HEAD origin/main gitee/main            # 三个都相同则同步完成
```

## 二、用 API 创建 Gitee Release + 上传产物

先验证 token：
```bash
curl -s "https://gitee.com/api/v5/user?access_token=$TOKEN"
# 返回 {"login":"techysy",...} 即有效
```

### 下载 GitHub 产物到本地临时目录
```bash
gh release download <tag> --dir /tmp/assets/<tag>
```

### 创建 Release（需要 target_commitish）
```bash
curl -s -X POST "https://gitee.com/api/v5/repos/$OWNER/$REPO/releases" \
  -H "Content-Type: application/json" \
  -d "$(python3 -c "import json,sys; print(json.dumps({'access_token':sys.argv[1],'tag_name':sys.argv[2],'name':sys.argv[3],'body':sys.argv[4],'target_commitish':'main','prerelease':False}))" "$TOKEN" "$TAG" "$NAME" "$BODY")"
# 返回 JSON 里有 "id"，记录它用于上传附件
```
body 可从 `gh release view <tag> --json body -q '.body'` 取。

### 上传附件（multipart，字段 file + access_token）
```bash
curl -s -X POST "https://gitee.com/api/v5/repos/$OWNER/$REPO/releases/$RELEASE_ID/attach_files" \
  -F "access_token=$TOKEN" -F "file=@/path/to/asset.fpk"
```

### 验证
```bash
curl -s "https://gitee.com/api/v5/repos/$OWNER/$REPO/releases?access_token=$TOKEN" | python3 -c "import json,sys; d=json.load(sys.stdin); [print(r['tag_name'], r['id'], [a['name'] for a in r.get('assets',[])]) for r in d]"
```
Gitee 会自动为每个 Release 追加 `zip` / `tar.gz` 源码包，所以产物数 = 上传的 + 2。

## 三、README 链接（两端自适应）

同一份 README 同时服务 GitHub + Gitee 时，**仓库内链接用根路径相对链接**，两端自动解析到各自仓库：
- Release 页：`[Releases](/releases/latest)` → GitHub 端跳 GitHub releases，Gitee 端跳 Gitee releases
- LICENSE：`[License](/blob/main/LICENSE)`
- **badge 图片**：shields.io 支持 Gitee → `https://img.shields.io/gitee/v/release/<user>/<repo>`（实测 200）。release 版本 badge 点击链接用 `/releases/latest` 相对路径。
- 上游第三方链接（如 `deepseek-ai/deepseek-harness`）保留 GitHub，不改。

## 坑
- 忘记 `target_commitish` → API 直接报错，加 `'target_commitish':'main'`。
- token 无 releases 权限 → API 返回 403/权限错误；换含 releases 权限的令牌。
- `git push gitee --tags` 后 Gitee Releases 页仍空 → 必须走 API 创建 Release，不能只依赖 push。
