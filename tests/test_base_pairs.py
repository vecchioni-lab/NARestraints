
from pathlib import Path

import pytest

from restraints.base_pairs import read_base_pair_file, parse_residue_range


def test_parse_forward_range():
    assert parse_residue_range("103:108") == ["103", "104", "105", "106", "107", "108"]


def test_parse_reverse_range():
    assert parse_residue_range("214:209") == ["214", "213", "212", "211", "210", "209"]


def test_parse_single_residue():
    assert parse_residue_range("103") == ["103"]


def test_read_pair_file(tmp_path: Path):
    path = tmp_path / "pairs.txt"
    path.write_text(
        "# first stretch\n"
        "A 103:108\n"
        "C 214:209\n"
        "\n"
        "A 109:115\n"
        "B 125:119\n"
    )

    stretches = read_base_pair_file(path)

    assert len(stretches) == 2
    assert len(stretches[0].pairs()) == 6
    assert stretches[0].pairs()[0].base1.resid == "103"
    assert stretches[0].pairs()[-1].base2.resid == "209"
    assert len(stretches[1].pairs()) == 7


def test_mismatched_ranges():
    path = Path("/tmp/narestraints_bad_pairs.txt")
    path.write_text("A 1:3\nB 10:11\n")
    with pytest.raises(ValueError):
        read_base_pair_file(path)
