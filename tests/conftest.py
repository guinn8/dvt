from pathlib import Path
import os, shutil, subprocess, stat, tempfile, textwrap, pytest

# ---------- helper utilities ------------------------------------------
def _git(cmd, cwd):
    subprocess.run(["git", *cmd], cwd=cwd, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def repo(tmp_path: Path, name: str) -> Path:
    root = tmp_path / name
    _git(["init", "-q", root], cwd=tmp_path)   # git ≥2.38 supports init -q <dir>
    return root

def helper(path: Path, name: str, text: str = "echo helper") -> Path:
    f = path / name
    f.write_text(f"#!/usr/bin/env bash\n{text}\n")
    f.chmod(f.stat().st_mode | stat.S_IXUSR)
    return f

def bash(script: str) -> str:
    # run snippet in clean POSIX shell, return stdout
    return subprocess.check_output(["bash", "-c", script], text=True)

# ---------- fixtures ---------------------------------------------------
@pytest.fixture()
def tmp_home(monkeypatch, tmp_path):
    home = tmp_path / "fake_home"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("DVT_HOME", str(home / "dev-tools"))
    return home
