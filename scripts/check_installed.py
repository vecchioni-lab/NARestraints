"""Smoke-test the installed distribution; execute with python -I outside the checkout."""
from __future__ import annotations

import argparse
import hashlib
from importlib import metadata, resources
import json
from pathlib import Path
import shutil
import subprocess
import sys
import sysconfig
import tempfile


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--expected-version", required=True)
    args = parser.parse_args()
    root = args.source_root.resolve()
    from restraints import builder, stacking
    from restraints.residue_library import load_residue_records

    installed_version = metadata.version("NARestraints")
    if installed_version != args.expected_version:
        raise SystemExit(f"Wrong installed version: {installed_version}")
    for module in (builder, stacking):
        path = Path(module.__file__).resolve()
        if root == path or root in path.parents or Path(sys.prefix).resolve() not in path.parents:
            raise SystemExit(f"Not a clean environment installation: {path}")
    direct = metadata.distribution("NARestraints").read_text("direct_url.json")
    if direct and json.loads(direct).get("dir_info", {}).get("editable"):
        raise SystemExit("Editable installs are not valid release tests")

    workbook = resources.files("restraints").joinpath("data", "Ligands.xlsx").read_bytes()
    if workbook != (root / "restraints/data/Ligands.xlsx").read_bytes():
        raise SystemExit("Installed workbook differs from the source resource")
    records = load_residue_records()
    if len(records) <= 600:
        raise SystemExit(f"Unexpected bundled residue count: {len(records)}")

    scripts = Path(sysconfig.get_path("scripts"))
    commands = ("narestraints", "narestraints-guesser", "narestraints-mirror")
    with tempfile.TemporaryDirectory(prefix="narestraints-installed-") as temporary:
        work = Path(temporary)
        for name in commands:
            subprocess.run([str(scripts / name), "--help"], cwd=work, check=True,
                           stdout=subprocess.DEVNULL, timeout=60)
        shutil.copyfile(root / "examples/DT.pdb", work / "input.pdb")
        shutil.copyfile(root / "examples/Std_padd.txt", work / "pairs.txt")
        subprocess.run([str(scripts / "narestraints"), "input.pdb", "pairs.txt", "-o", "output.phil"],
                       cwd=work, check=True, timeout=60)
        if not (work / "output.phil").stat().st_size:
            raise SystemExit("CLI generated empty restraints")
        subprocess.run([str(scripts / "narestraints-guesser"), "input.pdb", "-o", "guessed.txt"],
                       cwd=work, check=True, timeout=120)
        if not (work / "guessed.txt").stat().st_size:
            raise SystemExit("Guesser generated an empty file")
        subprocess.run([str(scripts / "narestraints-mirror"), "input.pdb", "-o", "mirrored.pdb"],
                       cwd=work, check=True, timeout=60)
        if not (work / "mirrored.pdb").stat().st_size:
            raise SystemExit("Mirror CLI generated an empty model")
    print(json.dumps({"version": installed_version, "python": sys.version.split()[0],
                      "builder": str(Path(builder.__file__).resolve()), "residue_records": len(records),
                      "workbook_sha256": hashlib.sha256(workbook).hexdigest(),
                      "installation": "non-editable", "console_scripts": list(commands)}, indent=2))


if __name__ == "__main__":
    main()
