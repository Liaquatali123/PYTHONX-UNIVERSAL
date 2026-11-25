# PYTHONX UNIVERSAL

Cross-platform Python artifact inspection and best-effort recovery. Python 3.9+; no mandatory runtime dependencies.

## Features
- Inspect .py, .pyc/.pyo, ZIP and PYZ files.
- Read compatible bytecode headers, marshal code objects and disassemble with Python's built-in dis module.
- Safely extract ZIP/PYZ archives with traversal, symlink, entry-count and size checks.
- Scan directories and export JSON reports.
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

## Usage
    python main.py inspect sample.pyc
    python main.py scan ./samples --json report.json
    python main.py recover archive.pyz --output recovered/
    python main.py decode payload.txt --output decoded.bin
    python main.py decompile sample.pyc --output recovered/

Commands: inspect, scan, recover, decode, decompile. Run python main.py --help for options.

## Limitations and safety
This is not a universal decryptor or protection remover. It cannot break encryption, DRM, licensing, anti-tamper or access controls. Bytecode is Python-version-specific; decompilation is best-effort and depends on third-party support. PyInstaller, Nuitka, Cython, PyArmor and native binaries may require matching vendor tools, runtime, or original source. Detection does not imply extraction. Never execute recovered code from untrusted sources. Marshal parsing is not a security boundary; use isolation for unknown files.

## Tests
    python -m unittest discover -s tests -v

MIT License; see LICENSE.
