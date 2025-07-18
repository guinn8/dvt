#!/usr/bin/env python3
from __future__ import annotations
import argparse, os, subprocess, sys, textwrap
from pathlib import Path
from typing import OrderedDict

DVT_HOME = Path(os.environ.get("DVT_HOME", Path.home() / "dev-tools"))

# ── workspace helpers ────────────────────────────────────────────────
def ensure_workspace() -> None:
    if not DVT_HOME.exists():
        sys.exit("❌  No dev-tools workspace. Run  dvt init  first.")

def repo_root(cwd: Path = Path.cwd()) -> Path:
    out = subprocess.check_output(
        ["git", "-C", cwd, "rev-parse", "--show-toplevel"], text=True
    ).strip()
    return Path(out)

def current_link() -> Path:
    return repo_root() / ".devtools"

# ── sub-commands ─────────────────────────────────────────────────────
def cmd_init(_: argparse.Namespace) -> None:
    DVT_HOME.mkdir(parents=True, exist_ok=True)
    print(f"✅  Created workspace at {DVT_HOME}")

def cmd_link(_: argparse.Namespace) -> None:
    ensure_workspace()
    root = repo_root()
    target = DVT_HOME / root.name
    target.mkdir(exist_ok=True)
    link = root / ".devtools"
    if link.is_symlink() or link.exists():
        link.unlink()
    link.symlink_to(target, target_is_directory=True)

    exclude_file = root / ".git/info/exclude"
    if exclude_file.exists():
        lines = exclude_file.read_text().splitlines()
        if ".devtools" not in lines:
            lines.append(".devtools")
            exclude_file.write_text("\n".join(lines) + "\n")
    else:
        exclude_file.parent.mkdir(parents=True, exist_ok=True)
        exclude_file.write_text(".devtools\n")

    print(f"🔗  {link} → {target}")

def helper_dirs() -> list[Path]:
    dirs: list[Path] = []
    seen: set[Path] = set()
    dir_ = Path.cwd()
    while True:
        try:
            root = repo_root(dir_)
        except subprocess.CalledProcessError:
            break
        if root in seen:
            break
        seen.add(root)
        p = root / ".devtools"
        if p.is_dir():
            dirs.append(p)
        dir_ = root.parent
    return dirs

def all_helpers() -> OrderedDict[str, Path]:
    table: OrderedDict[str, Path] = OrderedDict()
    for d in helper_dirs():
        for f in d.iterdir():
            if f.is_file() and os.access(f, os.X_OK) and f.name not in table:
                table[f.name] = f
    return table

def cmd_ls(_: argparse.Namespace) -> None:
    ensure_workspace()
    for name, path in all_helpers().items():
        print(f"{name:20} {path}")

def cmd_shell_hook(_: argparse.Namespace) -> None:
    print(
        textwrap.dedent(
            f"""\
            # ----- dvt shell hook -----
            _dvt_refresh() {{
            [[ -d {DVT_HOME} ]] || return
            local dir=$PWD paths=""
            local p
            while p=$(git -C "$dir" rev-parse --show-toplevel 2>/dev/null); do
                if [[ -d "$p/.devtools" ]]; then
                paths="${{paths}}$p/.devtools:"         # append, not prepend
                fi
                dir=$(dirname "$p")
            done
            PATH=$(echo "$PATH" | tr ':' '\\n' | grep -v '/\\.devtools$' | paste -sd:)
            PATH="${{paths}}$PATH"
            }}
            cd() {{ builtin cd "$@"; _dvt_refresh; }}
            _dvt_refresh
            # ----- end dvt hook -----
            """
        )
    )

def cmd_doctor(_: argparse.Namespace) -> None:
    ensure_workspace()
    bad = [d for d in helper_dirs() if not d.exists()]
    if bad:
        for b in bad:
            print(f"❌  broken link: {b}")
        sys.exit(1)
    print("✅  doctor: no issues detected")

# ── argparse wiring ──────────────────────────────────────────────────
def main() -> None:
    p = argparse.ArgumentParser(prog="dvt")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init").set_defaults(func=cmd_init)
    sub.add_parser("link").set_defaults(func=cmd_link)
    sub.add_parser("ls").set_defaults(func=cmd_ls)
    sub.add_parser("shell-hook").set_defaults(func=cmd_shell_hook)
    sub.add_parser("doctor").set_defaults(func=cmd_doctor)
    args = p.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
