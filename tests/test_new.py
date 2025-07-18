import subprocess, stat
from pathlib import Path
from .conftest import repo

def test_new_scaffold(tmp_home, tmp_path):
    root = repo(tmp_path, "proj")
    subprocess.run(["dvt", "init"], check=True)
    subprocess.run(["dvt", "link"], cwd=root, check=True)

    subprocess.run(["dvt", "new", "flash-fw"], cwd=root, check=True)

    helper = Path(tmp_home, "dev-tools", "proj", "flash-fw")
    text = helper.read_text()
    assert text.startswith("#!/usr/bin/env bash")
    assert helper.stat().st_mode & stat.S_IXUSR  # executable bit
