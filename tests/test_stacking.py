from restraints.phenix import PairResidue
from restraints.stacking import StackingResidue, generate_chain_stacking_restraints


def _t_like(chain: str, resid: str, *, sulfur: bool = False) -> PairResidue:
    return PairResidue(
        chain,
        resid,
        {
            "C2": "C2",
            "O2": "O2",
            "N1": "N1",
            "N3": "N3",
            "C4": "C4",
            "O4": "S4" if sulfur else "O4",
            "C5": "C5",
            "C7": "C7",
            "C6": "C6",
        },
        "T",
    )


def test_canonical_neighbours_keep_phenix_stacking_pair():
    residues = [
        StackingResidue("A", "1", "DT", _t_like("A", "1")),
        StackingResidue("A", "2", "DT", _t_like("A", "2")),
    ]

    generic, manual, warnings = generate_chain_stacking_restraints(residues)

    assert generic.count("stacking_pair {") == 1
    assert "base1 = chain A and resid 1" in generic
    assert "base2 = chain A and resid 2" in generic
    assert manual == ()
    assert warnings == ()


def test_modified_residue_gets_explicit_stacking_on_both_sides():
    residues = [
        StackingResidue("A", "11", "DT", _t_like("A", "11")),
        StackingResidue("A", "12", "DE", _t_like("A", "12", sulfur=True)),
        StackingResidue("A", "13", "DT", _t_like("A", "13")),
        StackingResidue("A", "14", "DT", _t_like("A", "14")),
    ]

    generic, manual, warnings = generate_chain_stacking_restraints(residues)

    # A11-DE and DE-A13 are manual; only A13-A14 remains generic.
    assert generic.count("stacking_pair {") == 1
    assert "base1 = chain A and resid 13" in generic
    assert "base2 = chain A and resid 14" in generic
    assert len(manual) == 2
    assert all("parallelity {" in block for block in manual)
    assert all("sigma = 0.027" in block for block in manual)
    assert all("target_angle_deg = 0" in block for block in manual)
    assert all("resid 12" in block for block in manual)
    assert all("name S4" in block for block in manual)
    assert warnings == ()


def test_unmapped_modified_residue_falls_back_without_dropping_stack():
    residues = [
        StackingResidue("A", "1", "DT", _t_like("A", "1")),
        StackingResidue("A", "2", "NEW", None),
    ]

    generic, manual, warnings = generate_chain_stacking_restraints(residues)

    assert generic.count("stacking_pair {") == 1
    assert manual == ()
    assert len(warnings) == 1
    assert "falling back to Phenix stacking_pair" in warnings[0]
