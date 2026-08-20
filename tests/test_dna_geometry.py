from restraints.dna_geometry import (
    distance,
    midpoint,
    canonical_atom_coordinate,
    find_sugar_attachment_atom,
    glycosidic_vector,
)
from Bio.PDB import PDBParser
from restraints.residue_library import load_residue_records, find_residue


def test_distance():
    assert distance([0, 0, 0], [3, 4, 0]) == 5.0


def test_midpoint():
    result = midpoint([0, 0, 0], [2, 4, 6])
    assert list(result) == [1.0, 2.0, 3.0]


def test_modified_residue_atom_mapping():
    structure = PDBParser(QUIET=True).get_structure("DNA", "examples/D3X3.pdb")
    records = load_residue_records("data/Ligands.xlsx")

    cj1 = next(
        residue
        for residue in structure.get_residues()
        if residue.get_resname().strip() == "CJ1"
    )

    record = find_residue(records, "CJ1")[0]

    n7_coord = canonical_atom_coordinate(cj1, record, "N7")
    n2_coord = canonical_atom_coordinate(cj1, record, "N2")

    assert n7_coord is not None
    assert n2_coord is not None


def test_find_standard_sugar_attachment():
    structure = PDBParser(QUIET=True).get_structure("DNA", "examples/D3X3.pdb")
    records = load_residue_records("data/Ligands.xlsx")

    residue = next(
        residue
        for residue in structure.get_residues()
        if residue.get_resname().strip() == "CJ1"
    )

    record = find_residue(records, "CJ1")[0]
    atom = find_sugar_attachment_atom(residue, record)

    assert atom.get_name() == "C1'"


def test_find_nonstandard_sugar_attachment():
    structure = PDBParser(QUIET=True).get_structure("PNA", "examples/9L5Z.pdb")
    records = load_residue_records("data/Ligands.xlsx")

    residue = next(
        residue
        for residue in structure.get_residues()
        if residue.get_resname().strip() == "CPN"
    )

    record = find_residue(records, "CPN")[0]
    atom = find_sugar_attachment_atom(residue, record)

    assert atom.get_name() == "C8'"


def test_glycosidic_vector():
    structure = PDBParser(QUIET=True).get_structure("DNA", "examples/D3X3.pdb")
    records = load_residue_records("data/Ligands.xlsx")

    residue = next(
        residue
        for residue in structure.get_residues()
        if residue.get_resname().strip() == "CJ1"
    )

    record = find_residue(records, "CJ1")[0]
    vector = glycosidic_vector(residue, record)

    assert vector is not None
    assert len(vector) == 3


def test_nonstandard_glycosidic_vector():
    structure = PDBParser(QUIET=True).get_structure("PNA", "examples/9L5Z.pdb")
    records = load_residue_records("data/Ligands.xlsx")

    residue = next(
        residue
        for residue in structure.get_residues()
        if residue.get_resname().strip() == "CPN"
    )

    record = find_residue(records, "CPN")[0]
    vector = glycosidic_vector(residue, record)

    assert vector is not None
    assert len(vector) == 3


def test_nonstandard_glycosidic_vector():
    structure = PDBParser(QUIET=True).get_structure("PNA", "examples/9L5Z.pdb")
    records = load_residue_records("data/Ligands.xlsx")

    residue = next(
        residue
        for residue in structure.get_residues()
        if residue.get_resname().strip() == "CPN"
    )

    record = find_residue(records, "CPN")[0]
    vector = glycosidic_vector(residue, record)

    assert vector is not None
    assert len(vector) == 3
