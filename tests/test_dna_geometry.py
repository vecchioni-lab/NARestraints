import numpy as np
import pytest
from Bio.PDB import Atom, Chain, Residue

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
    records = load_residue_records()

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
    records = load_residue_records()

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
    records = load_residue_records()

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
    records = load_residue_records()

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
    records = load_residue_records()

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
    records = load_residue_records()

    residue = next(
        residue
        for residue in structure.get_residues()
        if residue.get_resname().strip() == "CPN"
    )

    record = find_residue(records, "CPN")[0]
    vector = glycosidic_vector(residue, record)

    assert vector is not None
    assert len(vector) == 3


@pytest.mark.parametrize("code", ["PSU", "P2U", "B8H", "UY1"])
def test_pseudouridine_uses_the_carbon_link_and_base_only_planes(code):
    from restraints.builder import pair_residue_from_pdb
    from restraints.phenix import PairResidue, generate_pair_restraints
    from restraints.residue_library import heterocycle_atom_names
    from restraints.stacking import _selection_for_base_plane

    record, = find_residue(load_residue_records(), code)
    assert record["Glycosidic atom"] == "C5"
    assert record["Backbone attachment atom"] == "C1'"
    assert record["N1"] == "N1" and record["C5"] == "C5"
    assert record["C7"] is None
    names = ["N1", "C2", "O2", "N3", "C4", "O4", "C5", "C6", "C1'", "H1'"]
    residue = Residue.Residue((" ", 1, " "), code, "")
    chain = Chain.Chain("A")
    chain.add(residue)
    for serial, atom_name in enumerate(names, 1):
        point = {"C5": (0, 0, 0), "C1'": (1.5, 0, 0), "H1'": (1.1, 0, 0)}.get(atom_name, (3, serial, 1))
        residue.add(Atom.Atom(atom_name, np.array(point, dtype=float), 0, 1, " ", atom_name, serial,
                              element=atom_name[0]))
    assert find_sugar_attachment_atom(residue, record).name == "C1'"
    assert np.allclose(glycosidic_vector(residue, record), [-1.5, 0, 0])
    assert "C1'" not in heterocycle_atom_names(record)
    mapped = pair_residue_from_pdb([record], residue)
    adenine_roles = ("C2", "N1", "C6", "N6", "C5", "C4", "N3", "N9", "C8", "N7")
    partner = PairResidue("B", "1", {a: a for a in adenine_roles}, "A")
    pair = generate_pair_restraints(mapped, partner)
    assert pair.count("    bond {") == 2
    assert "chain A and resid 1 and name O4" in pair and "chain A and resid 1 and name N3" in pair
    assert "name N1" in _selection_for_base_plane(mapped) and "name C5" in _selection_for_base_plane(mapped)
    assert "C1'" not in pair and "C1'" not in _selection_for_base_plane(mapped)
    # An absent or distant named partner cannot be replaced by a nearer hydrogen.
    assert find_sugar_attachment_atom(residue, record, max_bond_distance=1.2) is None
    residue.detach_child("C1'")
    assert find_sugar_attachment_atom(residue, record) is None


def test_legacy_standard_and_pna_attachments_retain_their_mapping():
    records = load_residue_records()
    for code, expected in (("DT", "N1"), ("DA", "N9")):
        rec, = find_residue(records, code)
        assert rec["Glycosidic atom"] == expected
        assert "Backbone attachment atom" not in rec
    structure = PDBParser(QUIET=True).get_structure("PNA", "examples/9L5Z.pdb")
    residue = next(r for r in structure.get_residues() if r.get_resname().strip() == "CPN")
    rec, = find_residue(records, "CPN")
    assert "Backbone attachment atom" not in rec
    assert find_sugar_attachment_atom(residue, rec) is not None
