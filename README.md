# PYTHONX UNIVERSAL

Terminal-only Python file inspection and best-effort recovery. Python 3.9+; no mandatory runtime dependencies.

**One file at a time.** PYTHONX never scans folders, the whole phone, or computer storage. You choose one exact file path; it works only on that file.

## Start with one command

After installation, run:

    python main.py

Or, when installed:

    python -m pythonx.cli

The interactive tool asks for one file path, identifies its type, displays a summary, and shows relevant actions. Paste a path or drag a file into the terminal. Select an action from the menu; no need to remember separate commands.

Direct one-file inspection is also supported:

    python main.py "/sdcard/Download/sample.pyc"

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
    python main.py

## Actions

- Identify and inspect one selected .py, .pyc/.pyo, ZIP/PYZ, or other file.
- Check Python source syntax and compatible bytecode metadata.
- Safely extract a selected ZIP/PYZ archive with path traversal, symlink, entry-count and size safeguards.
- Save a JSON report.
- Explicitly attempt Base64 or zlib payload decoding.
- Optionally decompile bytecode when decompyle3 supports its Python version.

## Safety and limitations

This is not a universal decryptor or protection remover. It cannot break encryption, DRM, licensing, anti-tamper or access controls. Bytecode is Python-version-specific; decompilation is best-effort. PyInstaller, Nuitka, Cython, PyArmor and native binaries may require matching vendor tools, runtime, or original source. Detection does not imply extraction. Never execute recovered code from untrusted sources. Marshal parsing is not a security boundary.

## Tests

    python -m unittest discover -s tests -v

MIT License; see LICENSE.
