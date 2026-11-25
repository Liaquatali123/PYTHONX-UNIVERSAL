# PYTHONX UNIVERSAL

Terminal-only Python file inspection and best-effort recovery. Python 3.9+; no mandatory runtime dependencies.

**ONE FILE ONLY:** You select one exact file. PYTHONX does not scan folders, the whole phone, or computer storage.

## Quick start — Android Termux

Copy and run this complete block for a fresh installation:

```bash
pkg update -y && pkg install -y python git
termux-setup-storage
git clone https://github.com/Liaquatali123/PYTHONX-UNIVERSAL.git
cd PYTHONX-UNIVERSAL
python -m pip install --upgrade pip
python -m pip install -e .
python main.py
```

Already installed? Copy this block to update and start:

```bash
cd ~/PYTHONX-UNIVERSAL
git pull
python -m pip install -e .
python main.py
```

## Windows PowerShell

Fresh install:

```powershell
git clone https://github.com/Liaquatali123/PYTHONX-UNIVERSAL.git
cd PYTHONX-UNIVERSAL
py -m pip install --upgrade pip
py -m pip install -e .
py main.py
```

## Linux / macOS

Fresh install:

```bash
git clone https://github.com/Liaquatali123/PYTHONX-UNIVERSAL.git
cd PYTHONX-UNIVERSAL
python3 -m pip install --upgrade pip
python3 -m pip install -e .
python3 main.py
```

## How to use

1. Run the start command above.
2. Paste the full path of one file when prompted. On Android, for example: `/sdcard/Download/sample.pyc`.
3. PYTHONX identifies the file and displays its information.
4. Choose an action from the numbered menu.
5. Enter an output path or press Enter to accept the suggested path.

You do not need to remember separate inspect/recover/decode commands. The interactive menu guides you.

## Available actions

- File overview and SHA-256 hash.
- Python source syntax check.
- Python bytecode metadata and compatible disassembly.
- ZIP/PYZ safe extraction with path traversal, symlink, entry-count and size safeguards.
- JSON report export.
- Explicit Base64 or zlib payload decoding.
- Optional bytecode decompilation with `decompyle3` (best-effort).

## Run tests

Copy this block from the repository folder:

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

## Safety and limitations

PYTHONX is not a universal decryptor or protection remover. It cannot break encryption, DRM, licensing, anti-tamper or access controls. Bytecode is Python-version-specific; decompilation is best-effort. PyInstaller, Nuitka, Cython, PyArmor and native binaries may require matching vendor tools, runtime, or original source. Detection does not imply extraction. Never execute recovered code from untrusted sources. Marshal parsing is not a security boundary.

MIT License; see LICENSE.
