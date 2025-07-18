import subprocess, stat
from pathlib import Path
from .conftest import repo

def test_hook_install(tmp_home, tmp_path, monkeypatch):
    # 1. create workspace + repo + helper
    subprocess.run(["dvt", "init"], check=True)
    root = repo(tmp_path, "demo")
    subprocess.run(["dvt", "link"], cwd=root, check=True)

    central = Path(tmp_home, "dev-tools", "demo")
    helper = central / "hi"
    helper.write_text("#!/usr/bin/env bash\necho ok\n")
    helper.chmod(helper.stat().st_mode | stat.S_IXUSR)

    # 2. run the installer (writes ~/.config/dvt/hook.bash)
    subprocess.run(["dvt", "install-hook"], check=True)

    # 3. start a fresh *login* shell that should source ~/.bashrc
    out = subprocess.check_output(
        ["bash", "--login", "-c", f"cd {root} && hi"], text=True
    )

    assert out.strip() == "ok"
