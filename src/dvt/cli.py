#!/usr/bin/env python3
import argparse, sys, textwrap
from pathlib import Path

DVT_HOME = Path.home() / "dev-tools"

def ensure_workspace():
    if not DVT_HOME.exists():
        sys.exit("❌  No dev-tools workspace. Run  dvt init  first.")

def cmd_init(_):
    DVT_HOME.mkdir(parents=True, exist_ok=True)
    print(f"✅  Created workspace at {DVT_HOME}")

def cmd_doctor(_):
    ensure_workspace()
    print("✅  Workspace exists; nothing else checked yet")

def main() -> None:
    p = argparse.ArgumentParser(
        prog="dvt",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""
            dvt – dev-tools helper CLI (work in progress)
        """))
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init").set_defaults(func=cmd_init)
    sub.add_parser("doctor").set_defaults(func=cmd_doctor)
    args = p.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
