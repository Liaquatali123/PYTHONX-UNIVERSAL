"""Authenticated password-based file encryption for user-owned files.

Format: PYXENC1 | 16-byte scrypt salt | 12-byte AES-GCM nonce | ciphertext+tag.
"""
from __future__ import annotations

import os
from pathlib import Path

MAGIC = b"PYXENC1"
SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32
SCRYPT_N = 2 ** 14
SCRYPT_R = 8
SCRYPT_P = 1
MAX_ENCRYPT_SIZE = 256 * 1024 * 1024


def _crypto():
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
        from cryptography.hazmat.backends import default_backend
    except ImportError as exc:
        raise RuntimeError(
            "Encryption support requires cryptography. Install with: "
            "python -m pip install 'pythonx-universal[crypto]'"
        ) from exc
    return AESGCM, Scrypt, default_backend


def _derive_key(password: str, salt: bytes) -> bytes:
    if not isinstance(password, str) or len(password) < 8:
        raise ValueError("Password must contain at least 8 characters.")
    _, Scrypt, default_backend = _crypto()
    kdf = Scrypt(salt=salt, length=KEY_SIZE, n=SCRYPT_N,
                 r=SCRYPT_R, p=SCRYPT_P, backend=default_backend())
    return kdf.derive(password.encode("utf-8"))


def is_pyx_encrypted(path_or_data) -> bool:
    if isinstance(path_or_data, (bytes, bytearray)):
        return bytes(path_or_data).startswith(MAGIC)
    with Path(path_or_data).open("rb") as stream:
        return stream.read(len(MAGIC)) == MAGIC


def encrypt_file(source, destination, password: str) -> Path:
    src, dst = Path(source), Path(destination)
    if not src.is_file():
        raise FileNotFoundError(src)
    if src.resolve() == dst.resolve():
        raise ValueError("Input and output paths must be different.")
    if dst.exists():
        raise FileExistsError(f"Output already exists: {dst}")
    if src.stat().st_size > MAX_ENCRYPT_SIZE:
        raise ValueError("File exceeds the 256 MiB encryption limit.")
    if is_pyx_encrypted(src):
        raise ValueError("This file is already PYTHONX-encrypted.")
    raw = src.read_bytes()
    salt, nonce = os.urandom(SALT_SIZE), os.urandom(NONCE_SIZE)
    key = _derive_key(password, salt)
    AESGCM, _, _ = _crypto()
    ciphertext = AESGCM(key).encrypt(nonce, raw, MAGIC)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(MAGIC + salt + nonce + ciphertext)
    return dst


def decrypt_file(source, destination, password: str) -> Path:
    src, dst = Path(source), Path(destination)
    if not src.is_file():
        raise FileNotFoundError(src)
    if src.resolve() == dst.resolve():
        raise ValueError("Input and output paths must be different.")
    if dst.exists():
        raise FileExistsError(f"Output already exists: {dst}")
    if src.stat().st_size > MAX_ENCRYPT_SIZE:
        raise ValueError("File exceeds the 256 MiB decryption limit.")
    blob = src.read_bytes()
    minimum = len(MAGIC) + SALT_SIZE + NONCE_SIZE + 16
    if len(blob) < minimum or not blob.startswith(MAGIC):
        raise ValueError("Not a valid PYTHONX encrypted file.")
    offset = len(MAGIC)
    salt = blob[offset:offset + SALT_SIZE]
    nonce = blob[offset + SALT_SIZE:offset + SALT_SIZE + NONCE_SIZE]
    ciphertext = blob[offset + SALT_SIZE + NONCE_SIZE:]
    key = _derive_key(password, salt)
    AESGCM, _, _ = _crypto()
    try:
        plaintext = AESGCM(key).decrypt(nonce, ciphertext, MAGIC)
    except Exception as exc:
        raise ValueError("Wrong password or damaged/tampered encrypted file.") from exc
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(plaintext)
    return dst


def detect_protection(path) -> dict:
    p = Path(path)
    with p.open("rb") as stream:
        head = stream.read(1024 * 1024)
    if head.startswith(MAGIC):
        return {"encrypted": True, "format": "PYTHONX AES-256-GCM",
                "decryptable_by_pythonx": True,
                "note": "Requires the original password."}
    if head.startswith(b"Salted__"):
        label = "OpenSSL salted encryption container"
    elif head.startswith(b"-----BEGIN PGP MESSAGE-----"):
        label = "PGP armored message"
    elif head.startswith(b"\x84") or head.startswith(b"\x85"):
        label = "Possible OpenPGP binary data"
    elif head.startswith(b"7z\xbc\xaf\x27\x1c"):
        label = "7-Zip archive (may be encrypted)"
    elif head.startswith(b"Rar!\x1a\x07\x01\x00"):
        label = "RAR5 archive (may be encrypted)"
    elif b"/Encrypt" in head[:1024 * 1024] and head.startswith(b"%PDF"):
        label = "PDF declares encryption"
    else:
        label = None
    return {"encrypted": bool(label), "format": label or "Unknown / not identified",
            "decryptable_by_pythonx": False,
            "note": "Signature detection is indicative only; use the original format's legitimate password/key and software."}
