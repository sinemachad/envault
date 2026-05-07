"""File watcher that monitors a .env file and re-locks it on change."""

import time
import os
import hashlib
from typing import Callable, Optional


def _file_hash(path: str) -> Optional[str]:
    """Return MD5 hex digest of file contents, or None if unreadable."""
    try:
        with open(path, "rb") as fh:
            return hashlib.md5(fh.read()).hexdigest()
    except OSError:
        return None


def watch_env(
    env_path: str,
    vault_path: str,
    key: str,
    on_lock: Callable[[str, str], None],
    poll_interval: float = 1.0,
    max_iterations: Optional[int] = None,
) -> None:
    """
    Poll *env_path* for changes and call *on_lock(env_path, vault_path)*
    whenever the file is modified.

    Parameters
    ----------
    env_path:       Path to the plaintext .env file to watch.
    vault_path:     Destination vault file written on each change.
    key:            Encryption key passed through to on_lock.
    on_lock:        Callable invoked with (env_path, vault_path, key) on change.
    poll_interval:  Seconds between file-stat checks.
    max_iterations: Stop after this many poll cycles (useful for testing).
    """
    last_hash = _file_hash(env_path)
    iterations = 0

    while True:
        if max_iterations is not None:
            if iterations >= max_iterations:
                break
            iterations += 1

        time.sleep(poll_interval)
        current_hash = _file_hash(env_path)

        if current_hash is None:
            continue

        if current_hash != last_hash:
            last_hash = current_hash
            on_lock(env_path, vault_path, key)


def make_lock_callback(verbose: bool = True) -> Callable:
    """Return a callback suitable for *on_lock* that calls vault.lock."""
    from envault.vault import lock
    from envault.audit import record_event

    def _cb(env_path: str, vault_path: str, key: str) -> None:
        lock(env_path, vault_path, key)
        record_event("watch_relock", {"env": env_path, "vault": vault_path})
        if verbose:
            print(f"[envault] change detected — re-locked {env_path} -> {vault_path}")

    return _cb
