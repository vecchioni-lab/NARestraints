"""A chemical atom name and the role it plays toward adenine are distinct."""
from pathlib import Path
import re

from Bio.PDB import PDBParser
import pytest

from restraints.builder import pair_residue_from_pdb
from restraints.guesser import _candidate_score
from restraints.phenix import generate_pair_restraints
from restraints.recipe_library import recipe_for
from restraints.residue_library import find_residue, load_residue_records


def selections(text, kind):
    groups = re.findall(r"^    " + kind + r" \{\n(.*?)^    \}", text, re.M | re.S)
    return [re.findall(r"atom_selection_\d+ = (.+)", block) for block in groups]


def test_canonical_pair_uses_the_measured_edge_in_both_chain_orders():
    path = Path(__file__).parent / "fixtures" / "6i1v-canonical-pairs.pdb"
    model = PDBParser(QUIET=True).get_structure("6I1V", path)[0]
    records = load_residue_records()
    for pyr, adenine, oxygen in ((model["A"][("H_PSU",5," ")], model["B"][14], "O2"),
                                 (model["B"][16], model["A"][3], "O4")):
        p, a = (pair_residue_from_pdb(records, res) for res in (pyr, adenine))
        correct = p.chain, p.resid, oxygen
        acceptor = "chain %s and resid %s and name %s" % correct
        donor = f"chain {a.chain} and resid {a.resid} and name N6"
        first = generate_pair_restraints(p, a)
        assert first == generate_pair_restraints(a, p)
        assert [acceptor, donor] in selections(first, "bond")
        assert any(row[-1] == acceptor for row in selections(first, "angle"))
        result = _candidate_score(pyr, adenine, p, a, recipe_for("T", "A"), allow_bad_geometry=True)
        assert result is not None
        assert result.bond_distances[1] == pytest.approx(float(pyr[oxygen] - adenine["N6"]), abs=1e-5)
        assert 2.8 < result.bond_distances[1] < 3.1
        opposite = "O4" if oxygen == "O2" else "O2"
        assert float(pyr[opposite] - adenine["N6"]) > 5.0
        # Both physical oxygens retain their ordinary plane membership.
        parallel = selections(first, "parallelity")[0][0]
        assert parallel.count("name O2") == parallel.count("name O4") == 1


@pytest.mark.parametrize("code", ["PSU", "B8H", "P2U", "UY1"])
def test_reviewed_pseudouridine_records_declare_the_same_canonical_acceptor(code):
    record, = find_residue(load_residue_records(), code)
    assert record["A:T acceptor role"] == "O2"
    assert record["O2"] == "O2" and record["O4"] == "O4"
    assert record["Glycosidic atom"] == "C5" and record["Backbone attachment atom"] == "C1'"


def test_missing_declared_acceptor_cannot_fall_back_to_the_other_carbonyl():
    path = Path(__file__).parent / "fixtures" / "6i1v-canonical-pairs.pdb"
    model = PDBParser(QUIET=True).get_structure("6I1V", path)[0]
    records = load_residue_records()
    pyr, adenine = model["A"][("H_PSU",5," ")], model["B"][14]
    pyr.detach_child("O2")
    p, a = (pair_residue_from_pdb(records, res) for res in (pyr, adenine))
    with pytest.raises(ValueError, match="O2"):
        generate_pair_restraints(p, a)
    assert _candidate_score(pyr, adenine, p, a, recipe_for("T","A"), allow_bad_geometry=True) is None


@pytest.mark.parametrize("category,role", [("A", "O2"), ("T", "unmapped"), ("T", 2)])
def test_mistyped_acceptor_in_explicit_workbook_requires_review(category, role):
    path = Path(__file__).parent / "fixtures" / "6i1v-canonical-pairs.pdb"
    pyr = PDBParser(QUIET=True).get_structure("6I1V", path)[0]["A"][("H_PSU", 5, " ")]
    record, = find_residue(load_residue_records(), "PSU")
    record.update({"Base Analog": category, "A:T acceptor role": role})
    with pytest.raises(ValueError, match="Invalid A:T acceptor role"):
        pair_residue_from_pdb([record], pyr)
