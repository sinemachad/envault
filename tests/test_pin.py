"""Tests for envault.pin"""

import json
import os

import pytest

from envault.crypto import generate_key
from envault.pin import (
    PIN_FILENAME,
    _fingerprint,
    pin_key,
    read_pin,
    remove_pin,
    verify_pin,
)


@pytest.fixture()
def vault_file(tmp_path):
    p = tmp_path / "secrets.env.vault"
    p.write_text("dummy")
    return str(p)


@pytest.fixture()
def base_dir(tmp_path):
    return str(tmp_path)


class TestFingerprint:
    def test_returns_16_char_hex(self):
        fp = _fingerprint("somekey")
        assert len(fp) == 16
        assert all(c in "0123456789abcdef" for c in fp)

    def test_same_key_same_fingerprint(self):
        k = generate_key()
        assert _fingerprint(k) == _fingerprint(k)

    def test_different_keys_differ(self):
        assert _fingerprint(generate_key()) != _fingerprint(generate_key())


class TestPinKey:
    def test_returns_record_dict(self, vault_file, base_dir):
        key = generate_key()
        record = pin_key(key, vault_file, base_dir=base_dir)
        assert isinstance(record, dict)

    def test_record_has_required_fields(self, vault_file, base_dir):
        key = generate_key()
        record = pin_key(key, vault_file, base_dir=base_dir)
        for field in ("vault", "fingerprint", "label", "pinned_at"):
            assert field in record

    def test_fingerprint_matches_key(self, vault_file, base_dir):
        key = generate_key()
        record = pin_key(key, vault_file, base_dir=base_dir)
        assert record["fingerprint"] == _fingerprint(key)

    def test_label_stored(self, vault_file, base_dir):
        key = generate_key()
        record = pin_key(key, vault_file, label="v2", base_dir=base_dir)
        assert record["label"] == "v2"

    def test_pin_file_written_to_disk(self, vault_file, base_dir):
        key = generate_key()
        pin_key(key, vault_file, base_dir=base_dir)
        pin_path = os.path.join(base_dir, PIN_FILENAME)
        assert os.path.isfile(pin_path)

    def test_raises_if_vault_missing(self, tmp_path, base_dir):
        with pytest.raises(FileNotFoundError):
            pin_key(generate_key(), str(tmp_path / "nope.vault"), base_dir=base_dir)


class TestReadPin:
    def test_returns_none_when_no_pin(self, base_dir):
        assert read_pin(base_dir=base_dir) is None

    def test_returns_dict_after_pin_set(self, vault_file, base_dir):
        pin_key(generate_key(), vault_file, base_dir=base_dir)
        record = read_pin(base_dir=base_dir)
        assert isinstance(record, dict)


class TestVerifyPin:
    def test_correct_key_returns_true(self, vault_file, base_dir):
        key = generate_key()
        pin_key(key, vault_file, base_dir=base_dir)
        assert verify_pin(key, base_dir=base_dir) is True

    def test_wrong_key_returns_false(self, vault_file, base_dir):
        key = generate_key()
        pin_key(key, vault_file, base_dir=base_dir)
        assert verify_pin(generate_key(), base_dir=base_dir) is False

    def test_no_pin_always_passes(self, base_dir):
        assert verify_pin(generate_key(), base_dir=base_dir) is True


class TestRemovePin:
    def test_returns_true_when_removed(self, vault_file, base_dir):
        pin_key(generate_key(), vault_file, base_dir=base_dir)
        assert remove_pin(base_dir=base_dir) is True

    def test_returns_false_when_nothing_to_remove(self, base_dir):
        assert remove_pin(base_dir=base_dir) is False

    def test_file_gone_after_remove(self, vault_file, base_dir):
        pin_key(generate_key(), vault_file, base_dir=base_dir)
        remove_pin(base_dir=base_dir)
        assert read_pin(base_dir=base_dir) is None
