# Access Control

Envault supports per-profile access policies that restrict which environment
variables a given profile is allowed to read or write.

## Overview

Policies are stored in `access_policy.json` alongside your vault files. Each
entry maps a profile name to a list of allowed env-var keys. Profiles without
a policy have unrestricted access to all keys.

## Commands

### Set a policy

```bash
envault access set dev --keys DB_URL,SECRET_KEY,DEBUG
```

This allows the `dev` profile to access only `DB_URL`, `SECRET_KEY`, and
`DEBUG`. Any other keys in the vault are invisible to this profile.

### Show a policy

```bash
envault access show dev
```

Prints the list of keys the `dev` profile may access, or a message indicating
that all keys are permitted when no policy is set.

### List all policies

```bash
envault access list
```

### Remove a policy

```bash
envault access remove dev
```

Deletes the policy for `dev`, restoring unrestricted access.

## Integration with unlock

When unlocking a vault with a profile that has an access policy, envault
automatically filters the output to only include permitted keys:

```bash
envault unlock --profile dev vault.env.enc
```

This ensures that team members using the `dev` profile cannot inadvertently
expose production secrets.

## Policy file format

```json
{
  "dev": ["DB_URL", "DEBUG"],
  "ci": ["CI_TOKEN", "BUILD_ENV"]
}
```

The file is plain JSON and can be committed to version control alongside
your encrypted vault files.
