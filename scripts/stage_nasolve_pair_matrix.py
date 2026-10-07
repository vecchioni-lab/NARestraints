"""Stage isolated native NASolve modified-pair challenges; never run tools or edit donors.

Used after NARestraints role-orientation regression, from the NASolve terminal:
  python /path/to/clean/NARestraints/scripts/stage_nasolve_pair_matrix.py --nasolve-root "$PWD"
Each member has the same W 42-site model, GZ11 data, and off-pair 5CM/DF
annotations; only the ordered A:12/B:4 modified-base pairing differs.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
from tempfile import mkdtemp


# Identical off-pair annotations in all members: 5CM:G at A:7/C:9 and
# deposition-name (A1AAZ)->DF:A at A:19/D:4. The reference supplies B and D.
ANNOTATED_A = "GAGCAG(5CM)CTGTATGGACA(A1AAZ)CA"
ANNOTATED_C = "G(DG)CTGCT"
# Ordered pair tokens, NOT a "force" geometry override.
# A:T is a modified-context canonical control, not an unmodified dataset.
CASES = {
    "A_T_CONTROL": ("A:T", ("DA", "DT"), ("A", "T")),
    "D_T": ("D:T", ("1AP", "DT"), ("D", "T")),
    "B_S": ("B:S", ("IGU", "S6G"), ("B", "S")),
    "Z_P": ("Z:P", ("DZ", "DP"), ("Z", "P")),
    "K_X": ("K:X", ("CGY", "DX"), ("K", "X")),
}
INPUTS = (
    ("staraniso_alldata-unique.mtz", "staraniso_alldata-unique.mtz"),
    ("Data_1_autoPROC_STARANISO_all.cif", "Data_1_autoPROC_STARANISO_all.cif"),
    ("summary.html", "summary.html"),
)


class StagingError(ValueError):
    """Missing source files or an unsafe native-test destination."""


def _sha(path: Path) -> str:
    h = sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(data)
    return h.hexdigest()


def _sample_model(path: Path) -> dict[str, int]:
    # This is an input-count gate, not a geometry / ASU / model-compatibility
    # proof. The actual NASolve preflight owns the complete structure checks.
    sites: dict[str, set[str]] = {}
    with path.open(encoding="utf-8", errors="replace") as stream:
        for line in stream:
            if not line.startswith(("ATOM  ", "HETATM")) or len(line) < 27:
                continue
            chain = line[21:22].strip() or "_"
            residue = line[22:27].strip()
            sites.setdefault(chain, set()).add(residue)
    return {chain: len(numbers) for chain, numbers in sites.items()}


def stage_matrix(nasolve_root: Path, output_base: Path) -> dict[str, object]:
    """Allocate one fresh directory and copy, hash, and describe five members.

    Does not modify any existing project/worktree or launch campaign planning.
    Missing optional component dictionaries are reported, not improvised.
    """
    nasolve_root = Path(nasolve_root).expanduser().resolve()
    output_base = Path(output_base).expanduser().resolve()
    donor = nasolve_root / "examples/TestSets/GZ11"
    model = nasolve_root / "MR_frames/5W6W/5W6W_noPO4.pdb"
    source_paths = [(donor / name, name) for name, _ in INPUTS]
    source_paths.append((model, "zp_input_W.pdb"))
    for path, name in source_paths:
        if not path.is_file() or not path.stat().st_size:
            raise StagingError(f"Missing/empty native-test source {name}: {path}")
    for prohibited in (donor, model.parent, nasolve_root):
        if output_base == prohibited or prohibited in output_base.parents:
            raise StagingError(f"Output base must not reside beneath the checkout/source: {output_base}")
    if nasolve_root in output_base.parents or output_base == nasolve_root:
        raise StagingError("Output base must be outside the NASolve checkout")
    # Deliberately require a known source inventory before allocating anything.
    counts = _sample_model(model)
    if counts != {"A": 21, "B": 7, "C": 7, "D": 7}:
        raise StagingError(f"Unexpected W model chain/residue count: {counts}")

    output_base.mkdir(parents=True, exist_ok=True)
    root = Path(mkdtemp(prefix="nar-pair-matrix-", dir=output_base))
    files = {
        name: {"source": str(path), "sha256": _sha(path), "size": path.stat().st_size}
        for path, name in source_paths
    }
    members = []
    missing = []
    for case, (pair, requested_codes, roles) in CASES.items():
        dataset = root / case
        dataset.mkdir()
        for path, name in source_paths:
            destination = dataset / name
            shutil.copy2(path, destination)
            if _sha(destination) != files[name]["sha256"]:
                raise StagingError(f"Copy checksum mismatch: {case}/{name}")
        conf = (
            "[automr]\nmode = standard\nframe = W\n"
            f"pair = {pair}\n"
            "model = zp_input_W.pdb\n"
            "sequence_reference = w-metal-scaffold\n\n"
            "[sequences]\n"
            f"A = {ANNOTATED_A}\n"
            f"C = {ANNOTATED_C}\n"
        )
        (dataset / "nasolve.txt").write_text(conf, encoding="utf-8")
        unavailable = [
            code for code in requested_codes
            if code not in {"DA", "DC", "DG", "DT", "DU"}
            and not (nasolve_root / "src/nasolve/data/ligands" / (code + ".cif")).is_file()
        ]
        if unavailable:
            missing.append({"dataset": case, "codes": unavailable})
        members.append({
            "name": case,
            "ordered_pair": pair,
            "request_codes": list(requested_codes),
            "expected_base_classes": list(roles),
            "off_pair": {
                "A:7/C:9": ["5CM", "DG"],
                "A:19/D:4": ["DF", "DA"],
            },
            "dictionary_missing_in_NASolve": unavailable,
            "stage": "STAGED_ONLY",
        })
    manifest: dict[str, object] = {
        "schema_version": 1,
        "kind": "nasolve-narestraints-native-pair-validation-matrix",
        "scientific_scope": "synthetic chemistry challenge on real GZ11 diffraction; not proof of experimental pair identities",
        "nasolve_root": str(nasolve_root),
        "root": str(root),
        "source": files,
        "source_W_residue_counts": counts,
        "existing_failed_ZP_attempt": str(
            Path.home() / "NASolve-live-tests/zp-paired-native-oiipj_t2/GZ11_ZP/AutoMR/run_001"
        ),
        "upstream_candidate_pr": "https://github.com/vecchioni-lab/NARestraints/pull/4",
        "members": members,
        "missing_optional_pinned_dictionaries": missing,
        "human_review": "NOT_PERFORMED",
        "campaign_plan": "NOT_CREATED",
    }
    with (root / "staging-manifest.json").open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, indent=2, sort_keys=True)
        stream.write("\n")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--nasolve-root", type=Path, default=Path.cwd(),
        help="NASolve source root (the current working directory by default)",
    )
    parser.add_argument(
        "--output-base", type=Path, default=Path.home() / "NASolve-live-tests",
        help="Existing or creatable external tests directory",
    )
    args = parser.parse_args()
    try:
        manifest = stage_matrix(args.nasolve_root, args.output_base)
    except (StagingError, OSError) as exc:
        parser.error(str(exc))
    print("ROOT:", manifest["root"])
    print("CASES:", ", ".join(row["name"] for row in manifest["members"]))
    print("COPIES: all inputs match their donor SHA-256")
    for row in manifest["missing_optional_pinned_dictionaries"]:
        print("DICTIONARY-UNAVAILABLE:", row["dataset"], ", ".join(row["codes"]))
    print("NEXT: inspect dictionary blockers; plan only after reviewing roles")
    print("NATIVE TOOLS: not run; historic campaigns preserved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
