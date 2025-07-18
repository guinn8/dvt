#!/usr/bin/env python3
from __future__ import annotations
import argparse, os, subprocess, sys, textwrap
from pathlib import Path
from typing import OrderedDict

DVT_HOME = Path(os.environ.get("DVT_HOME", Path.home() / "dev-tools"))


# ── helpers ───────────────────────────────────────────────────────────
def ensure_workspace() -> None:
    if not DVT_HOME.exists():
        sys.exit("❌  No dev‑tools workspace. Run  dvt init  first.")

def repo_root(cwd: Path = Path.cwd()) -> Path:
    return Path(
        subprocess.check_output(
            ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
            text=True,
            stderr=subprocess.DEVNULL,      # ← add this
        ).strip()
    )

def current_link() -> Path:
    return repo_root() / ".devtools"

def helper_dirs() -> list[Path]:
    dirs, seen, d = [], set(), Path.cwd()
    while True:
        try:
            root = repo_root(d)
        except subprocess.CalledProcessError:
            break
        if root in seen:
            break
        seen.add(root)
        p = root / ".devtools"
        if p.is_dir():
            dirs.append(p)
        d = root.parent
    return dirs


# ── core commands ────────────────────────────────────────────────────
def cmd_init(_: argparse.Namespace) -> None:
    DVT_HOME.mkdir(parents=True, exist_ok=True)
    print(f"✅  Created workspace at {DVT_HOME}")

def cmd_link(_: argparse.Namespace) -> None:
    ensure_workspace()
    root = repo_root()
    tgt = DVT_HOME / root.name
    tgt.mkdir(exist_ok=True)
    link = root / ".devtools"
    if link.is_symlink() or link.exists():
        link.unlink()
    link.symlink_to(tgt, target_is_directory=True)

    excl = root / ".git/info/exclude"
    lines = excl.read_text().splitlines() if excl.exists() else []
    if ".devtools" not in lines:
        excl.parent.mkdir(parents=True, exist_ok=True)
        lines.append(".devtools")
        excl.write_text("\n".join(lines) + "\n")
    print(f"🔗  {link} → {tgt}")

def cmd_ls(_: argparse.Namespace) -> None:
    ensure_workspace()
    table: OrderedDict[str, Path] = OrderedDict()
    for d in helper_dirs():
        for f in d.iterdir():
            if f.is_file() and os.access(f, os.X_OK) and f.name not in table:
                table[f.name] = f
    for n, pth in table.items():
        print(f"{n:20} {pth}")

def cmd_doctor(_: argparse.Namespace) -> None:
    ensure_workspace()
    dirs = set(helper_dirs()) | {p for p in DVT_HOME.iterdir() if p.is_dir()}
    bad, non_exec = [], []
    for d in dirs:
        if not d.exists():
            bad.append(d)
            continue
        for f in d.iterdir():
            if f.is_file() and not os.access(f, os.X_OK):
                non_exec.append(f)
    if bad or non_exec:
        for b in bad:
            print(f"❌ broken link: {b}")
        for f in non_exec:
            print(f"❌ non-executable helper: {f}")
        sys.exit(1)
    print("✅ doctor: no issues detected")

def cmd_new(a: argparse.Namespace) -> None:
    ensure_workspace()
    link = current_link()
    if not link.is_symlink():
        sys.exit("❌  Repo not linked. Run  dvt link first.")
    tgt = link / a.name
    if tgt.exists():
        sys.exit(f"❌  Helper '{a.name}' already exists.")
    tgt.write_text("#!/usr/bin/env bash\nset -euo pipefail\n\n")
    tgt.chmod(tgt.stat().st_mode | 0o755)
    print(f"✅  Created {tgt}")

def shell_hook_text() -> str:
    return textwrap.dedent(
        f"""\
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
        """
    ).strip() + "\n"

def cmd_shell_hook(_: argparse.Namespace) -> None:
    print(shell_hook_text(), end="")

def _hook_paths() -> tuple[Path, list[Path]]:
    cfg = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "dvt"
    return cfg / "hook.bash", [Path.home() / f for f in (".bash_profile", ".bashrc")]

def cmd_install_hook(_: argparse.Namespace) -> None:
    hook, rcs = _hook_paths()
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text(shell_hook_text())
    ln = f"source {hook}\n"
    for rc in rcs:
        txt = rc.read_text() if rc.exists() else ""
        if ln not in txt:
            rc.write_text(txt + ln)
    print(f"✅  Hook installed → {hook}")

def cmd_uninstall_hook(_: argparse.Namespace) -> None:
    hook, rcs = _hook_paths()
    ln = f"source {hook}\n"
    for rc in rcs:
        if rc.exists():
            rc.write_text(rc.read_text().replace(ln, ""))
    if hook.exists():
        hook.unlink()
    print("✅  Hook removed")


# ── argparse wiring ──────────────────────────────────────────────────
def main() -> None:
    p = argparse.ArgumentParser(
        prog="dvt",
        description="Per‑repo helper launcher with global workspace",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="create $DVT_HOME").set_defaults(func=cmd_init)
    sub.add_parser("link", help="symlink .devtools in current repo").set_defaults(func=cmd_link)
    sub.add_parser("ls", help="list helpers visible from cwd").set_defaults(func=cmd_ls)
    sub.add_parser("shell-hook", help="print Bash hook").set_defaults(func=cmd_shell_hook)
    sub.add_parser("doctor", help="health‑check workspace").set_defaults(func=cmd_doctor)

    n = sub.add_parser("new", help="scaffold new helper")
    n.add_argument("name")
    n.set_defaults(func=cmd_new)

    sub.add_parser("install-hook", help="write hook to ~/.config/dvt").set_defaults(func=cmd_install_hook)
    sub.add_parser("uninstall-hook", help="remove hook files").set_defaults(func=cmd_uninstall_hook)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
