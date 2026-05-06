# Lifecycle Hooks

envault supports **pre/post hooks** — shell commands that run automatically before or after key vault operations.

## Supported Events

| Event | Triggered |
|---|---|
| `pre-lock` | Before encrypting a `.env` file |
| `post-lock` | After encrypting a `.env` file |
| `pre-unlock` | Before decrypting a vault file |
| `post-unlock` | After decrypting a vault file |
| `pre-rotate` | Before rotating the encryption key |
| `post-rotate` | After rotating the encryption key |

## Managing Hooks

### Register a hook

```bash
envault hooks add post-lock "git add .env.vault"
envault hooks add post-unlock "./scripts/validate_env.sh"
```

### Remove a hook

```bash
envault hooks remove post-lock "git add .env.vault"
```

### List registered hooks

```bash
envault hooks list
```

Example output:

```
[post-lock]
  git add .env.vault
[post-unlock]
  ./scripts/validate_env.sh
```

## Hook Storage

Hooks are stored in `.envault-hooks.json` in the project directory. You may commit this file to share hooks with your team.

```json
{
  "post-lock": ["git add .env.vault"],
  "post-unlock": ["./scripts/validate_env.sh"]
}
```

## Hook Execution

- Hooks run in the project directory (`--dir` flag).
- All current environment variables are inherited by the hook process.
- Non-zero exit codes are captured and reported but do **not** abort the vault operation by default.
- `stdout` and `stderr` from hooks are available in the returned results when called programmatically via `run_hooks()`.

## Programmatic Usage

```python
from envault.hooks import add_hook, run_hooks

add_hook("post-lock", "echo vault updated")
results = run_hooks("post-lock")
for r in results:
    print(r["command"], "->", r["returncode"])
```
