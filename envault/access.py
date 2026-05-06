"""Access control: restrict which keys a profile can read/write."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

_POLICY_FILENAME = "access_policy.json"


def _get_policy_path(base_dir: str) -> Path:
    return Path(base_dir) / _POLICY_FILENAME


def _load_policy(base_dir: str) -> Dict[str, List[str]]:
    path = _get_policy_path(base_dir)
    if not path.exists():
        return {}
    with open(path, "r") as fh:
        return json.load(fh)


def _save_policy(base_dir: str, policy: Dict[str, List[str]]) -> None:
    path = _get_policy_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as fh:
        json.dump(policy, fh, indent=2)


def set_allowed_keys(base_dir: str, profile: str, keys: List[str]) -> Dict[str, List[str]]:
    """Set the list of env keys a profile is allowed to access."""
    policy = _load_policy(base_dir)
    policy[profile] = list(keys)
    _save_policy(base_dir, policy)
    return {"profile": profile, "allowed_keys": policy[profile]}


def get_allowed_keys(base_dir: str, profile: str) -> Optional[List[str]]:
    """Return allowed keys for a profile, or None if no restriction set."""
    policy = _load_policy(base_dir)
    return policy.get(profile)


def remove_policy(base_dir: str, profile: str) -> bool:
    """Remove access policy for a profile. Returns True if it existed."""
    policy = _load_policy(base_dir)
    if profile not in policy:
        return False
    del policy[profile]
    _save_policy(base_dir, policy)
    return True


def filter_env(env: Dict[str, str], allowed_keys: Optional[List[str]]) -> Dict[str, str]:
    """Return a filtered env dict containing only allowed keys.
    If allowed_keys is None, all keys are permitted.
    """
    if allowed_keys is None:
        return dict(env)
    return {k: v for k, v in env.items() if k in allowed_keys}


def list_policies(base_dir: str) -> Dict[str, List[str]]:
    """Return all profile access policies."""
    return _load_policy(base_dir)
