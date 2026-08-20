from restraints.phenix import PairResidue, generate_pair_restraints


def residue(chain, resid, base, atoms):
    return PairResidue(chain, str(resid), atoms, base)


def standard_atoms(base):
    if base in {"A", "G", "D", "B", "Z", "K"}:
        atoms = {
            "C2": "C2", "C6": "C6", "N1": "N1", "C5": "C5", "C4": "C4",
            "N3": "N3", "N9": "N9", "C8": "C8", "N7": "N7",
        }
        if base == "A":
            atoms["N6"] = "N6"
        else:
            atoms["N2"] = "N2"
            atoms["O6"] = "O6"
        return atoms
    return {
        "C2": "C2", "O2": "O2", "N1": "N1", "N3": "N3",
        "C4": "C4", "C5": "C5", "C6": "C6",
        "O4": "O4", "N4": "N4", "C7": "C7",
    }


def test_at_recipe_contains_matlab_geometry():
    a = residue("A", 1, "A", standard_atoms("A"))
    t = residue("B", 2, "T", standard_atoms("T"))
    text = generate_pair_restraints(a, t)
    assert text is not None
    assert "angle_ideal = 116.2" in text
    assert "angle_ideal = 115.6" in text
    assert "distance_ideal = 2.8" in text
    assert "parallelity {" in text
    assert "planarity {" in text


def test_gc_recipe_contains_matlab_geometry():
    g = residue("A", 1, "G", standard_atoms("G"))
    c = residue("B", 2, "C", standard_atoms("C"))
    text = generate_pair_restraints(g, c)
    assert text is not None
    assert "angle_ideal = 122.2" in text
    assert "angle_ideal = 122.8" in text
    assert text.count("distance_ideal = 2.8") == 3
    assert "parallelity {" in text
    assert "planarity {" in text


def test_special_category_pairs_use_configured_recipe():
    d = residue("A", 1, "D", standard_atoms("D"))
    t = residue("B", 2, "T", standard_atoms("T"))
    text = generate_pair_restraints(d, t)
    assert text is not None
    assert text.count("distance_ideal = 2.8") == 3


def test_unsupported_pair_returns_none():
    g = residue("A", 1, "G", standard_atoms("G"))
    t = residue("B", 2, "T", standard_atoms("T"))
    assert generate_pair_restraints(g, t) is None


def test_d_t_gc_recipe_maps_c_role_n4_to_t_o4():
    d = PairResidue("A", "3", {
        "C2": "C2", "N1": "N1", "N2": "N2", "C4": "C4",
        "C5": "C5", "C6": "C6", "O6": "O6", "N3": "N3",
        "N9": "N9", "C8": "C8", "N7": "N7",
    }, "D")
    t = PairResidue("B", "4", {
        "N1": "N1", "C2": "C2", "O2": "O2", "N3": "N3",
        "C4": "C4", "O4": "O4", "C5": "C5", "C6": "C6",
        "C7": "C7",
    }, "T")
    block = generate_pair_restraints(d, t)
    assert block is not None
    assert "chain B and resid 4 and name O4" in block
    assert "chain B and resid 4 and name N4" not in block
