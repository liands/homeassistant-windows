"""Fetch a reviewed release of a supported optional custom component."""

import argparse
import json
from pathlib import Path, PurePosixPath
import shutil
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from install import ROOT, RUNTIME, metadata, verified_download


def install_jbl(config):
    """Install the reviewed local integration and its optional popup module."""
    source = ROOT / "integrations" / "jbl_partylight"
    target = config / "custom_components" / "jbl_partylight"
    frontend = config / "www" / "jbl-partylight-reconnect.js"
    if target.exists() or frontend.exists():
        raise SystemExit("A JBL já está instalada. Consulte a atualização manual no readme.md.")
    target.parent.mkdir(parents=True, exist_ok=True)
    frontend.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=target.parent) as directory:
        staged = Path(directory) / "jbl_partylight"
        shutil.copytree(source, staged)
        shutil.copyfile(ROOT / "integrations/frontend/jbl-partylight-reconnect.js", frontend)
        try:
            staged.rename(target)
        except BaseException:
            frontend.unlink(missing_ok=True)
            raise
    print("JBL instalada. Configure os secrets e o pacote YAML conforme o readme.md.")


def extract_component(source, archive, target):
    prefix = f"{source['prefix']}/custom_components/{source['domain']}/"
    with ZipFile(archive) as package:
        with TemporaryDirectory(dir=target.parent) as folder:
            staging = target.parent / folder / source["domain"]
            for name in package.namelist():
                if not name.startswith(prefix) or name.endswith("/"):
                    continue
                relative = PurePosixPath(name.removeprefix(prefix))
                if relative.is_absolute() or any(part == ".." or ":" in part or "\\" in part for part in relative.parts):
                    raise SystemExit("Caminho inesperado dentro da dependência.")
                output = staging.joinpath(*relative.parts)
                output.parent.mkdir(parents=True, exist_ok=True)
                with package.open(name) as entry, output.open("xb") as file:
                    shutil.copyfileobj(entry, file)
            manifest = json.loads((staging / "manifest.json").read_text(encoding="utf-8"))
            if manifest["domain"] != source["domain"] or manifest["version"] != source["version"]:
                raise SystemExit("Versão ou domínio inesperado.")
            staging.rename(target)


def main():
    sources = {item["name"]: item for item in metadata("components.json")}
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("component", choices=[*sources, "jbl"])
    component = parser.parse_args().component
    config = RUNTIME / "config"
    if not (config / "configuration.yaml").is_file():
        raise SystemExit("Execute scripts/install.py primeiro.")
    if component == "jbl":
        install_jbl(config)
        return
    source = sources[component]
    target = config / "custom_components" / source["domain"]
    if target.exists():
        raise SystemExit(f"{target} já existe. Consulte o procedimento de atualização no readme.md.")
    target.parent.mkdir(parents=True, exist_ok=True)
    archive = verified_download(source, RUNTIME / "downloads" / f"{source['name']}-{source['version']}.zip")
    extract_component(source, archive, target)
    print(f"Instalado {source['domain']} {source['version']}. Inicie o Core para configurar.")


if __name__ == "__main__":
    main()
