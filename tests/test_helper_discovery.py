from pathlib import Path
import subprocess
from .conftest import repo, helper, bash

def test_helper_exec(tmp_home, tmp_path):
    root = repo(tmp_path, "app")
    subprocess.run(["dvt", "init"], check=True)
    subprocess.run(["dvt", "link"], cwd=root, check=True)

    central = Path(tmp_home, "dev-tools", "app")
    helper(central, "say-hi", "echo hi")

    out = bash(f"cd {root} && source <(dvt shell-hook) && say-hi")
    assert out.strip() == "hi"

def test_duplicate_collision(tmp_home, tmp_path):
    root = repo(tmp_path, "proj")
    subprocess.run(["dvt","init"], check=True)
    subprocess.run(["dvt","link"], cwd=root, check=True)
    central = Path(tmp_home,"dev-tools","proj")
    (central/"dup").write_text("#!/usr/bin/env bash\necho one\n")
    (central/"dup").chmod(0o755)
    # attempt to create same helper
    cp = subprocess.run(["dvt","new","dup"], cwd=root, capture_output=True, text=True)
    assert cp.returncode != 0
    assert "already exists" in cp.stderr
