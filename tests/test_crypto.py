"""Tests for envault.crypto encryption/decryption module."""

import pytest
from envault.crypto import generate_key, derive_key, encrypt, decrypt


class TestGenerateKey:
    def test_returns_string(self):
        key = generate_key()
        assert isinstance(key, str)

    def test_key_is_unique(self):
        assert generate_key() != generate_key()

    def test_key_usable_for_encryption(self):
        key = generate_key()
        token = encrypt("hello", key)
        assert decrypt(token, key) == "hello"


class TestDeriveKey:
    def test_returns_key_and_salt(self):
        key, salt = derive_key("my-passphrase")
        assert isinstance(key, str)
        assert isinstance(salt, bytes)
        assert len(salt) == 16

    def test_same_passphrase_same_salt_gives_same_key(self):
        _, salt = derive_key("secret")
        key1, _ = derive_key("secret", salt)
        key2, _ = derive_key("secret", salt)
        assert key1 == key2

    def test_different_salts_give_different_keys(self):
        key1, _ = derive_key("secret")
        key2, _ = derive_key("secret")
        # Extremely unlikely to collide with random salts
        assert key1 != key2

    def test_derived_key_usable_for_encryption(self):
        key, _ = derive_key("passphrase")
        token = encrypt("env_value", key)
        assert decrypt(token, key) == "env_value"


class TestEncryptDecrypt:
    def test_roundtrip(self):
        key = generate_key()
        plaintext = "DATABASE_URL=postgres://user:pass@localhost/db"
        token = encrypt(plaintext, key)
        assert decrypt(token, key) == plaintext

    def test_encrypted_output_is_bytes(self):
        key = generate_key()
        token = encrypt("SECRET=abc123", key)
        assert isinstance(token, bytes)

    def test_different_keys_produce_different_tokens(self):
        key1, key2 = generate_key(), generate_key()
        t1 = encrypt("value", key1)
        t2 = encrypt("value", key2)
        assert t1 != t2

    def test_wrong_key_raises_value_error(self):
        key1 = generate_key()
        key2 = generate_key()
        token = encrypt("secret", key1)
        with pytest.raises(ValueError, match="Decryption failed"):
            decrypt(token, key2)

    def test_tampered_token_raises_value_error(self):
        key = generate_key()
        token = encrypt("secret", key)
        tampered = token[:-4] + b"XXXX"
        with pytest.raises(ValueError, match="Decryption failed"):
            decrypt(tampered, key)

    def test_multiline_env_content(self):
        key = generate_key()
        content = "API_KEY=abc\nDB_PASS=xyz\nDEBUG=true\n"
        assert decrypt(encrypt(content, key), key) == content
