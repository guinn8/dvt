from .conftest import repo, helper, bash
from pathlib import Path
import subprocess

def test_nested_shadowing(tmp_home, tmp_path):
    outer = repo(tmp_path, "outer"); subprocess.run(["dvt","init"], check=True)
    subprocess.run(["dvt","link"], cwd=outer, check=True)

    inner = outer / "sub"; inner.mkdir()
    subprocess.run(["git","init","-q"], cwd=inner)          # nested repo
    subprocess.run(["dvt","link"], cwd=inner, check=True)

    helper(Path(tmp_home, "dev-tools", "outer"), "echo-me", "echo root")
    helper(Path(tmp_home, "dev-tools", "sub"),   "echo-me", "echo sub")

    out = bash(f"cd {inner} && source <(dvt shell-hook) && echo-me")
    assert out.strip() == "sub"
