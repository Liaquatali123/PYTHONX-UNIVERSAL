"""Friendly single-file interactive terminal interface."""
from __future__ import annotations
import argparse
import shutil
import subprocess
from getpass import getpass
from pathlib import Path
from .scanner import inspect_file, write_json
from .recovery import recover_path, decode_payload
from .encryption import encrypt_file, decrypt_file, is_pyx_encrypted

BANNER = r"""
 ____  __   __ ____  _   _  ___  __  __
|  _ \ \ \ / /|  _ \| | | |/ _ \|  \/  |
| |_) | \ V / | |_) | |_| | | | | |\/| |
|  __/   | |  |  __/|  _  | |_| | |  | |
|_|      |_|  |_|   |_| |_|\___/|_|  |_|
             UNIVERSAL FILE TOOL
"""

def clean_path(value):
    return value.strip().strip('"').strip("'").strip()

def ask_output(prompt, default):
    value = input(f"{prompt} [{default}]: ").strip()
    return Path(clean_path(value)) if value else Path(default)

def show_inspection(data):
    print("\n[ FILE OVERVIEW ]")
    for key in ("name", "type", "size", "sha256"):
        if key in data:
            value = data[key]
            if key == "size":
                value = f"{value:,} bytes"
            print(f"  {key.replace('_', ' ').title():<12}: {value}")
    protection = data.get("protection", {})
    print("  Protection   :", protection.get("format", "Unknown / not identified"))
    print("  Encrypted    :", "YES" if protection.get("encrypted") else "Not detected")
    if protection.get("note"):
        print("  Note         :", protection["note"])
    if data.get("syntax_valid") is not None:
        print("  Python syntax :", "VALID" if data["syntax_valid"] else "INVALID")
        if data.get("syntax_error"):
            print("  Syntax error  :", data["syntax_error"])
    if data.get("archive"):
        print("  Archive items :", data["archive"]["entry_count"])
        if data["archive"].get("has_encrypted_entries"):
            print("  Password ZIP  : detected")
    if data.get("frozen_markers"):
        print("  Markers       :", ", ".join(data["frozen_markers"]))
    bytecode = data.get("bytecode", {})
    if bytecode.get("warning"):
        print("  Bytecode note :", bytecode["warning"])
    if bytecode.get("marshal_error"):
        print("  Marshal note  :", bytecode["marshal_error"])

def interactive():
    print(BANNER)
    print("  One file at a time | No folder scan | No automatic storage scan")
    print("  Paste or drag one file path into this terminal.")
    while True:
        raw = input("\n[ PYTHONX ] File path (or q to quit): ")
        if raw.strip().lower() in {"q", "quit", "exit"}:
            return 0
        path = Path(clean_path(raw)).expanduser()
        if not path.exists():
            print("  [!] File not found. Check the path and try again.")
            continue
        if not path.is_file():
            print("  [!] Select one file, not a folder.")
            continue
        break
    try:
        info = inspect_file(path)
        show_inspection(info)
    except Exception as exc:
        print(f"  [!] Inspection error: {type(exc).__name__}: {exc}")
        return 1
    suffix = path.suffix.lower()
    is_zip = bool(info.get("archive"))
    is_bytecode = suffix in {".pyc", ".pyo"}
    encrypted = is_pyx_encrypted(path)
    while True:
        print("\n[ SELECT ACTION ]")
        print("  1) Save full file report (JSON)")
        if is_zip:
            print("  2) Safely extract this archive")
        if is_bytecode:
            print("  3) Decompile bytecode (optional support)")
        print("  4) Try Base64 / zlib payload decoding")
        print("  5) Protect this file with AES-256-GCM password encryption")
        if encrypted:
            print("  6) Decrypt this PYTHONX protected file")
        print("  7) Show file details again")
        print("  0) Exit")
        choice = input("\n  Choose an option: ").strip()
        try:
            if choice == "0":
                return 0
            elif choice == "1":
                output = ask_output("JSON report path", str(path.with_name(path.name + ".report.json")))
                write_json(info, output)
                print("  [+] Report saved:", output.resolve())
            elif choice == "2" and is_zip:
                output = ask_output("Extraction folder", str(path.with_name(path.stem + "_extracted")))
                files = recover_path(path, output)
                print(f"  [+] Extracted {len(files)} file(s) to {output.resolve()}")
            elif choice == "3" and is_bytecode:
                exe = shutil.which("decompyle3")
                if not exe:
                    print("  [!] Install optional support: python -m pip install 'pythonx-universal[decompile]'")
                    continue
                output = ask_output("Output folder", str(path.with_name(path.stem + "_source")))
                result = subprocess.run([exe, "-o", str(output), str(path)], check=False)
                if result.returncode:
                    print("  [!] Unsupported bytecode version or decompilation failed.")
                else:
                    print("  [+] Output:", output.resolve())
            elif choice == "4":
                output = ask_output("Decoded output file", str(path.with_name(path.name + ".decoded")))
                method = decode_payload(path, output)
                print(f"  [+] Decoded using {method}: {output.resolve()}")
            elif choice == "5":
                output = ask_output("Encrypted output file", str(path.with_name(path.name + ".pyx")))
                password = getpass("  New password (minimum 8 characters): ")
                confirm = getpass("  Confirm password: ")
                if password != confirm:
                    print("  [!] Passwords do not match.")
                    continue
                encrypt_file(path, output, password)
                print("  [+] Protected file saved:", output.resolve())
                print("  [!] Keep the password safe. It cannot be recovered if lost.")
            elif choice == "6" and encrypted:
                output = ask_output("Decrypted output file", str(path.with_suffix(".recovered")))
                password = getpass("  Password: ")
                decrypt_file(path, output, password)
                print("  [+] Decrypted file saved:", output.resolve())
            elif choice == "7":
                show_inspection(inspect_file(path))
            else:
                print("  [!] Choose an option shown in the menu.")
        except Exception as exc:
            print(f"  [!] {type(exc).__name__}: {exc}")

def main(argv=None):
    parser = argparse.ArgumentParser(prog="pythonx", description="PYTHONX UNIVERSAL single-file tool")
    parser.add_argument("path", nargs="?", help="Optional single file path")
    args = parser.parse_args(argv)
    if not args.path:
        return interactive()
    path = Path(clean_path(args.path)).expanduser()
    if not path.exists():
        print("ERROR: File not found:", path)
        return 1
    if not path.is_file():
        print("ERROR: Give one file path, not a folder. Folder scanning is disabled.")
        return 1
    try:
        show_inspection(inspect_file(path))
        return 0
    except Exception as exc:
        print("ERROR:", type(exc).__name__ + ":", exc)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
