# Key Rotation

Key rotation lets you replace the encryption key protecting a vault without
exposing the plaintext secrets.  You should rotate keys:

- When a team member leaves the project.
- After a suspected key leak.
- As part of a regular security hygiene schedule.

## CLI usage

```bash
# Auto-generate a new key and re-encrypt the vault
envault rotate .env.vault $OLD_KEY

# Supply an explicit replacement key
envault rotate .env.vault $OLD_KEY --new-key $NEW_KEY

# Print only the new key (useful in scripts / CI)
NEW_KEY=$(envault rotate .env.vault $OLD_KEY --print-key)
```

## Python API

```python
from envault.rotation import rotate_key

new_key = rotate_key(".env.vault", old_key)
print("Distribute this new key:", new_key)
```

## Workflow

1. Run `envault rotate` to get the new key.
2. Distribute the new key to all team members via a secure channel
   (e.g., a password manager or encrypted message).
3. Update any CI/CD environment variables that hold the old key.
4. Confirm every team member can `envault unlock` with the new key before
   discarding the old one.

## Security notes

- The old key is **never written to disk** during rotation.
- The vault file is updated **atomically** (write then replace).
- Every rotation is recorded in the audit log (`envault audit`).
