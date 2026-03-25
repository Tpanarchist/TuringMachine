import os
import subprocess
import sys
from pathlib import Path


def test_python_module_help_smoke() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["SDL_VIDEODRIVER"] = "dummy"

    result = subprocess.run(
        [sys.executable, "-m", "tmviz", "--help"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()
    assert "--spec" in result.stdout
