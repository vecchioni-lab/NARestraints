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


# The order of role categories matters for recipes: AT expects an A-like
# residue followed by a T-like residue; GC expects a G-like residue followed
# by a C-like residue. Pair lookup itself remains order-independent.
PAIR_RECIPES: dict[frozenset[str], PairRecipe] = {
    frozenset(("A", "T")): PairRecipe("AT", frozenset(("A",)), frozenset(("T",))),
    frozenset(("G", "C")): PairRecipe("GC", frozenset(("G",)), frozenset(("C",))),
    frozenset(("D", "T")): PairRecipe("GC", frozenset(("D",)), frozenset(("T",))),
    frozenset(("B", "S")): PairRecipe("GC", frozenset(("B",)), frozenset(("S",))),
    frozenset(("Z", "P")): PairRecipe("GC", frozenset(("Z",)), frozenset(("P",))),
    frozenset(("K", "X")): PairRecipe("GC", frozenset(("K",)), frozenset(("X",))),
    frozenset(("I", "C")): PairRecipe("AT", frozenset(("I",)), frozenset(("C",))),
}


def recipe_for(category1: str, category2: str) -> PairRecipe | None:
    """Return the configured recipe for an unordered category pair."""
    return PAIR_RECIPES.get(frozenset((category1, category2)))
