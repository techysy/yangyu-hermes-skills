---
name: nextjs-sqlite-backend
description: Use when building Next.js + SQLite backends with encryption.
tags: nextjs, sqlite, better-sqlite3, encryption, aes-256-gcm, migrations, typescript
---

# Next.js + SQLite Backend with Encryption at Rest

Build production-ready local backends using Next.js 15 + TypeScript + better-sqlite3 with encryption, migrations, and clean domain separation.

## Tech Stack

| Layer | Choice |
|-------|--------|
| Runtime | Node.js 22+ (Next.js 15 App Router) |
| Language | TypeScript (strict) |
| Database | better-sqlite3 (WAL mode, synchronous) |
| Encryption | Node.js crypto (AES-256-GCM) |
| HTTP | Next.js route handlers + native fetch |

## Project Setup

```bash
npm init -y
npm install next react react-dom better-sqlite3
npm install -D typescript @types/node @types/react @types/better-sqlite3 tsx eslint eslint-config-next
```

### next.config.mjs

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  serverExternalPackages: ['better-sqlite3'],
};
export default nextConfig;
```

Note: Next 15 moved `experimental.serverComponentsExternalPackages` to `serverExternalPackages`.

### tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "ES2022"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./src/*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

## Database Core (src/lib/db/core.ts)

Singleton better-sqlite3 connection with WAL + migration runner:

```typescript
import Database from 'better-sqlite3';
import path from 'node:path';
import fs from 'node:fs';

let dbInstance: Database.Database | null = null;

function getDataDir(): string {
  const dir = process.env.DATA_DIR || path.join(process.cwd(), 'data');
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  return dir;
}

export function getDb(): Database.Database {
  if (dbInstance) return dbInstance;
  const dbPath = path.join(getDataDir(), 'app.db');
  dbInstance = new Database(dbPath);
  dbInstance.pragma('journal_mode = WAL');
  dbInstance.pragma('foreign_keys = ON');
  return dbInstance;
}

export interface Migration {
  version: number;
  name: string;
  up: (db: Database.Database) => void;
}

export function migrate(migrations: Migration[]) {
  const db = getDb();
  db.exec(`
    CREATE TABLE IF NOT EXISTS _migrations (
      version INTEGER PRIMARY KEY,
      name TEXT NOT NULL,
      applied_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
  `);
  for (const m of migrations) {
    const already = db.prepare('SELECT 1 FROM _migrations WHERE version = ?').get(m.version);
    if (already) continue;
    db.transaction(() => {
      m.up(db);
      db.prepare('INSERT INTO _migrations (version, name) VALUES (?, ?)').run(m.version, m.name);
    })();
  }
}
```

## Encryption at Rest (src/lib/db/crypto.ts)

AES-256-GCM with per-value random IV:

```typescript
import crypto from 'node:crypto';

const ALGO = 'aes-256-gcm';
const IV_LEN = 16;
const TAG_LEN = 16;

let keyBuffer: Buffer | null = null;

function getKey(): Buffer {
  if (keyBuffer) return keyBuffer;
  const hex = process.env.ENCRYPTION_KEY;
  if (!hex || hex.length !== 64) {
    throw new Error('ENCRYPTION_KEY must be 64 hex chars (32 bytes). Generate: openssl rand -hex 32');
  }
  keyBuffer = Buffer.from(hex, 'hex');
  return keyBuffer;
}

/** Encrypt plaintext → "iv:tag:ciphertext" (all hex) */
export function encrypt(plaintext: string): string {
  const iv = crypto.randomBytes(IV_LEN);
  const cipher = crypto.createCipheriv(ALGO, getKey(), iv);
  const enc = Buffer.concat([cipher.update(plaintext, 'utf8'), cipher.final()]);
  const tag = cipher.getAuthTag();
  return `${iv.toString('hex')}:${tag.toString('hex')}:${enc.toString('hex')}`;
}

/** Decrypt "iv:tag:ciphertext" → plaintext */
export function decrypt(payload: string): string {
  const [ivHex, tagHex, encHex] = payload.split(':');
  if (!ivHex || !tagHex || !encHex) throw new Error('Malformed encrypted payload');
  const iv = Buffer.from(ivHex, 'hex');
  const tag = Buffer.from(tagHex, 'hex');
  const enc = Buffer.from(encHex, 'hex');
  const decipher = crypto.createDecipheriv(ALGO, getKey(), iv);
  decipher.setAuthTag(tag);
  return decipher.update(enc) + decipher.final('utf8');
}
```

Generate key: `openssl rand -hex 32`

## Migration Files

Naming: `src/lib/db/migrations/NNN_description.mts` (`.mts` required for direct tsx execution).

```typescript
// 001_initial_schema.mts
import type Database from 'better-sqlite3';

export function createInitialSchema(db: Database.Database) {
  db.exec(`
    CREATE TABLE IF NOT EXISTS my_table (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      -- Encrypted fields stored as "iv:tag:hex" ciphertext
      secret_encrypted TEXT,
      -- Non-sensitive extra fields (JSON)
      extra TEXT NOT NULL DEFAULT '{}',
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
  `);
}
```

Migration runner entry (`src/lib/db/migrate.mts`):

```typescript
import { migrate } from './core';
import { createInitialSchema } from './migrations/001_initial_schema.mts';

const migrations = [
  { version: 1, name: 'initial_schema', up: createInitialSchema },
];

migrate(migrations);
console.log(`Applied ${migrations.length} migration(s).`);
```

package.json script: `"db:migrate": "tsx src/lib/db/migrate.mts"`

## Domain Repository Pattern

Each entity gets its own CRUD module with automatic encryption:

```typescript
// src/lib/db/repos/myEntity.ts
import { randomUUID } from 'node:crypto';
import { getDb } from '../core';
import { encrypt, decrypt } from '../crypto';

export interface MyEntity {
  id: string;
  name: string;
  secret?: string;  // decrypted on read
  extra: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

// Map row ↔ domain object, encrypting/decrypting sensitive fields
function rowToEntity(r: Row): MyEntity {
  return {
    id: r.id, name: r.name,
    secret: r.secret_encrypted ? decrypt(r.secret_encrypted) : undefined,
    extra: JSON.parse(r.extra || '{}'),
    created_at: r.created_at, updated_at: r.updated_at,
  };
}

export function list(): MyEntity[] { /* SELECT * */ }
export function get(id: string): MyEntity | null { /* SELECT WHERE id */ }
export function create(data: CreateInput): MyEntity {
  // Encrypt sensitive fields before INSERT
  db.prepare('INSERT ... VALUES (?, ?, ?, ...)').
    run(id, data.name, data.secret ? encrypt(data.secret) : null, ...);
}
export function update(id: string, data: Partial<MyEntity>): MyEntity | null { /* ... */ }
export function remove(id: string): boolean { /* DELETE */ }
```

## 4-Level Scope Resolution Pattern

For features needing cascading fallback (e.g., proxy assignment):

```typescript
export function resolve(context: {
  accountId?: string;
  provider?: string;
  comboId?: string;
}): Entity | null {
  const levels = [
    { type: 'account', target: context.accountId },
    { type: 'provider', target: context.provider },
    { type: 'combo', target: context.comboId },
    { type: 'global', target: undefined },
  ];
  for (const lvl of levels) {
    const row = db.prepare(`
      SELECT p.* FROM entities p
      JOIN scopes s ON s.entity_id = p.id
      WHERE s.scope_type = ? AND (s.scope_target = ? OR s.scope_target IS NULL)
      ORDER BY s.priority ASC LIMIT 1
    `).get(lvl.type, lvl.target);
    if (row) return row;
  }
  return null;
}
```

## .env.example

```env
# Database
DATA_DIR=./data

# Encryption (generate: openssl rand -hex 32)
ENCRYPTION_KEY=

# Server
PORT=3000
```

## Key Pitfalls

1. **Use `.mts` extension** for migration files run via tsx — tsx needs explicit extension to resolve imports
2. **Encrypt before write, decrypt on read** — never store plaintext secrets in SQLite
3. **Random IV per encryption** — never reuse IV with same key in GCM mode
4. **WAL mode** — enables concurrent reads while writing; essential for performance
5. **Use transactions** for multi-statement operations (migrations, combo + targets)
6. **`serverExternalPackages`** — Next 15 key change; `experimental.*` is deprecated
7. **Validate ENCRYPTION_KEY at startup** — fail fast if missing or wrong length

## References

- `references/fryrouter-scaffold.md` — full scaffold example with 12 tables, proxy 4-level resolution, and encrypted domain repos
