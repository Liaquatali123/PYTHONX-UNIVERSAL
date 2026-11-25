"""Safe archive extraction and explicit Base64/zlib decoding."""
from __future__ import annotations
import base64
import binascii
import shutil
import zipfile
import zlib
from pathlib import Path, PurePosixPath

MAX_MEMBER = 64 * 1024 * 1024
MAX_TOTAL = 256 * 1024 * 1024

def safe_target(root, name):
    part = PurePosixPath(name)
    if part.is_absolute() or ".." in part.parts or (part.parts and ":" in part.parts[0]):
        raise ValueError("Unsafe archive path: " + name)
    root = Path(root).resolve()
    target = root.joinpath(*part.parts)
    resolved = target.resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError("Archive path escapes output directory")
    return target

def extract_zip(source, output):
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    written, total = [], 0
    with zipfile.ZipFile(source) as zf:
        infos = zf.infolist()
        if len(infos) > 10000:
            raise ValueError("Too many archive entries")
        for info in infos:
            if info.is_dir():
                continue
            if info.file_size > MAX_MEMBER:
                raise ValueError("Archive member exceeds size limit")
            total += info.file_size
            if total > MAX_TOTAL:
                raise ValueError("Archive exceeds total extraction limit")
            mode = (info.external_attr >> 16) & 0o170000
            if mode == 0o120000:
                raise ValueError("Symlink entries are refused")
            target = safe_target(out, info.filename)
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)
            written.append(str(target))
    return written

def recover_path(source, output):
    src, out = Path(source), Path(output)
    if src.is_dir():
        out.mkdir(parents=True, exist_ok=True)
        copied = []
        for item in src.rglob("*"):
            if item.is_file():
                target = safe_target(out, item.relative_to(src).as_posix())
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target)
                copied.append(str(target))
        return copied
    if zipfile.is_zipfile(src):
        return extract_zip(src, out)
    if src.suffix.lower() in (".py", ".pyc", ".pyo"):
        out.mkdir(parents=True, exist_ok=True)
        target = out / src.name
        shutil.copy2(src, target)
        return [str(target)]
    raise ValueError("Supported inputs: directory, ZIP/PYZ, .py, .pyc and .pyo")

def decode_payload(source, output):
    raw = Path(source).read_bytes()
    if len(raw) > MAX_MEMBER:
        raise ValueError("Payload exceeds size limit")
    try:
        decoded = base64.b64decode(b"".join(raw.split()), validate=True)
        method = "base64"
    except (binascii.Error, ValueError):
        try:
            decoded = zlib.decompress(raw)
            method = "zlib"
        except zlib.error as exc:
            raise ValueError("Input is neither valid Base64 nor zlib data") from exc
    if len(decoded) > MAX_TOTAL:
        raise ValueError("Decoded output exceeds size limit")
    Path(output).write_bytes(decoded)
    return method
