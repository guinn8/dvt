import subprocess, stat
from pathlib import Path
from .conftest import repo

def test_doctor_flags_non_exec(tmp_home, tmp_path):
    root = repo(tmp_path,"proj")
    subprocess.run(["dvt","init"], check=True)
    subprocess.run(["dvt","link"], cwd=root, check=True)
    central = Path(tmp_home,"dev-tools","proj")
    (central/"oops").write_text("echo hi\n")  # missing exec bit
    cp = subprocess.run(["dvt","doctor"], capture_output=True, text=True)
    assert cp.returncode != 0
    assert "non-executable" in cp.stdout
