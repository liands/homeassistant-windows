"""Start only this project's Home Assistant and honor its restart status."""

import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime"
VENV = RUNTIME / "venv"
CONFIG = RUNTIME / "config"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Valida o YAML e encerra.")
    args = parser.parse_args()
    if Path(sys.prefix).resolve() != VENV.resolve():
        raise SystemExit(r"Use .\runtime\venv\Scripts\python.exe para iniciar.")
    if not (CONFIG / "configuration.yaml").is_file():
        raise SystemExit("Execute scripts/install.py primeiro.")
    environment = dict(os.environ, PYTHONUTF8="1", UV_CACHE_DIR=str(RUNTIME / "uv-cache"))
    # Core may resolve uv via PATH when it downloads requirements for integrations.
    environment["PATH"] = str(VENV / "Scripts") + os.pathsep + environment.get("PATH", "")
    if args.check:
        check = "from homeassistant.scripts import run; raise SystemExit(run(['check_config']))"
        command = [sys.executable, "-c", check, "-c", str(CONFIG), "--script",
                   "check_config", "--fail-on-warnings"]
        return subprocess.call(command, cwd=CONFIG, env=environment)
    command = [sys.executable, "-m", "homeassistant", "--ignore-os-check", "-c",
               str(CONFIG), "--log-no-color"]
    try:
        while True:
            code = subprocess.call(command, cwd=CONFIG, env=environment)
            if code != 100:
                return code
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
