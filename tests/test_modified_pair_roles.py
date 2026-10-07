"""Sheet-family pair geometry must use actual NARestraints atom-role mappings.

Pair lookup is unordered; GC/AT geometry roles are ordered. These tests use
the installed Ligands.xlsx rather than guessing a base category from its name.
No structural claim is made about every possible analogue or experimental pose.
"""
from __future__ import annotations

from functools import lru_cache

import pytest

from restraints.phenix import (
    GC_PARALLEL_C, GC_PARALLEL_G, PairResidue,
    atom_name, generate_pair_restraints,
)
from restraints.recipe_library import recipe_for
from restraints.residue_library import load_residue_records
from restraints.stacking import (
    _PLANE_ATOMS_BY_BASE_CLASS, _selection_for_base_plane,
)


# The first member occupies the G-like GC geometry role; the second occupies C.
# B:S is the original correct mapping. Z:P and K:X were reversed in 1.1.2.
GC_FAMILIES = (("B", "S"), ("P", "Z"), ("X", "K"))
G_ROLES = ("C2", "N1", "N2", "C6", "O6")
C_ROLES = ("C2", "O2", "N3", "C4", "N4")
D_ROLES = ("C2", "N1", "N2", "C6", "N6")
T_ROLES = ("C2", "N3", "O2", "O4")
_META = frozenset({
    "Ligand code", "Name", "Abbreviation", "Base Analog", "Phosphate",
    "Sugar Type", "SugarType", "Saenger", "Notes", "Ref", "Entries",
    "Function", "Source sheet", "Glycosidic atom",
})


@lru_cache(maxsize=1)
def _workbook():
    return tuple(load_residue_records())


def _representative(sheet: str, required: tuple[str, ...], *, code: str | None = None):
    """Find an explicitly mapped, role-complete *real* sheet record.

    If an entire sheet lacks the necessary contacts, a copied GC recipe is not
    science: fail the test and review that family rather than inventing atoms.
    """
    records = [
        row for row in _workbook()
        if row.get("Source sheet") == sheet and row.get("Base Analog") == sheet
        and (code is None or row.get("Ligand code") == code)
    ]
    assert records, f"Missing matching {sheet} workbook records" + (f" for {code}" if code else "")
    matches = [
        row for row in records
        if all(isinstance(row.get(role), str) and row[role].strip() for role in required)
    ]
    assert matches, f"{sheet} has no mapped workbook record with {required}"
    return matches[0]


def _pair_residue(sheet: str, chain: str, resid: str, required, *, code=None):
    record = _representative(sheet, required, code=code)
    atoms = {
        str(key): value.strip()
        for key, value in record.items()
        if key not in _META and isinstance(value, str) and value.strip()
    }
    return PairResidue(chain, resid, atoms, sheet)


@pytest.mark.parametrize("g_like,c_like", GC_FAMILIES)
def test_sheet_family_gc_roles_use_real_workbook_atoms(g_like, c_like):
    p = _pair_residue(g_like, "A", "12", G_ROLES, code="DP" if g_like == "P" else None)
    z = _pair_residue(c_like, "B", "4", C_ROLES, code="DZ" if c_like == "Z" else None)

    recipe = recipe_for(g_like, c_like)
    assert recipe is not None and recipe.name == "GC"
    assert recipe.role1_categories == frozenset((g_like,))
    assert recipe.role2_categories == frozenset((c_like,))

    text = generate_pair_restraints(p, z)
    assert text and text == generate_pair_restraints(z, p)
    assert text.count("distance_ideal = 2.8") == 3
    assert text.count("angle_ideal =") == 6

    for residue, role in (
        (p, "N1"), (p, "N2"), (p, "O6"),
        (z, "O2"), (z, "N3"), (z, "N4"),
    ):
        selection = f"chain {residue.chain} and resid {residue.resid} and name {atom_name(residue, role, recipe.name)}"
        assert selection in text

    assert _PLANE_ATOMS_BY_BASE_CLASS[g_like] == GC_PARALLEL_G
    assert _PLANE_ATOMS_BY_BASE_CLASS[c_like] == GC_PARALLEL_C
    assert _selection_for_base_plane(p)
    assert _selection_for_base_plane(z)


def test_actual_D_sheet_uses_separate_D_T_recipe_not_GC():
    d = _pair_residue("D", "A", "3", D_ROLES)
    # The partner is a normal thymine workbook entry, not a modified-base sheet.
    rows = [row for row in _workbook() if row.get("Source sheet") == "thymine"]
    matched = next((
        row for row in rows if all(
            isinstance(row.get(role), str) and row[role].strip() for role in T_ROLES
        )
    ), None)
    assert matched is not None, "thymine sheet lacks D:T partner mapping"
    atoms = {k: v.strip() for k, v in matched.items()
             if k not in _META and isinstance(v, str) and v.strip()}
    t = PairResidue("B", "4", atoms, "T")
    recipe = recipe_for("D", "T")
    assert recipe is not None and recipe.name == "D_T"
    assert recipe.role1_categories == frozenset({"D"})
    assert recipe.role2_categories == frozenset({"T"})
    text = generate_pair_restraints(d, t)
    assert text and text == generate_pair_restraints(t, d)
    assert text.count("distance_ideal = 2.8") == 3
    assert text.count("angle_ideal =") == 4


def test_only_configured_modified_families_have_recipes():
    # This prevents an accidental blanket GC or AT fallback and protects
    # the unreviewed D:A idea from being silently treated as D:T.
    assert recipe_for("D", "A") is None
    assert recipe_for("I", "C").name == "AT"
    assert recipe_for("B", "P") is None
