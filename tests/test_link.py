from .conftest import repo
from pathlib import Path
import subprocess

def test_link_symlink(tmp_home, tmp_path):
    root = repo(tmp_path, "proj")
    subprocess.run(["dvt", "init"], check=True)
    subprocess.run(["dvt", "link"], cwd=root, check=True)

    link = root / ".devtools"
    assert link.is_symlink()
    assert ".devtools" in (root / ".git/info/exclude").read_text().splitlines()

