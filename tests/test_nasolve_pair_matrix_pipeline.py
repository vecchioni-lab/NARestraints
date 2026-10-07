"""Safety/provenance tests for the non-executing NASolve live-pair matrix stager."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.stage_nasolve_pair_matrix import (
    ANNOTATED_A, ANNOTATED_C, CASES, StagingError, stage_matrix,
)


def _fake_nasolve(root: Path) -> Path:
    donor = root / "examples/TestSets/GZ11"
    donor.mkdir(parents=True)
    (donor / "staraniso_alldata-unique.mtz").write_bytes(b"original-mtz")
    (donor / "Data_1_autoPROC_STARANISO_all.cif").write_text("data_test\n")
    (donor / "summary.html").write_text("<html>original donor</html>\n")
    frame = root / "MR_frames/5W6W"
    frame.mkdir(parents=True)
    model = frame / "5W6W_noPO4.pdb"
    text = ""
    count = 0
    for chain, start, total in (("A", 1, 21), ("B", 1, 7), ("C", 8, 7), ("D", 1, 7)):
        for i in range(start, start + total):
            count += 1
            text += (f"ATOM  {count:5d}  C1'  DC {chain}{i:4d}    "
                     f"{0.:8.3f}{0.:8.3f}{0.:8.3f}{1.:6.2f}{20.:6.2f}          C \n")
    model.write_text(text + "END\n")
    return root


def test_stage_five_distinct_frozen_sources_without_mutating_originals(tmp_path):
    source = _fake_nasolve(tmp_path / "src")
    originals = {
        str(path): path.read_bytes()
        for path in (*((source / "examples/TestSets/GZ11").iterdir()),
                     source / "MR_frames/5W6W/5W6W_noPO4.pdb")
    }
    manifest = stage_matrix(source, tmp_path / "live-tests")
    root = Path(manifest["root"])
    assert root.is_dir()
    assert manifest["human_review"] == "NOT_PERFORMED"
    assert manifest["campaign_plan"] == "NOT_CREATED"
    assert set(case["name"] for case in manifest["members"]) == set(CASES)
    assert manifest["source_W_residue_counts"] == {"A": 21, "B": 7, "C": 7, "D": 7}
    for name, (pair, _, _) in CASES.items():
        dataset = root / name
        config = (dataset / "nasolve.txt").read_text()
        assert f"pair = {pair}\n" in config
        assert f"A = {ANNOTATED_A}\n" in config
        assert f"C = {ANNOTATED_C}\n" in config
        assert "force =" not in config
        assert not (dataset / "NASolveCampaign").exists()
        assert not (dataset / "AutoMR").exists()
        for filename, entry in manifest["source"].items():
            assert (dataset / filename).read_bytes() == Path(entry["source"]).read_bytes()
    assert {str(path): path.read_bytes() for path in map(Path, originals)} == originals
    assert json.loads((root / "staging-manifest.json").read_text()) == manifest
    assert {x["dataset"] for x in manifest["missing_optional_pinned_dictionaries"]} == {
        "B_S", "Z_P", "K_X", "D_T",
    }


def test_staging_never_overwrites_existing_attempts(tmp_path):
    source = _fake_nasolve(tmp_path / "src")
    a = stage_matrix(source, tmp_path / "live-tests")
    folder = Path(a["root"])
    sentinel = folder / "protect-this-existing-run"
    sentinel.write_text("historical science")
    b = stage_matrix(source, tmp_path / "live-tests")
    assert a["root"] != b["root"]
    assert sentinel.read_text() == "historical science"


def test_missing_source_fails_before_creating_any_matrix(tmp_path):
    source = _fake_nasolve(tmp_path / "src")
    (source / "examples/TestSets/GZ11/summary.html").unlink()
    output = tmp_path / "live-tests"
    with pytest.raises(StagingError, match="Missing/empty"):
        stage_matrix(source, output)
    assert not output.exists()


def test_matrix_must_live_outside_source_checkout(tmp_path):
    source = _fake_nasolve(tmp_path / "src")
    with pytest.raises(StagingError, match="Output base"):
        stage_matrix(source, source / "live-tests")
    assert not (source / "live-tests").exists()
