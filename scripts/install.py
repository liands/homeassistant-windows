"""Install the archived Core version and its Windows changes in a local venv."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime"
VENV = RUNTIME / "venv"
PYTHON = VENV / "Scripts" / "python.exe"
DATA = ROOT / "patches"


def metadata(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def digest(data):
    return hashlib.sha256(data).hexdigest() if data is not None else None


def verified_download(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file() and digest(target.read_bytes()) == source["sha256"]:
        return target
    temporary = target.with_suffix(target.suffix + ".download")
    try:
        with urllib.request.urlopen(source["url"], timeout=60) as response, temporary.open("wb") as output:
            shutil.copyfileobj(response, output)
        if digest(temporary.read_bytes()) != source["sha256"]:
            raise SystemExit(f"SHA-256 inesperado para {target.name}.")
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    return target


def apply_port(site):
    staged = {}
    for change in metadata("windows-port.json"):
        path = site / change["file"]
        current = path.read_bytes() if path.is_file() else None
        checksum = digest(current)
        if checksum == change["after"]:
            continue
        if checksum != change["before"]:
            raise SystemExit(f"Versão inesperada em {change['file']}. Pare o Core e recrie runtime/venv.")
        lines = (current or b"").decode().splitlines(keepends=True)
        for start, old, new in reversed(change["edits"]):
            end = start + len(old.splitlines(keepends=True))
            if "".join(lines[start:end]) != old:
                raise SystemExit(f"Trecho inesperado em {change['file']}.")
            lines[start:end] = new.splitlines(keepends=True)
        result = "".join(lines).encode()
        if digest(result) != change["after"]:
            raise SystemExit(f"SHA-256 final inesperado para {change['file']}.")
        staged[path] = result
    for path, result in staged.items():
        temporary = path.with_suffix(".port.tmp")
        temporary.write_bytes(result)
        temporary.replace(path)
    print(f"Porta Windows verificada. Arquivos atualizados: {len(staged)}.", flush=True)


def pip_install(*args):
    subprocess.run(
        [str(PYTHON), "-m", "pip", "--disable-pip-version-check", "--cache-dir",
         str(RUNTIME / "pip-cache"), "install", *map(str, args)],
        check=True, cwd=ROOT,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--with-ble", action="store_true", help="Instala também o coletor Xiaomi BLE.")
    args = parser.parse_args()
    if os.name != "nt" or platform.machine().upper() not in {"AMD64", "X86_64"} or sys.version_info[:2] != (3, 14):
        raise SystemExit("Use Python 3.14 x64 no Windows. A versão de referência é 3.14.4.")
    source = metadata("core-wheel.json")
    wheel = verified_download(source, RUNTIME / "downloads" / source["filename"])
    if not PYTHON.is_file():
        subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=True)
    pip_install(wheel, f"aiodns=={source['aiodns']}")
    apply_port(VENV / "Lib" / "site-packages")
    if args.with_ble:
        pip_install("-r", ROOT / "requirements-ble.txt")
    example = ROOT / "examples" / "config"
    for template in example.rglob("*"):
        if not template.is_file() or template.name.endswith(".example"):
            continue
        target = RUNTIME / "config" / template.relative_to(example)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            shutil.copyfile(template, target)
    print("Para iniciar: .\\runtime\\venv\\Scripts\\python.exe .\\scripts\\start.py")


if __name__ == "__main__":
    main()
