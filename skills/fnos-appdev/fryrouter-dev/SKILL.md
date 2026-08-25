---
name: fryrouter-dev
version: 1.0.0
author: yangyu
license: MIT
description: "fryrouter 项目开发规范 — 数据库 schema、编码约定、架构决策、文件结构"
tags: [fryrouter, ai-routing, nextjs, sqlite, typescript]
related_skills: [hermes-agent]
triggers:
  - "fryrouter"
  - "fry-router"
  - "AI routing gateway"
  - "开发 fryrouter"
  - "添加 provider"
  - "路由引擎"
---

## When to Use

开发 fryrouter 项目时使用：添加新 provider、修改数据库 schema、实现路由引擎、编写 API endpoint、排查问题。

# fryRouter 开发规范

fryRouter 是本地 AI 路由网关，TypeScript + Next.js 15 + better-sqlite3，AES-256-GCM 加密，4 级代理作用域。

## 项目信息

- **仓库**: github.com/techysy/fry-router
- **本地路径**: ~/projects/fryrouter
- **端口**: 20129
- **数据库**: SQLite (better-sqlite3, WAL mode)
- **加密**: AES-256-GCM, `ENCRYPTION_KEY` env (64 hex chars)

## 技术栈

| 层 | 选择 |
|---|---|
| Runtime | Node.js 22+ (Next.js 15 App Router) |
| Language | TypeScript (strict) |
| Database | better-sqlite3 (WAL) |
| Encryption | Node.js crypto (AES-256-GCM) |
| Dev | tsx (直接执行 TS) |

## 目录结构

```
fryrouter/
├── src/
│   ├── app/
│   │   ├── api/v1/              # OpenAI 兼容 API
│   │   │   ├── chat/completions/route.ts
│   │   │   └── models/route.ts
│   │   └── dashboard/            # Web 管理 UI (待建)
│   ├── lib/
│   │   ├── db/
│   │   │   ├── core.ts           # DB 单例 + migration runner
│   │   │   ├── crypto.ts         # AES-256-GCM
│   │   │   ├── migrate.mts       # CLI 入口
│   │   │   ├── migrations/       # 版本化 schema
│   │   │   └── repos/            # 每实体 CRUD
│   │   │       ├── connections.ts
│   │   │       ├── apiKeys.ts
│   │   │       ├── combos.ts
│   │   │       ├── proxies.ts
│   │   │       └── settings.ts
│   │   ├── open-sse/             # 路由引擎 (待建)
│   │   │   ├── executors/        # per-provider 上游调用
│   │   │   ├── translators/      # 格式翻译
│   │   │   └── providers/        # provider 注册表
│   │   └── sse/                  # SSE 流式处理
│   └── ...
├── docs/
│   └── ARCHITECTURE.md           # 架构文档
├── .env.example
├── package.json
└── tsconfig.json
```

## 数据库 Schema (12 张表)

### 核心表

| 表 | 用途 |
|---|---|
| `provider_connections` | OAuth/API-key 上游账号，敏感字段加密 |
| `secrets` | 加密 secret 存储 |
| `api_keys` | 客户端 API key (`fr_` 前缀) |
| `models` | per-provider 模型目录 |
| `combos` | 路由组 (如 "best-reasoning") |
| `combo_targets` | combo 内有序模型引用 |
| `proxy_registry` | HTTP/HTTPS/SOCKS5 代理 |
| `proxy_scopes` | 代理 → 实体分配 (4 级作用域) |
| `settings` | 系统配置 KV |
| `usage_logs` | 每次请求遥测 |
| `quota_snapshots` | 周期性聚合用量 |
| `kv_store` | 杂项 KV (别名等) |

### 代理作用域 (优先级高 → 低)

1. **account** — 按 connection_id
2. **provider** — 按 provider_name
3. **combo** — 按 combo_id
4. **global** — 全部流量兜底

## 加密约定

- **算法**: AES-256-GCM
- **密钥**: `ENCRYPTION_KEY` env (64 hex chars = 32 bytes)
- **格式**: `iv:tag:ciphertext` (全 hex 编码)
- **IV**: 每次加密随机生成 16 bytes
- **需加密字段**: apiKey, accessToken, refreshToken, proxy 用户名/密码

## Migration 规范

```typescript
// migrations/NNN_name.mts
export function createXxxTable(db: Database.Database) {
  db.exec(`CREATE TABLE IF NOT EXISTS ...`);
}
```

```typescript
// migrate.mts
import { createXxxTable } from './migrations/NNN_name.mts';
const migrations = [
  { version: N, name: 'xxx', up: createXxxTable },
];
migrate(migrations);
```

**规则**:
- 每个 migration 只改一个事
- 版本号递增，永不修改旧 migration
- `_migrations` 表追踪已应用版本
- 幂等: 重复运行 `npm run db:migrate` 安全

## 编码约定

### Import 顺序
```typescript
// 1. Node builtin
import path from 'node:path';
// 2. 第三方
import Database from 'better-sqlite3';
// 3. 本地
import { getDb } from '../core';
import { encrypt } from '../crypto';
```

### 命名
- 文件: `kebab-case.ts` (migration 用 `NNN_name.mts`)
- 函数: `camelCase`
- 接口: `PascalCase`，不加 `I` 前缀
- 常量: `UPPER_SNAKE_CASE`

### CRUD Repo 模板
```typescript
export interface Entity {
  id: string;
  // ...
}

export function listEntities(filter?: {...}): Entity[] { ... }
export function getEntity(id: string): Entity | null { ... }
export function createEntity(data: {...}): Entity { ... }
export function updateEntity(id: string, data: Partial<Entity>): Entity | null { ... }
export function deleteEntity(id: string): boolean { ... }
```

### 路由 Handler 模板
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { validateApiKey } from '@/lib/db';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function POST(req: NextRequest) {
  const key = req.headers.get('authorization')?.replace('Bearer ', '');
  if (!key || !validateApiKey(key)) {
    return NextResponse.json(
      { error: { message: 'Invalid API key', type: 'auth_error' } },
      { status: 401 }
    );
  }
  // ...
}
```

## 请求处理流程

```
Client → /v1/chat/completions
  ├─ API key 校验
  ├─ Combo 解析 → 有序模型列表
  ├─ Account 选择 (provider_connections, priority ASC)
  ├─ 代理解析 (account → provider → combo → global)
  ├─ 格式翻译 (OpenAI ↔ provider)
  ├─ 上游 dispatch (fetch + retry + token refresh)
  ├─ SSE 流式回传
  └─ usage_logs 记录
```

## 环境变量 (.env)

```
DATA_DIR=./data
ENCRYPTION_KEY=       # openssl rand -hex 32
PORT=20129
HOSTNAME=0.0.0.0
INITIAL_PASSWORD=
OUTBOUND_PROXY_URL=
```

## 常用命令

```bash
npm install              # 安装依赖
npm run dev              # 开发服务器 (port 20129)
npm run db:migrate       # 运行 migration
npm run build            # 构建
npm run start            # 生产启动
```

## Git 规范

```
feat: 新功能
fix: 修复
refactor: 重构
docs: 文档
chore: 构建/工具
```

## 已知问题 / 待办

- [ ] `open-sse/` 路由引擎
- [ ] Dashboard 管理 UI
- [ ] Provider 格式翻译器
- [ ] 用量聚合任务
- [ ] SSE 流式处理

## 参考文档

- 架构文档: `docs/ARCHITECTURE.md`
- Next.js 15 文档: https://hermes-agent.nousresearch.com/docs (or nextjs.org)
- better-sqlite3: https://github.com/WiseLibs/better-sqlite3
