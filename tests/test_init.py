import subprocess, os
from pathlib import Path
import subprocess

def test_init_creates_workspace(tmp_home):
    subprocess.run(["dvt", "init"], check=True)
    assert Path(tmp_home, "dev-tools").exists()
