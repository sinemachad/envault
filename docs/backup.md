# Vault Backup

The `backup` module lets you create point-in-time copies of an encrypted vault
file and restore them later, without exposing any plaintext secrets.

## Quick Start

```bash
# Create a backup before a risky change
envault backup create .env.vault --label before-deploy

# List all backups (newest first)
envault backup list

# Restore a specific backup
envault backup restore backup_2024-06-01T12-00-00Z.env.vault .env.vault

# Delete an old backup
envault backup delete backup_2024-06-01T12-00-00Z.env.vault
```

## How It Works

1. **`create`** copies the `.env.vault` file into `.envault/backups/` and
   records metadata (timestamp, optional label, source path) in an index file.
2. **`list`** reads the index and prints entries newest-first.
3. **`restore`** copies the archived file back to the specified destination.
4. **`delete`** removes the archived file and its index entry.

Backups are stored **encrypted** — the same Fernet key that was used to lock
the vault is required to decrypt a restored backup.

## Storage Layout

```
.envault/
  backups/
    index.json                           # metadata for all backups
    backup_2024-06-01T12-00-00Z.env.vault
    backup_2024-06-02T08-30-00Z.env.vault
```

## Python API

```python
from envault.backup import create_backup, list_backups, restore_backup, delete_backup

# Create
entry = create_backup(".env.vault", base_dir=".", label="v1.2-release")
print(entry["id"])  # backup_2024-...

# List
for b in list_backups("."):
    print(b["timestamp"], b["label"])

# Restore
restore_backup(entry["id"], dest_path=".env.vault", base_dir=".")

# Delete
delete_backup(entry["id"], base_dir=".")
```

## Notes

- Backup IDs are derived from the UTC timestamp and are unique.
- Labels are optional but recommended for clarity.
- Backups are not automatically pruned; use `delete` to manage storage.
