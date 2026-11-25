# PYTHONX UNIVERSAL

Terminal-only, cross-platform Python file inspection, password protection and best-effort recovery. Python 3.9+. One explicitly selected file at a time — no folder or whole-storage scanning.

## Android Termux — fresh install

Copy this complete block:

```bash
pkg update -y && pkg install -y python git rust clang openssl libffi
termux-setup-storage
git clone https://github.com/Liaquatali123/PYTHONX-UNIVERSAL.git
cd PYTHONX-UNIVERSAL
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e ".[crypto,decompile]"
python main.py
```

## Android Termux — update existing install

```bash
cd ~/PYTHONX-UNIVERSAL
git pull
python -m pip install -e ".[crypto,decompile]"
python main.py
```

## Windows PowerShell — fresh install

```powershell
git clone https://github.com/Liaquatali123/PYTHONX-UNIVERSAL.git
cd PYTHONX-UNIVERSAL
py -m pip install --upgrade pip
py -m pip install -e ".[crypto,decompile]"
py main.py
```

## Linux / macOS — fresh install

```bash
git clone https://github.com/Liaquatali123/PYTHONX-UNIVERSAL.git
cd PYTHONX-UNIVERSAL
python3 -m pip install --upgrade pip
python3 -m pip install -e ".[crypto,decompile]"
python3 main.py
```

## Protect your own code or file

1. Start PYTHONX and enter the exact file path.
2. Select **Protect this file**.
3. Enter a password of at least 8 characters twice.
4. PYTHONX creates a separate `.pyx` encrypted file. The original is not overwritten.

## Decrypt your PYTHONX file

1. Select the `.pyx` file.
2. PYTHONX identifies its own encrypted format and displays the decrypt action.
3. Enter the original password.
4. The decrypted content is saved to a separate output file.

Encryption uses **AES-256-GCM** authenticated encryption with a random salt and nonce, and a password-derived key using scrypt. A wrong password or modified file is rejected. Passwords are not stored. If you lose the password, PYTHONX cannot recover it.

This protects files at rest; it does not make Python source impossible to copy after it has been decrypted or executed. It is not source-code obfuscation, licensing enforcement, or a compiled executable packer.

## Detection and recovery

- Detects the PYTHONX encrypted format and several common encryption/container signatures (OpenSSL, PGP, encrypted PDF marker, 7z/RAR container signatures).
- Detects password-protected ZIP entries.
- Only PYTHONX's own AES-GCM format is decrypted directly by PYTHONX. For other formats, use the original software and a legitimate password/key. Detection is indicative, not proof that a file is encrypted.
- Python source syntax checks, bytecode metadata/disassembly, JSON reports, safe ZIP/PYZ extraction and Base64/zlib decoding.
- Optional best-effort Python bytecode decompilation.

## Tests

```bash
python -m pip install -e ".[crypto,decompile]"
python -m unittest discover -s tests -v
```

## Safety and limitations

PYTHONX does not crack passwords or break AES, DRM, licensing, anti-tamper or access controls. It cannot guarantee recovery of damaged files. Python bytecode is version-specific; decompilation may fail. Never execute recovered code from an untrusted source. Marshal parsing is not a security boundary. Keep a backup before recovery operations.

MIT License; see LICENSE.
