# Gitee Release "latest" 标记坑 + 用户偏好（只保留最新版）

> 本文件捕获一个独立的会话级坑。Gitee 镜像完整流程见同目录 `gitee-release-mirror.md`。

## 坑：Gitee 把「最后创建的 Release」当作 /releases/latest

- Gitee 的 `/releases/latest` 指向**最后创建（created_at 最新）的那个 Release**，不是语义版本最高的。
- 若按「旧版本先建、新版本后建」顺序创建多个 Release，最新版本反而**不是** latest；最老的版本（最后创建）会被误标成 latest。
- Gitee **没有显式「设为 latest」的 API**，只能靠调整创建顺序或删除旧 Release 来实现。

**复现**：镜像 deepseek-harness-fnos 时，按 v0.1.1-rc.2 → 0.1.0-rc.7 → 0.1.0-rc.6 顺序创建，0.1.0-rc.6（最老）最后创建，`/releases/latest` 错误重定向到 0.1.0-rc.6。

**验证 latest 指向**：
```bash
curl -s -o /dev/null -w "%{redirect_url}\n" "https://gitee.com/$OWNER/$REPO/releases/latest"
# 应指向最新 tag；若指向旧 tag → latest 标错了
```

## 用户偏好：产物只保留最新版，删掉旧 release

用户明确指示：「产物只需要保留最新的就行，删掉前面的不久就是最新的了」。

即镜像 Gitee 时，**只保留最新版本的一个 Release（及其产物），删除所有旧版本 Release**。latest 自然归最新版，避免「版本号反了」的困惑。

```bash
# 删除旧 release（id 从 GET .../releases 拿）
curl -s -X DELETE "https://gitee.com/api/v5/repos/$OWNER/$REPO/releases/$RELEASE_ID?access_token=$TOKEN" -w "HTTP %{http_code}\n"   # 204 = 成功
```

## 经验

- 若想保留多个版本且让最新成为 latest → 最新版本**最后创建**。
- 但用户偏好是**只留最新版** → 删旧 release 是最直接、最符合用户意图的做法。
- 改 README 链接时，仓库内链接用根路径相对链接（`/releases/latest`、`/blob/main/LICENSE`），两端自适应；badge 用 shields.io 的 `gitee/v/release/<user>/<repo>`。
