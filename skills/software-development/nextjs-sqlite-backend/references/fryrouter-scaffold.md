# fryRouter Scaffold Reference

Complete Next.js 15 + TypeScript + better-sqlite3 scaffold with encryption, migrations, and domain-driven repos.

## Project Structure

```
fryrouter/
├── src/
│   ├── app/
│   │   ├── api/
│   │   │   ├── health/route.ts        # GET /api/health
│   │   │   └── v1/
│   │   │       ├── chat/route.ts      # POST /v1/chat/completions
│   │   │       └── models/route.ts    # GET /v1/models
│   │   ├── dashboard/                 # Web management UI (future)
│   │   ├── layout.tsx                 # Root layout
│   │   └── page.tsx                   # Home page
│   └── lib/
│       ├── db/
│       │   ├── core.ts                # DB singleton + migration runner
│       │   ├── crypto.ts              # AES-256-GCM encrypt/decrypt
│       │   ├── index.ts               # Barrel export
│       │   ├── migrate.mts            # CLI entry: tsx src/lib/db/migrate.mts
│       │   ├── migrations/
│       │   │   └── 001_initial_schema.mts
│       │   └── repos/
│       │       ├── apiKeys.ts          # Client API keys
│       │       ├── combos.ts           # Model routing groups + targets
│       │       ├── connections.ts      # Provider OAuth/API-key accounts
│       │       ├── proxies.ts          # Proxy registry + 4-level resolution
│       │       └── settings.ts         # KV config store
│       ├── sse/                       # Request handling pipeline (future)
│       └── open-sse/                  # Routing/translation engine (future)
├── docs/
│   └── ARCHITECTURE.md
├── .env.example
├── .gitignore
├── next.config.mjs
├── package.json
└── tsconfig.json
```

## Database Schema (12 Tables)

### Core Tables

| Table | Purpose | Encryption |
|-------|---------|------------|
| `provider_connections` | OAuth/API-key accounts for upstream providers | api_key_encrypted, access_token_encrypted, refresh_token_encrypted |
| `secrets` | Long-term encrypted credential backup | ciphertext |
| `api_keys` | Client API keys for `/v1/` requests | — |
| `models` | Per-provider model catalog (capabilities, pricing) | — |
| `combos` | Named routing groups | — |
| `combo_targets` | Ordered model references within a combo | — |
| `proxy_registry` | HTTP/HTTPS/SOCKS5 proxy entries | username_encrypted, password_encrypted |
| `proxy_scopes` | Proxy → entity assignments (account/provider/combo/global) | — |
| `settings` | System configuration KV | — |
| `usage_logs` | Per-request telemetry (tokens, latency, cost, status) | — |
| `quota_snapshots` | Periodic aggregated usage per connection | — |
| `kv_store` | Miscellaneous KV (model aliases, custom models) | — |

### Key Schema Patterns

**Encrypted field convention:**
- Column name: `<field>_encrypted`
- Storage format: `iv:tag:ciphertext` (all hex-encoded, colon-separated)
- IV: 16 bytes random per encryption
- Auth tag: 16 bytes (GCM)

**Combo + targets (one-to-many):**
```sql
CREATE TABLE combos (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  kind TEXT NOT NULL DEFAULT 'fallback',  -- 'fallback' | 'round_robin'
  description TEXT,
  is_active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE combo_targets (
  id TEXT PRIMARY KEY,
  combo_id TEXT NOT NULL,
  provider TEXT NOT NULL,
  model_id TEXT NOT NULL,
  priority INTEGER NOT NULL DEFAULT 0,
  is_active INTEGER NOT NULL DEFAULT 1,
  FOREIGN KEY (combo_id) REFERENCES combos(id) ON DELETE CASCADE
);
```

**Proxy 4-level scope:**
```sql
CREATE TABLE proxy_scopes (
  id TEXT PRIMARY KEY,
  proxy_id TEXT NOT NULL,
  scope_type TEXT NOT NULL,  -- 'account' | 'provider' | 'combo' | 'global'
  scope_target TEXT,         -- NULL for global, else connection_id / provider_name / combo_id
  priority INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY (proxy_id) REFERENCES proxy_registry(id) ON DELETE CASCADE
);
```

**Usage logs (indexed for aggregation):**
```sql
CREATE INDEX idx_usage_ts ON usage_logs(timestamp);
CREATE INDEX idx_usage_provider ON usage_logs(provider);
CREATE INDEX idx_usage_model ON usage_logs(model);
```

## API Routes

### Health Check
```
GET /api/health → { status: "ok", name: "fryRouter", version: "0.1.0" }
```

### OpenAI-Compatible Endpoints
```
GET  /v1/models           # List available models (requires Bearer API key)
POST /v1/chat/completions # Chat completion (requires Bearer API key)
```

## Encryption Implementation

```typescript
// Generate key
// openssl rand -hex 32

import crypto from 'node:crypto';

const ALGO = 'aes-256-gcm';
const IV_LEN = 16;

function getKey(): Buffer {
  const hex = process.env.ENCRYPTION_KEY;
  if (!hex || hex.length !== 64) {
    throw new Error('ENCRYPTION_KEY must be 64 hex chars');
  }
  return Buffer.from(hex, 'hex');
}

export function encrypt(plaintext: string): string {
  const iv = crypto.randomBytes(IV_LEN);
  const cipher = crypto.createCipheriv(ALGO, getKey(), iv);
  const enc = Buffer.concat([cipher.update(plaintext, 'utf8'), cipher.final()]);
  const tag = cipher.getAuthTag();
  return `${iv.toString('hex')}:${tag.toString('hex')}:${enc.toString('hex')}`;
}

export function decrypt(payload: string): string {
  const [ivHex, tagHex, encHex] = payload.split(':');
  const iv = Buffer.from(ivHex, 'hex');
  const tag = Buffer.from(tagHex, 'hex');
  const enc = Buffer.from(encHex, 'hex');
  const decipher = crypto.createDecipheriv(ALGO, getKey(), iv);
  decipher.setAuthTag(tag);
  return decipher.update(enc) + decipher.final('utf8');
}
```

## Proxy 4-Level Resolution

```
Priority: account → provider → combo → global
```

```typescript
export function resolveProxy(context: {
  connectionId?: string;
  provider?: string;
  comboId?: string;
}): Proxy | null {
  const levels = [
    { type: 'account', target: context.connectionId },
    { type: 'provider', target: context.provider },
    { type: 'combo', target: context.comboId },
    { type: 'global', target: undefined },
  ];
  for (const lvl of levels) {
    const row = db.prepare(`
      SELECT p.* FROM proxy_registry p
      JOIN proxy_scopes s ON s.proxy_id = p.id
      WHERE s.scope_type = ? AND (s.scope_target = ? OR s.scope_target IS NULL) AND p.status = 'active'
      ORDER BY s.priority ASC LIMIT 1
    `).get(lvl.type, lvl.target);
    if (row) return rowToProxy(row);
  }
  return null;
}
```

## Connection CRUD with Auto-Encryption

```typescript
export function createConnection(data: {
  provider: string;
  authType?: string;
  apiKey?: string;
  accessToken?: string;
  refreshToken?: string;
}): ProviderConnection {
  const id = randomUUID();
  db.prepare(`
    INSERT INTO provider_connections (id, provider, auth_type, api_key_encrypted, access_token_encrypted, refresh_token_encrypted, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
  `).run(
    id, data.provider, data.authType || 'api_key',
    data.apiKey ? encrypt(data.apiKey) : null,
    data.accessToken ? encrypt(data.accessToken) : null,
    data.refreshToken ? encrypt(data.refreshToken) : null
  );
  return getConnection(id)!;
}
```

## Verification Commands

```bash
# Install
npm install

# Run migration
npm run db:migrate
# Output: "Applied 1 migration(s)."

# Verify tables
sqlite3 data/fryrouter.db ".tables"

# Verify schema
sqlite3 data/fryrouter.db ".schema proxy_registry"

# Start dev server
npm run dev
# → http://localhost:20129

# Test
curl http://localhost:20129/api/health
# → {"status":"ok","name":"fryRouter","version":"0.1.0"}
```

## Lessons from This Scaffold

1. **`.mts` extension required** — tsx needs explicit extension to resolve imports in migration files
2. **`serverExternalPackages`** — Next 15 moved this from `experimental.*`; old key triggers warning
3. **Encrypt before write, decrypt on read** — repo pattern handles this automatically
4. **Combo + targets split** — use `db.transaction()` for atomic insert of combo with multiple targets
5. **Proxy 4-level resolution** — iterate scope levels in priority order, return first active match
6. **Usage logs indexed** — add indexes on timestamp/provider/model for fast aggregation queries

## Repository

- GitHub: https://github.com/techysy/fry-router
- License: MIT
- Author: yangyu (techysy)
