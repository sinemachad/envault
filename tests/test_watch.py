"""Tests for envault.watch."""

import os
import time
import pytest

from envault.watch import _file_hash, watch_env
from envault.vault import lock, unlock
from envault.crypto import generate_key


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("API_KEY=secret\nDEBUG=true\n")
    return str(p)


@pytest.fixture()
def vault_file(tmp_path):
    return str(tmp_path / ".env.vault")


# ---------------------------------------------------------------------------
# _file_hash
# ---------------------------------------------------------------------------

class TestFileHash:
    def test_returns_string_for_existing_file(self, env_file):
        result = _file_hash(env_file)
        assert isinstance(result, str) and len(result) == 32

    def test_returns_none_for_missing_file(self, tmp_path):
        assert _file_hash(str(tmp_path / "nope.env")) is None

    def test_hash_changes_when_content_changes(self, env_file):
        h1 = _file_hash(env_file)
        with open(env_file, "a") as fh:
            fh.write("NEW=1\n")
        h2 = _file_hash(env_file)
        assert h1 != h2

    def test_hash_stable_for_unchanged_file(self, env_file):
        assert _file_hash(env_file) == _file_hash(env_file)


# ---------------------------------------------------------------------------
# watch_env
# ---------------------------------------------------------------------------

class TestWatchEnv:
    def test_callback_invoked_on_change(self, env_file, vault_file):
        key = generate_key()
        calls = []

        def fake_lock(ep, vp, k):
            calls.append((ep, vp, k))

        # Mutate file after a short pause inside a thread so watch sees it.
        import threading

        def mutate():
            time.sleep(0.05)
            with open(env_file, "a") as fh:
                fh.write("EXTRA=1\n")

        t = threading.Thread(target=mutate, daemon=True)
        t.start()

        watch_env(
            env_path=env_file,
            vault_path=vault_file,
            key=key,
            on_lock=fake_lock,
            poll_interval=0.02,
            max_iterations=10,
        )
        t.join()

        assert len(calls) >= 1
        assert calls[0][0] == env_file
        assert calls[0][1] == vault_file
        assert calls[0][2] == key

    def test_no_callback_when_file_unchanged(self, env_file, vault_file):
        key = generate_key()
        calls = []

        watch_env(
            env_path=env_file,
            vault_path=vault_file,
            key=key,
            on_lock=lambda *a: calls.append(a),
            poll_interval=0.01,
            max_iterations=5,
        )

        assert calls == []
