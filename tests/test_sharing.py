"""Tests for envault.sharing module."""

import json
import pytest
from pathlib import Path

from envault.sharing import export_bundle, import_bundle, BUNDLE_VERSION


SAMPLE_ENV = "DB_HOST=localhost\nDB_PORT=5432\nSECRET_KEY=supersecret\n"
PASSPHRASE = "correct-horse-battery-staple"


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text(SAMPLE_ENV, encoding="utf-8")
    return str(p)


@pytest.fixture
def bundle_file(tmp_path, env_file):
    out = tmp_path / "vault.bundle.json"
    export_bundle(env_file, PASSPHRASE, output_path=str(out))
    return str(out)


class TestExportBundle:
    def test_returns_json_string(self, env_file):
        result = export_bundle(env_file, PASSPHRASE)
        data = json.loads(result)
        assert isinstance(data, dict)

    def test_bundle_has_version(self, env_file):
        data = json.loads(export_bundle(env_file, PASSPHRASE))
        assert data["version"] == BUNDLE_VERSION

    def test_bundle_has_ciphertext(self, env_file):
        data = json.loads(export_bundle(env_file, PASSPHRASE))
        assert "ciphertext" in data
        assert len(data["ciphertext"]) > 0

    def test_writes_output_file(self, env_file, tmp_path):
        out = tmp_path / "out.json"
        export_bundle(env_file, PASSPHRASE, output_path=str(out))
        assert out.exists()
        assert out.stat().st_size > 0

    def test_ciphertext_differs_from_plaintext(self, env_file):
        data = json.loads(export_bundle(env_file, PASSPHRASE))
        assert "DB_HOST" not in data["ciphertext"]


class TestImportBundle:
    def test_returns_dict(self, bundle_file):
        result = import_bundle(bundle_file, PASSPHRASE)
        assert isinstance(result, dict)

    def test_recovers_all_keys(self, bundle_file):
        result = import_bundle(bundle_file, PASSPHRASE)
        assert result["DB_HOST"] == "localhost"
        assert result["DB_PORT"] == "5432"
        assert result["SECRET_KEY"] == "supersecret"

    def test_writes_env_file(self, bundle_file, tmp_path):
        out = tmp_path / ".env.restored"
        import_bundle(bundle_file, PASSPHRASE, output_path=str(out))
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert "DB_HOST" in content

    def test_wrong_passphrase_raises(self, bundle_file):
        with pytest.raises(Exception):
            import_bundle(bundle_file, "wrong-passphrase")

    def test_invalid_version_raises(self, tmp_path):
        bad_bundle = tmp_path / "bad.json"
        bad_bundle.write_text(json.dumps({"version": 99, "ciphertext": "abc"}), encoding="utf-8")
        with pytest.raises(ValueError, match="Unsupported bundle version"):
            import_bundle(str(bad_bundle), PASSPHRASE)
