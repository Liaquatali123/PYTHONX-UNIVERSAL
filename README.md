# PYTHONX UNIVERSAL

Terminal-only, cross-platform Python artifact inspection and best-effort recovery. Python 3.9+; no mandatory runtime dependencies. No web GUI and no automatic whole-storage scan.

## Features
- Inspect a user-supplied .py, .pyc/.pyo, ZIP or PYZ file path.
- Scan only the exact file or folder path supplied by the user.
- Safely extract ZIP/PYZ archives with traversal, symlink, entry-count and size checks.
- Export JSON reports.
- Explicitly decode recognizable Base64 or zlib payloads.
- Optional decompyle3 command integration.

## Install

Linux/macOS:
    git clone https://github.com/Liaquatali123/PYTHONX-UNIVERSAL.git
    cd PYTHONX-UNIVERSAL
    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -e .

Windows PowerShell:
    git clone https://github.com/Liaquatali123/PYTHONX-UNIVERSAL.git
    cd PYTHONX-UNIVERSAL
    py -m venv .venv
    .venv\Scripts\Activate.ps1
    python -m pip install -e .

Android Termux:
    pkg update && pkg install python git
    git clone https://github.com/Liaquatali123/PYTHONX-UNIVERSAL.git
    cd PYTHONX-UNIVERSAL
    python -m pip install -e .
    termux-setup-storage

## Terminal usage

Inspect one exact file:
    python main.py inspect /path/to/file.pyc

Scan one exact file:
    python main.py scan /path/to/file.py --json report.json

Scan a folder only when you explicitly provide that folder:
    python main.py scan /path/to/my-project --json report.json

Extract a ZIP/PYZ archive:
    python main.py recover /path/to/archive.pyz --output ./recovered

Decode a payload:
    python main.py decode /path/to/payload.txt --output ./decoded.bin

Decompile compatible bytecode (optional dependency):
    python -m pip install decompyle3
    python main.py decompile /path/to/file.pyc --output ./recovered

Run:
    python main.py --help

**No default storage path is scanned.** The tool works only on paths the user explicitly supplies. Supplying a folder to `scan` intentionally scans that folder recursively; supplying a single file inspects only that file.

## Limitations and safety
This is not a universal decryptor or protection remover. It cannot break encryption, DRM, licensing, anti-tamper or access controls. Bytecode is Python-version-specific; decompilation is best-effort and depends on third-party support. PyInstaller, Nuitka, Cython, PyArmor and native binaries may require matching vendor tools, runtime, or original source. Detection does not imply extraction. Never execute recovered code from untrusted sources. Marshal parsing is not a security boundary; use isolation for unknown files.

## Tests
    python -m unittest discover -s tests -v

MIT License; see LICENSE.
