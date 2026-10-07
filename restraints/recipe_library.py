"""Explicit nucleic-acid base-pair recipe library.

Pair identity and restraint recipe are deliberately separate. This table is
scientific configuration: it is not inferred from atom names or guessed from
chemistry.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PairRecipe:
    """A named restraint recipe plus its two role categories."""

    name: str
    role1_categories: frozenset[str]
    role2_categories: frozenset[str]
    noncanonical: bool = False


# The order of role categories matters for recipes: AT expects an A-like
# residue followed by a T-like residue; GC expects a G-like residue followed
# by a C-like residue. Pair lookup itself remains order-independent.
PAIR_RECIPES: dict[frozenset[str], PairRecipe] = {
    frozenset(("A", "T")): PairRecipe("AT", frozenset(("A",)), frozenset(("T",))),
    frozenset(("G", "C")): PairRecipe("GC", frozenset(("G",)), frozenset(("C",))),
    frozenset(("D", "T")): PairRecipe("D_T", frozenset(("D",)), frozenset(("T",))),
    # Explicit sheet-family orientation. The GC engine's first role requests
    # guanine-like N1/N2/O6, and its second requests cytosine-like O2/N3/N4.
    # Pair identity is unordered; role assignment is not. The B:S ordering was
    # already correct. Z:P and K:X previously had their roles reversed.
    frozenset(("B", "S")): PairRecipe("GC", frozenset(("B",)), frozenset(("S",))),
    frozenset(("Z", "P")): PairRecipe("GC", frozenset(("P",)), frozenset(("Z",))),
    frozenset(("K", "X")): PairRecipe("GC", frozenset(("X",)), frozenset(("K",))),
    # D is 2,6-diaminopurine-like; D:T uses its dedicated three-contact
    # D_T geometry. Do not invent a D:A pair or coerce it through GC.
    frozenset(("I", "C")): PairRecipe("AT", frozenset(("I",)), frozenset(("C",))),
    # Explicitly supported non-canonical geometries. The guesser must
    # opt in before these recipes are considered.
    frozenset(("A", "G")): PairRecipe(
        "AG_IX", frozenset(("A",)), frozenset(("G",)), noncanonical=True
    ),
    frozenset(("G", "T")): PairRecipe(
        "GU_XXVIII", frozenset(("G",)), frozenset(("T",)), noncanonical=True
    ),
}


def recipe_for(category1: str, category2: str) -> PairRecipe | None:
    """Return the configured recipe for an unordered category pair."""
    return PAIR_RECIPES.get(frozenset((category1, category2)))
