# Vault Rollback

envault can restore a vault to a previous state using snapshots stored in the
change history. This lets you undo accidental edits or bad rotations without
losing data.

## How It Works

Whenever `envault history record` (or an operation that records history with a
`snapshot`) is called, the plaintext key/value pairs are embedded in the
history log alongside the action label and timestamp.  The rollback command
finds those entries and re-encrypts the snapshot back into the vault file.

## Commands

### List rollback points

```bash
envault rollback-list path/to/.env.vault
```

Prints a numbered table of available rollback points, most recent first:

```
#     Action                          Timestamp
-------------------------------------------------------
0     lock                            2024-06-01T12:00:00
1     rotate                          2024-05-30T09:15:42
```

### Restore to a rollback point

```bash
# Restore to the most recent snapshot (index 0)
envault rollback path/to/.env.vault <KEY>

# Restore to an older snapshot
envault rollback path/to/.env.vault <KEY> --index 1
```

Flags:

| Flag | Description |
|------|-------------|
| `--index N` | Rollback point to restore (default: `0`, most recent) |
| `-q / --quiet` | Suppress confirmation output |

## Example Workflow

```bash
# 1. Lock and record a snapshot
envault lock .env --key $ENVAULT_KEY
envault history record .env.vault --action lock --snapshot

# 2. Make changes, then realise something went wrong
envault rollback-list .env.vault
envault rollback .env.vault $ENVAULT_KEY --index 0
```

## Safety Notes

- Rollback **overwrites** the current vault file immediately.
- Always keep a backup of your key; without it, snapshots cannot be
  re-encrypted.
- Rollback points are only available if history was recorded with a snapshot;
  plain `history record` calls without `--snapshot` are skipped.
