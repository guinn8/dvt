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

# src/dvt/cli.py  (replace cmd_doctor)
def cmd_doctor(_):
    ensure_workspace()

    # collect every .devtools dir we should care about
    dirs = set(helper_dirs())                         # from cwd chain
    for proj in DVT_HOME.iterdir():                   # all projects
        if proj.is_dir():
            dirs.add(proj)

    bad_links, non_exec = [], []
    for d in dirs:
        if not d.exists():
            bad_links.append(d)
            continue
        for f in d.iterdir():
            if f.is_file() and not os.access(f, os.X_OK):
                non_exec.append(f)

    if bad_links or non_exec:
        for b in bad_links:
            print(f"❌ broken link: {b}")
        for f in non_exec:
            print(f"❌ non-executable helper: {f}")
        sys.exit(1)

    print("✅ doctor: no issues detected")



def cmd_new(args):
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
    return textwrap.dedent(
        f"""\
        # ----- dvt shell hook -----
        _dvt_refresh() {{
          [[ -d {DVT_HOME} ]] || return
          local dir=$PWD paths=""
          local p
          while p=$(git -C "$dir" rev-parse --show-toplevel 2>/dev/null); do
            if [[ -d "$p/.devtools" ]]; then
              paths="${{paths}}$p/.devtools:"   # append so inner wins
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
# ── helper used by both install & uninstall ───────────────────────────
def _hook_paths() -> tuple[Path, list[Path]]:
    cfg = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "dvt"
    hook_file = cfg / "hook.bash"
    rc_files = [Path.home() / f for f in (".bash_profile", ".bashrc")]
    return hook_file, rc_files


# ── install‑hook ───────────────────────────────────────────────────────
def cmd_install_hook(_: argparse.Namespace) -> None:
    hook_file, rc_files = _hook_paths()
    hook_file.parent.mkdir(parents=True, exist_ok=True)
    hook_file.write_text(shell_hook_text())

    line = f"source {hook_file}\n"
    for rc in rc_files:
        if rc.exists():
            lines = rc.read_text().splitlines(keepends=True)
            if line not in lines:
                rc.write_text("".join(lines) + line)
        else:
            rc.write_text(line)

    print("✅  dvt hook installed →", hook_file)
    for rc in rc_files:
        print("   • sourced from", rc)


# ── uninstall‑hook ─────────────────────────────────────────────────────
def cmd_uninstall_hook(_: argparse.Namespace) -> None:
    hook_file, rc_files = _hook_paths()
    line = f"source {hook_file}\n"
    still_referenced = False

    for rc in rc_files:
        if not rc.exists():
            continue
        lines = rc.read_text().splitlines(keepends=True)
        if line in lines:
            lines.remove(line)
            rc.write_text("".join(lines))
        if line in lines:                 # if we failed to remove
            still_referenced = True

    if hook_file.exists() and not still_referenced:
        hook_file.unlink()
        print("🗑️  removed hook file", hook_file)
    print("✅  dvt hook uninstalled")


# ── argparse wiring  (near bottom)──────────────────────────────────────

# ── argparse wiring ──────────────────────────────────────────────────
def main() -> None:
    p = argparse.ArgumentParser(prog="dvt")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init").set_defaults(func=cmd_init)
    sub.add_parser("link").set_defaults(func=cmd_link)
    sub.add_parser("ls").set_defaults(func=cmd_ls)
    sub.add_parser("shell-hook").set_defaults(func=print(shell_hook_text()))
    sub.add_parser("doctor").set_defaults(func=cmd_doctor)
    n = sub.add_parser("new"); n.add_argument("name"); n.set_defaults(func=cmd_new)
    ih = sub.add_parser("install-hook");   ih.set_defaults(func=cmd_install_hook)
    uh = sub.add_parser("uninstall-hook"); uh.set_defaults(func=cmd_uninstall_hook)

    ih.set_defaults(func=cmd_install_hook)

    args = p.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
