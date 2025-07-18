# tests/test_hook_uninstall.py
import subprocess
from pathlib import Path
from .conftest import repo, helper


def _login(cmd: str, home: Path) -> subprocess.CompletedProcess[str]:
    """Run a command inside a fresh *login* bash with isolated HOME."""
    env = {"HOME": str(home)}
    return subprocess.run(
        ["bash", "--login", "-c", cmd],
        text=True,
        capture_output=True,
        env=env,
    )


def test_hook_uninstall(tmp_home, tmp_path):
    # --- workspace & repo setup --------------------------------------
    root = repo(tmp_path, "demo")
    subprocess.run(["dvt", "init"], check=True)
    subprocess.run(["dvt", "link"], cwd=root, check=True)

    central = Path(tmp_home, "dev-tools", "demo")
    helper(central, "dvt_hi", "echo pong")          # unique helper name

    # --- install hook and prove helper works -------------------------
    subprocess.run(["dvt", "install-hook"], check=True)
    ok = _login(f"cd {root} && dvt_hi", tmp_home)
    assert ok.returncode == 0
    assert ok.stdout.strip() == "pong"

    # --- uninstall hook and prove helper disappears ------------------
    subprocess.run(["dvt", "uninstall-hook"], check=True)
    gone = _login(f"cd {root} && dvt_hi", tmp_home)
    assert gone.returncode != 0            # command no longer found
