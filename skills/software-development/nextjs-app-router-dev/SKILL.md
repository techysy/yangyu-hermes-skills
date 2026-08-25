---
name: nextjs-app-router-dev
version: 1.0.0
description: "Next.js App Router 开发与排障：Edge middleware、SQLite、session 认证。"
tags: [nextjs, react, sqlite, typescript, auth]
triggers:
  - "next.js"
  - "nextjs"
  - "app router"
  - "next middleware"
  - "better-sqlite3"
---

## When to Use

开发或排障任何 Next.js（App Router）+ TypeScript + SQLite 项目时使用：middleware、API routes、session 认证、server/client 组件边界、构建报错。

## 核心约定

| 层 | 默认选择 |
|---|---|
| 路由 | App Router，route handler 加 `export const runtime = 'nodejs'` + `dynamic = 'force-dynamic'` |
| CSS | Tailwind 4 + `@theme` CSS 变量，颜色只引变量不硬编码 |
| 状态 | Zustand；图表 recharts；文案全走 i18n `t()` |

## Pitfalls（按踩坑频率排序）

1. **Middleware 是 Edge runtime**：不能 import `node:crypto`/`buffer` 等任何 Node 内置模块，build 直接报 `UnhandledSchemeError: Reading from "node:x" is not handled by plugins`。需要 HMAC/哈希时用 Web Crypto `crypto.subtle`，且签名/验签函数必须是 async。见 `references/web-crypto-session-auth.md` 的可用模板。
2. **SQLite 双引号 = 标识符**：SQL 里 `datetime("now")` 会报 `no such column: "now"`。字符串字面量一律单引号 `datetime('now')`；TS 字符串含单引号时外层用双引号包裹。
3. **管理 API 永不回显密钥**：GET 响应只返回 `hasApiKey` / `hasUsername` 这类布尔标记；PUT 时字段留空 = 保留原值。表单用 `type="password"` + `autoComplete="new-password"`。
4. **动态路由 params 是 Promise**：`{ params }: { params: Promise<{ id: string }> }`，handler 里 `const { id } = await ctx.params`。
5. **换机器拉代码先 npm install**：`Module not found: Can't resolve 'xxx'` 九成是依赖没装，不是代码问题。
6. **交接文档 ≠ 实际代码**：接手他人项目先核对 migration schema 和 repo 函数签名再动手；文档里不存在的字段（如 weight/status）以 schema 为准，缺方法就补 repo 层而不是绕路。
7. **Watchpack `EINVAL ... System Volume Information` 是 Windows 扫盘噪音**，可忽略。

## Session 认证推荐模式

- 密码登录 route 做常量时间比较后，签发 httpOnly + sameSite=lax cookie（token = base64url(payload).HMAC-SHA256）
- `src/middleware.ts` 统一守卫：dashboard 页面未登录 307 → /login；管理 API 未登录 401；公开面（如 `/api/v1/*` 业务 API 用自己的 key 鉴权）和 auth 路由本身放行
- 根路径 `/` 做 server component 读 cookie 按登录态 redirect
- 完整可运行代码：`references/web-crypto-session-auth.md`

## 验证流程

1. `npm run build` 必须通过再提交
2. dev server 起来后 curl 全链路验证：未授权应 401/307、错误密码 401、CRUD 往返、密钥不回显
3. 测试数据清理后再交付
