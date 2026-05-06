"""Pre/post hooks for vault operations (lock, unlock, rotate)."""

import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

HOOKS_FILE = ".envault-hooks.json"

VALID_EVENTS = ["pre-lock", "post-lock", "pre-unlock", "post-unlock", "pre-rotate", "post-rotate"]


def _get_hooks_path(base_dir: str = ".") -> Path:
    return Path(base_dir) / HOOKS_FILE


def _load_hooks(base_dir: str = ".") -> Dict[str, List[str]]:
    path = _get_hooks_path(base_dir)
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return json.load(f)


def _save_hooks(hooks: Dict[str, List[str]], base_dir: str = ".") -> None:
    path = _get_hooks_path(base_dir)
    with open(path, "w") as f:
        json.dump(hooks, f, indent=2)


def add_hook(event: str, command: str, base_dir: str = ".") -> Dict:
    """Register a shell command to run on a given event."""
    if event not in VALID_EVENTS:
        raise ValueError(f"Unknown event '{event}'. Valid events: {VALID_EVENTS}")
    hooks = _load_hooks(base_dir)
    hooks.setdefault(event, [])
    if command not in hooks[event]:
        hooks[event].append(command)
    _save_hooks(hooks, base_dir)
    return {"event": event, "command": command, "hooks": hooks}


def remove_hook(event: str, command: str, base_dir: str = ".") -> Dict:
    """Remove a registered hook command for an event."""
    hooks = _load_hooks(base_dir)
    if event not in hooks or command not in hooks[event]:
        raise KeyError(f"Hook '{command}' not found for event '{event}'")
    hooks[event].remove(command)
    if not hooks[event]:
        del hooks[event]
    _save_hooks(hooks, base_dir)
    return {"event": event, "command": command, "hooks": hooks}


def list_hooks(base_dir: str = ".") -> Dict[str, List[str]]:
    """Return all registered hooks."""
    return _load_hooks(base_dir)


def run_hooks(event: str, base_dir: str = ".", env: Optional[Dict] = None) -> List[Dict]:
    """Execute all commands registered for an event. Returns results."""
    hooks = _load_hooks(base_dir)
    results = []
    for command in hooks.get(event, []):
        merged_env = {**os.environ, **(env or {})}
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            env=merged_env,
            cwd=base_dir,
        )
        results.append({
            "command": command,
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        })
    return results
