"""Command line interface."""
import argparse
import json
import shutil
import subprocess
from pathlib import Path
from .scanner import inspect_file, scan_path, write_json
from .recovery import recover_path, decode_payload

def main(argv=None):
    parser = argparse.ArgumentParser(prog="pythonx", description="PYTHONX UNIVERSAL")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("inspect", "scan"):
        cmd = sub.add_parser(name)
        cmd.add_argument("path")
        cmd.add_argument("--json", dest="json_file")
    rec = sub.add_parser("recover")
    rec.add_argument("path")
    rec.add_argument("-o", "--output", required=True)
    dec = sub.add_parser("decode")
    dec.add_argument("path")
    dec.add_argument("-o", "--output", required=True)
    decomp = sub.add_parser("decompile")
    decomp.add_argument("path")
    decomp.add_argument("-o", "--output", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "inspect":
            data = inspect_file(args.path)
            print(json.dumps(data, indent=2, ensure_ascii=False))
            if args.json_file:
                write_json(data, args.json_file)
        elif args.command == "scan":
            data = scan_path(args.path)
            print(json.dumps(data, indent=2, ensure_ascii=False))
            if args.json_file:
                write_json(data, args.json_file)
        elif args.command == "recover":
            files = recover_path(args.path, args.output)
            print("Recovered/copied", len(files), "file(s)")
            for f in files:
                print(" +", f)
        elif args.command == "decode":
            method = decode_payload(args.path, args.output)
            print("Decoded with", method, "to", Path(args.output).resolve())
        elif args.command == "decompile":
            exe = shutil.which("decompyle3")
            if not exe:
                print("Optional tool missing. Install with: python -m pip install decompyle3")
                return 2
            result = subprocess.run([exe, "-o", args.output, args.path], check=False)
            if result.returncode:
                print("Decompilation failed or bytecode version is unsupported.")
                return result.returncode
            print("Output:", Path(args.output).resolve())
        return 0
    except Exception as exc:
        print("ERROR:", type(exc).__name__ + ":", exc)
        return 1
