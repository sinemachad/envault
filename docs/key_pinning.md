# Key Pinning

Key pinning lets you lock a vault file to a specific encryption key fingerprint.
This prevents accidental decryption (or re-encryption) with the wrong key after
a rotation, and provides a lightweight audit trail showing *when* a key was
trusted for a given vault.

## How it works

When you pin a key, envault computes a 16-character SHA-256 fingerprint of the
raw key string and writes it to a `.envault-pin` file in the working directory.
The pin file is a plain JSON document — safe to commit alongside your vault.

```json
{
  "vault": "/project/secrets.env.vault",
  "fingerprint": "3a9f1c0e7b2d4e8a",
  "label": "post-2024-q3-rotation",
  "pinned_at": "2024-09-01T12:00:00+00:00"
}
```

## CLI usage

### Pin a vault to a key

```bash
envault pin set secrets.env.vault $ENVAULT_KEY --label "q3-rotation"
```

### Show the current pin

```bash
envault pin show
```

Output:
```
Vault      : /project/secrets.env.vault
Fingerprint: 3a9f1c0e7b2d4e8a
Label      : q3-rotation
Pinned at  : 2024-09-01T12:00:00+00:00
```

### Verify a key against the pin

```bash
envault pin verify $ENVAULT_KEY
# Key matches pinned fingerprint. ✓
```

This command exits with code `1` if the key does **not** match, making it easy
to add to CI pipelines:

```yaml
- name: Verify envault key pin
  run: envault pin verify ${{ secrets.ENVAULT_KEY }}
```

### Remove the pin

```bash
envault pin remove
```

## Recommended workflow

1. After every key rotation (`envault rotate`), run `envault pin set` with the
   new key and a descriptive label.
2. Commit the updated `.envault-pin` alongside the rotated vault file.
3. Add `envault pin verify` to your CI pipeline to catch accidental key mismatches
   before a deployment.

## Notes

- If no pin file exists, `verify` always returns success — pinning is opt-in.
- The fingerprint is **not** the key itself; it cannot be reversed to recover
  the original key.
- Labels are optional but strongly recommended for traceability.
