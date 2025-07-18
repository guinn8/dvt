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
