"""Runtime environment injection — load a decrypted vault into os.environ."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional

from envault.vault import unlock
from envault.access import filter_allowed_keys


class InjectionResult:
    """Holds the outcome of an inject operation."""

    def __init__(self, injected: List[str], skipped: List[str]) -> None:
        self.injected = injected
        self.skipped = skipped

    def __repr__(self) -> str:  # pragma: no cover
        return f"InjectionResult(injected={self.injected}, skipped={self.skipped})"


def inject_env(
    vault_path: str,
    key: str,
    *,
    profile: Optional[str] = None,
    overwrite: bool = False,
    base_dir: Optional[str] = None,
) -> InjectionResult:
    """Decrypt *vault_path* and inject variables into :data:`os.environ`.

    Parameters
    ----------
    vault_path:
        Path to the encrypted ``.env.vault`` file.
    key:
        Base-64 encoded encryption key.
    profile:
        Optional profile name used for access-control filtering.
    overwrite:
        When *False* (default) existing env vars are **not** overwritten.
    base_dir:
        Directory used to resolve the access-control policy file.  Defaults
        to the directory that contains *vault_path*.
    """
    env_vars: Dict[str, str] = unlock(vault_path, key)

    if profile is not None:
        resolved_base = base_dir or str(Path(vault_path).parent)
        env_vars = filter_allowed_keys(env_vars, profile, base_dir=resolved_base)

    injected: List[str] = []
    skipped: List[str] = []

    for var_key, value in env_vars.items():
        if not overwrite and var_key in os.environ:
            skipped.append(var_key)
        else:
            os.environ[var_key] = value
            injected.append(var_key)

    return InjectionResult(injected=injected, skipped=skipped)
