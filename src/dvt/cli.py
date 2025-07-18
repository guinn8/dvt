#!/usr/bin/env python3
from __future__ import annotations
import argparse, os, subprocess, sys, textwrap
from pathlib import Path
from typing import OrderedDict

DVT_HOME = Path(os.environ.get("DVT_HOME", Path.home() / "dev-tools"))

MANUAL = """
dvt – Developer‑Tools Launcher
================================

Workspace     :  $DVT_HOME   (default: ~/dev-tools)
Central helpers live in      $DVT_HOME/<repo‑slug>/
Each git repo holds a symlink .devtools → that folder.

One‑time setup
--------------
    dvt init                     # create the workspace
    dvt install-hook             # install shell hook, reload shell

Per‑repo setup
--------------
    cd my-project/
    dvt link                     # registers .devtools symlink

Day‑to‑day
----------
    dvt new build-fw             # scaffold new helper in this repo
    build-fw                     # run it immediately (hook added to $PATH)

Diagnostics
-----------
    dvt ls                       # list helpers visible from here
    dvt doctor                   # broken links, non-exec, duplicates
    dvt uninstall-hook           # remove shell hook cleanly

States
------
G0  absent         – dvt not installed
G1  installed      – workspace missing          (run `dvt init`)
G2  workspace      – no projects registered    (run `dvt link`)
G3  active         – helpers available         (normal work mode)

For detailed CLI flags use  dvt -h  or  dvt <cmd> -h
""".strip()

def cmd_help(_: argparse.Namespace) -> None: print(MANUAL)

# ── workspace helpers ────────────────────────────────────────────────
def ensure_workspace() -> None:
    if not DVT_HOME.exists():
        sys.exit("❌  No dev-tools workspace. Run  dvt init  first.")

def repo_root(cwd: Path = Path.cwd()) -> Path:
    out = subprocess.check_output(["git", "-C", cwd, "rev-parse", "--show-toplevel"], text=True).strip()
    return Path(out)

def current_link() -> Path: return repo_root() / ".devtools"

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
    dirs, seen, dir_ = [], set(), Path.cwd()
    while True:
        try:
            root = repo_root(dir_)
        except subprocess.CalledProcessError:
            break
        if root in seen: break
        seen.add(root)
        p = root / ".devtools"
        if p.is_dir(): dirs.append(p)
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

def cmd_doctor(_: argparse.Namespace) -> None:
    ensure_workspace()
    dirs = set(helper_dirs()) | {p for p in DVT_HOME.iterdir() if p.is_dir()}
    bad, non_exec = [], []
    for d in dirs:
        if not d.exists():
            bad.append(d); continue
        for f in d.iterdir():
            if f.is_file() and not os.access(f, os.X_OK):
                non_exec.append(f)
    if bad or non_exec:
        for b in bad: print(f"❌ broken link: {b}")
        for f in non_exec: print(f"❌ non-executable helper: {f}")
        sys.exit(1)
    print("✅ doctor: no issues detected")

def cmd_new(args: argparse.Namespace) -> None:
    ensure_workspace()
    link = current_link()
    if not link.is_symlink():
        sys.exit("❌  Repo not linked. Run dvt link first.")
    target = link / args.name
    if target.exists():
        sys.exit(f"❌  Helper '{args.name}' already exists.")
    target.write_text("#!/usr/bin/env bash\nset -euo pipefail\n\n")
    target.chmod(target.stat().st_mode | 0o755)
    print(f"✅  Created {target}")

def shell_hook_text() -> str:
    return textwrap.dedent(f"""
        # ----- dvt shell hook -----
        _dvt_refresh() {{
          [[ -d {DVT_HOME} ]] || return
          local dir=$PWD paths="" p
          while p=$(git -C "$dir" rev-parse --show-toplevel 2>/dev/null); do
            [[ -d "$p/.devtools" ]] && paths="${{paths}}$p/.devtools:"
            dir=$(dirname "$p")
          done
          PATH=$(echo "$PATH" | tr ':' '\\n' | grep -v '/\\.devtools$' | paste -sd:)
          PATH="${{paths}}$PATH"
        }}
        cd() {{ builtin cd "$@"; _dvt_refresh; }}
        _dvt_refresh
        # ----- end dvt hook -----
        """).strip()+"\n"

def cmd_shell_hook(_: argparse.Namespace) -> None: print(shell_hook_text(), end="")

def _hook_paths() -> tuple[Path, list[Path]]:
    cfg = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "dvt"
    return cfg / "hook.bash", [Path.home() / f for f in (".bash_profile", ".bashrc")]

def cmd_install_hook(_: argparse.Namespace) -> None:
    hook_file, rc_files = _hook_paths()
    hook_file.parent.mkdir(parents=True, exist_ok=True)
    hook_file.write_text(shell_hook_text())
    line = f"source {hook_file}\n"
    for rc in rc_files:
        txt = rc.read_text() if rc.exists() else ""
        if line not in txt:
            rc.write_text(txt + line)
    print(f"✅  dvt hook installed → {hook_file}")
    for rc in rc_files: print("   • sourced from", rc)

def cmd_uninstall_hook(_: argparse.Namespace) -> None:
    hook_file, rc_files = _hook_paths()
    line = f"source {hook_file}\n"
    for rc in rc_files:
        if not rc.exists(): continue
        txt = rc.read_text()
        if line in txt:
            rc.write_text(txt.replace(line, ""))
    if hook_file.exists(): hook_file.unlink()
    print("✅  dvt hook uninstalled")

# ── argparse wiring ──────────────────────────────────────────────────
def main() -> None:
    p = argparse.ArgumentParser(prog="dvt")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init").set_defaults(func=cmd_init)
    sub.add_parser("link").set_defaults(func=cmd_link)
    sub.add_parser("ls").set_defaults(func=cmd_ls)
    sub.add_parser("shell-hook").set_defaults(func=cmd_shell_hook)
    sub.add_parser("doctor").set_defaults(func=cmd_doctor)
    n = sub.add_parser("new"); n.add_argument("name"); n.set_defaults(func=cmd_new)
    sub.add_parser("install-hook").set_defaults(func=cmd_install_hook)
    sub.add_parser("uninstall-hook").set_defaults(func=cmd_uninstall_hook)
    sub.add_parser("help").set_defaults(func=cmd_help)
    args = p.parse_args()
    args.func(args)

if __name__ == "__main__": main()
