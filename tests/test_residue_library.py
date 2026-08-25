from restraints.residue_library import load_residue_records, find_residue


def test_load_residue_records():
    records = load_residue_records()
    assert len(records) > 600


def test_find_duplicate_residue():
    records = load_residue_records()
    matches = find_residue(records, "A40")

    assert len(matches) == 2
    assert {match["Source sheet"] for match in matches} == {"adenine", "D"}