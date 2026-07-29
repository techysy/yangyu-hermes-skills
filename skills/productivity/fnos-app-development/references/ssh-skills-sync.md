# SSH Key Setup for Skills Sync

## Problem

When Hermes WebUI runs in Remote Gateway mode on fnOS, skills/settings are read from the NAS local filesystem (`hermes_home/skills/`), not from the remote Gateway. The NAS has no skills. The remote Arch VM has all skills.

## Solution: Periodic Sync via tar+ssh

Since rsync is often unavailable on Arch Linux (not installed by default), use `tar` over `ssh`:

```bash
# Push skills from Arch VM to fnOS (Arch VM has SSH access to fnOS)
tar czf - -C /home/your_user/.hermes skills/ | \
  ssh -o StrictHostKeyChecking=no yangyu@192.168.x.x \
  "tar xzf - -C /vol4/@appdata/HermesWebUI/hermes_home"
```

## One-Time SSH Key Setup

### Step 1: On Arch VM, generate key (if not already)
```bash
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""
```

### Step 2: Copy public key to fnOS
```bash
cat ~/.ssh/id_ed25519.pub | \
  ssh yangyu@192.168.x.x "tee -a ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

### Step 3: Test
```bash
ssh -o StrictHostKeyChecking=no yangyu@192.168.x.x "echo OK"
```

## Cron Job for Periodic Sync

Create a no_agent cron job on the Arch VM that syncs every 5 minutes:

```bash
hermes cron create \
  --schedule "every 5m" \
  --name sync-skills-to-fnos \
  --no-agent \
  --script 'tar czf - -C /home/your_user/.hermes skills/ | ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 yangyu@192.168.x.x "tar xzf - -C /vol4/@appdata/HermesWebUI/hermes_home"'
```

The cron job runs as a watchdog script (no LLM, no tokens). Empty stdout = silent tick. Only sync errors are reported.

## Verification

```bash
# Check skills on fnOS after sync
ssh yangyu@192.168.x.x "ls /vol4/@appdata/HermesWebUI/hermes_home/skills/ | head -5"
# Expected: 12306, apple, autonomous-ai-agents, blog, computer-use ...
```

## Alternative: Pull from fnOS (if SSH keys go other direction)

On fnOS `cmd/main`, add a `sync_skills()` function before starting the WebUI:

```bash
sync_skills() {
  log "Syncing skills from Arch VM..."
  rsync -avz --delete -e "ssh -o StrictHostKeyChecking=no" \
    yangyu@192.168.x.x:/home/your_user/.hermes/skills/ \
    "${DATA_DIR}/hermes_home/skills/" || log "sync failed"
}
```

Requires fnOS to have SSH key access to Arch VM.
