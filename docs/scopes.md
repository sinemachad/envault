# Environment Scopes

Scopes let you register named aliases that map a human-readable label (e.g.
`dev`, `staging`, `prod`) to a specific vault file path. This makes it easy
to switch context without remembering file paths.

## Registering a scope

```bash
envault scope add dev .env.vault --description "Local development"
envault scope add staging envs/staging.vault
envault scope add prod envs/prod.vault --description "Production secrets"
```

Scopes are stored in `scopes.json` inside the working directory (or the path
provided via `--base-dir`).

## Listing scopes

```bash
envault scope list
```

Example output:

```
dev                  .env.vault             # Local development
staging              envs/staging.vault
prod                 envs/prod.vault        # Production secrets
```

## Inspecting a scope

```bash
envault scope show staging
```

Output:

```
name:        staging
vault:       envs/staging.vault
description:
```

## Removing a scope

```bash
envault scope remove staging
```

## Using scopes with other commands

Scopes are resolved at the application layer. Pass the vault path returned by
`get_scope()` directly to `lock`, `unlock`, `diff`, or any other command that
accepts a vault file path.

```python
from envault.scope import get_scope
from envault.vault import unlock

scope = get_scope(".", "prod")
if scope is None:
    raise SystemExit("Unknown scope 'prod'")

env = unlock(scope["vault"], key)
```

## Storage format

`scopes.json` is a plain JSON object keyed by scope name:

```json
{
  "dev": {
    "vault": ".env.vault",
    "description": "Local development"
  },
  "prod": {
    "vault": "envs/prod.vault",
    "description": "Production secrets"
  }
}
```

This file should be committed to version control so all team members share the
same scope definitions.
