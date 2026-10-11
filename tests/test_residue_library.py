from importlib.resources import as_file, files

import openpyxl
import pytest

from restraints.residue_library import load_residue_records, find_residue


def test_load_residue_records():
    records = load_residue_records()
    assert len(records) > 600


def test_find_duplicate_residue():
    records = load_residue_records()
    matches = find_residue(records, "A40")

    assert len(matches) == 2
    assert {match["Source sheet"] for match in matches} == {"adenine", "D"}


@pytest.mark.parametrize(
    "code, expected_sugar, expected_abbreviation",
    [
        ("5BU", "RNA", "5-bromo-rU"),
        ("BRU", "DNA", "5-bromo-dU"),
    ],
)
def test_bromouridine_sugar_metadata(code, expected_sugar, expected_abbreviation):
    """The reviewed CCD atom inventory distinguishes ribose from deoxyribose."""
    record, = find_residue(load_residue_records(), code)

    assert record["Sugar Type"] == expected_sugar
    assert record["Abbreviation"] == expected_abbreviation


@pytest.mark.parametrize(
    "code, canonical_position, expected_atom",
    [("DF", "O2", "S1"), ("S6G", "C5", "C5")],
)
def test_reviewed_legacy_atom_mapping(code, canonical_position, expected_atom):
    """The bundled mappings retain the reviewed PDB atom identity exactly."""
    record, = find_residue(load_residue_records(), code)

    assert record[canonical_position] == expected_atom


def test_all_canonical_c5_atom_mappings_have_no_outer_whitespace():
    """Canonical C5 selections must address the exact PDB atom name."""
    mismatches = [
        (record["Source sheet"], record["Ligand code"], record["C5"])
        for record in load_residue_records()
        if isinstance(record.get("C5"), str)
        and record["C5"] != record["C5"].strip()
    ]

    if mismatches:
        pytest.fail(
            f"{len(mismatches)} canonical C5 mappings have outer whitespace; "
            f"first examples: {mismatches[:5]!r}"
        )


@pytest.mark.parametrize(
    "row, code, expected_sugar, expected_abbreviation",
    [
        (429, "5BU", "RNA", "5-bromo-rU"),
        (428, "BRU", "DNA", "5-bromo-dU"),
    ],
)
def test_sort_sheet_matches_reviewed_bromouridine_metadata(
    row, code, expected_sugar, expected_abbreviation
):
    """Retain the human sorting view's agreement with the active mapping sheets."""
    resource = files("restraints").joinpath("data", "Ligands.xlsx")
    with as_file(resource) as path:
        workbook = openpyxl.load_workbook(path, read_only=True)
        try:
            sheet = workbook["sort"]
            assert sheet[f"B{row}"].value == code
            assert sheet[f"G{row}"].value == expected_sugar
            assert sheet[f"D{row}"].value == expected_abbreviation
        finally:
            workbook.close()
