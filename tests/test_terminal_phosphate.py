from pathlib import Path

import pytest

from restraints.builder import build_phil_from_pdb
from restraints.terminal_phosphate import (
    TERMINAL_OP3_ANGLES,
    generate_terminal_phosphate_restraints,
)


def test_terminal_op3_recipe_uses_csd_targets():
    text = generate_terminal_phosphate_restraints(
        "D", "1", {"P", "OP1", "OP2", "OP3", "O5'", "C5'"}
    )
    assert len(TERMINAL_OP3_ANGLES) == 3
    assert text.count("angle {") == 3
    assert "name OP1" in text
    assert "name OP2" in text
    assert "name OP3" in text
    assert "name O5'" in text
    assert "angle_ideal = 114" in text
    assert "sigma = 0.7" in text
    assert "angle_ideal = 112.8" in text
    assert "sigma = 1" in text
    assert "angle_ideal = 102.9" in text
    assert "sigma = 1.2" in text
    assert "bond {" not in text


def test_terminal_op3_recipe_accepts_legacy_o3p_alias():
    text = generate_terminal_phosphate_restraints(
        "D", "1", {"P", "O1P", "O2P", "O3P", "O5'"}
    )
    assert text.count("angle {") == 3


def test_terminal_op3_recipe_fails_closed_when_op3_missing():
    with pytest.raises(ValueError, match="missing required atom.*OP3"):
        generate_terminal_phosphate_restraints(
            "D", "1", {"P", "OP1", "OP2", "O5'"}
        )


def _atom(serial: int, name: str, element: str) -> str:
    return (
        f"{'ATOM':<6}{serial:5d} {name:>4s} {'DC':>3s} {'D':1s}{1:4d}    "
        f"{float(serial):8.3f}{0.0:8.3f}{0.0:8.3f}"
        f"{1.00:6.2f}{20.00:6.2f}          {element:>2s}\n"
    )


def test_builder_adds_terminal_phosphate_blocks_only_when_requested(tmp_path: Path):
    pdb = tmp_path / "model.pdb"
    pdb.write_text("".join([
        _atom(1, "P", "P"),
        _atom(2, "OP1", "O"),
        _atom(3, "OP2", "O"),
        _atom(4, "OP3", "O"),
        _atom(5, "O5'", "O"),
        _atom(6, "C5'", "C"),
        "TER\nEND\n",
    ]))

    ordinary = tmp_path / "ordinary.phil"
    build_phil_from_pdb(pdb, [], ordinary, include_stacking=False)
    assert "name OP3" not in ordinary.read_text()

    terminal = tmp_path / "terminal.phil"
    build_phil_from_pdb(
        pdb,
        [],
        terminal,
        include_stacking=False,
        terminal_phosphate_sites=["D:1"],
    )
    text = terminal.read_text()
    assert text.count("angle {") == 3
    assert "chain D and resid 1 and name OP3" in text
