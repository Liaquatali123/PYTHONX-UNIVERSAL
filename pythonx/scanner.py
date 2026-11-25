"""Metadata inspection for Python files and common archives."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import marshal
import struct
import types
import zipfile
from pathlib import Path

MAX_FILE_SIZE = 128 * 1024 * 1024
MARKERS = (b"pyinstaller", b"pyi_archive", b"PYZ-00", b"Nuitka", b"PyArmor")

def inspect_file(path):
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(p)
    size = p.stat().st_size
    if size > MAX_FILE_SIZE:
        raise ValueError("File exceeds 128 MiB inspection limit")
    data = p.read_bytes()
    result = {"path": str(p.resolve()), "name": p.name, "size": size,
              "sha256": hashlib.sha256(data).hexdigest(), "type": "unknown"}
    suffix = p.suffix.lower()
    if suffix == ".py":
        result["type"] = "python-source"
        try:
            compile(data.decode("utf-8-sig"), str(p), "exec")
            result["syntax_valid"] = True
        except Exception as exc:
            result["syntax_valid"] = False
            result["syntax_error"] = str(exc)
    elif suffix in (".pyc", ".pyo"):
        result["type"] = "python-bytecode"
        result["bytecode"] = inspect_pyc(data)
    if zipfile.is_zipfile(p):
        result["type"] = "python-zipapp" if suffix == ".pyz" else "zip-archive"
        with zipfile.ZipFile(p) as zf:
            infos = zf.infolist()
            result["archive"] = {"entry_count": len(infos),
                "entries": [{"name": i.filename, "size": i.file_size,
                             "compressed_size": i.compress_size} for i in infos[:10000]],
                "truncated": len(infos) > 10000}
    head = data[:2 * 1024 * 1024].lower()
    found = [m.decode("ascii") for m in MARKERS if m.lower() in head]
    if found:
        result["frozen_markers"] = found
        result.setdefault("warnings", []).append("Marker detection only; no protection bypass is performed.")
    if data.startswith(b"\x7fELF") or data.startswith(b"MZ"):
        result["type"] = "native-executable"
    return result

def inspect_pyc(data):
    info = {"magic_hex": data[:4].hex(),
            "current_magic_match": data[:4] == importlib.util.MAGIC_NUMBER}
    if len(data) < 16:
        info["warning"] = "Too short for a modern pyc header"
        return info
    info["flags"] = struct.unpack("<I", data[4:8])[0]
    try:
        obj = marshal.loads(data[16:])
        info["marshal_type"] = type(obj).__name__
        if isinstance(obj, types.CodeType):
            import dis
            import io
            out = io.StringIO()
            dis.dis(obj, file=out)
            info["code_name"] = obj.co_name
            info["names"] = list(obj.co_names)
            info["disassembly"] = out.getvalue()[:20000]
    except Exception as exc:
        info["marshal_error"] = str(exc)
    return info

def scan_path(path):
    # Never choose a default location: inspect only the explicit user-supplied path.
    root = Path(path).expanduser()
    if not root.exists():
        raise FileNotFoundError(root)
    if not root.is_file():
        raise ValueError("PYTHONX accepts one regular file only; folder scanning is disabled")
    return [inspect_file(root)]

def write_json(data, path):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
