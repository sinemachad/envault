# envault

> Lightweight secrets manager that encrypts `.env` files and syncs them across team members via a shared key.

---

## Installation

```bash
pip install envault
```

Or with [pipx](https://pypa.github.io/pipx/):

```bash
pipx install envault
```

---

## Usage

**Initialize envault in your project:**

```bash
envault init
```

**Encrypt your `.env` file and generate a shared key:**

```bash
envault lock
# → Encrypted: .env.vault
# → Key saved: .envault.key  (add this to .gitignore!)
```

**Share the key with your team** (via a password manager, CI secret, etc.), then teammates can decrypt with:

```bash
envault unlock --key <shared-key>
# → Restored: .env
```

**Inject secrets directly into a command without writing to disk:**

```bash
envault run --key <shared-key> -- python app.py
```

> ⚠️ Never commit `.env` or `.envault.key` to version control. Add both to your `.gitignore`.

---

## How It Works

envault uses **AES-256-GCM** encryption under the hood. The shared key is a base64-encoded 32-byte secret that any team member can use to lock or unlock the `.env` file. The encrypted `.env.vault` file is safe to commit to your repository.

---

## Contributing

Pull requests are welcome! Please open an issue first to discuss any major changes.

---

## License

[MIT](LICENSE) © envault contributors