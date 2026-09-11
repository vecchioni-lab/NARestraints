from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .phenix import (
    AT_PARALLEL_A,
    AT_PARALLEL_T,
    GC_PARALLEL_C,
    GC_PARALLEL_G,
    PairResidue,
    atom_name,
)


# Residue names that Phenix's nucleic-acid secondary-structure machinery
# recognizes directly. Everything else is treated as modified/noncanonical for
# stacking so NARestraints can supply the base planes explicitly.
_PHENIX_STANDARD_NA_CODES = {
    "A", "C", "G", "U",
    "DA", "DC", "DG", "DT",
}

# Base-plane atom templates follow the same role geometry used by the reviewed
# pair recipes. Modified residue atom names are resolved through the workbook
# mapping by atom_name(), so, for example, a canonical O4 role may select S4.
_PLANE_ATOMS_BY_BASE_CLASS = {
    "A": AT_PARALLEL_A,
    "I": AT_PARALLEL_A,
    "T": AT_PARALLEL_T,
    "G": GC_PARALLEL_G,
    "D": GC_PARALLEL_G,
    "B": GC_PARALLEL_G,
    "Z": GC_PARALLEL_G,
    "K": GC_PARALLEL_G,
    "C": GC_PARALLEL_C,
    "S": GC_PARALLEL_C,
    "P": GC_PARALLEL_C,
    "X": GC_PARALLEL_C,
}


@dataclass(frozen=True)
class StackingResidue:
    chain: str
    resid: str
    residue_name: str
    mapped: PairResidue | None = None

    @property
    def is_standard(self) -> bool:
        return self.residue_name.strip().upper() in _PHENIX_STANDARD_NA_CODES


def _selection_for_base_plane(residue: PairResidue) -> str:
    template = _PLANE_ATOMS_BY_BASE_CLASS.get(residue.base_class)
    if template is None:
        raise ValueError(
            f"No reviewed stacking-plane template for base class {residue.base_class!r}"
        )

    names: list[str] = []
    for canonical in template:
        try:
            actual = atom_name(residue, canonical)
        except ValueError:
            continue
        if actual not in names:
            names.append(actual)

    if len(names) < 3:
        raise ValueError(
            f"Need at least three mapped base-plane atoms for "
            f"{residue.chain}:{residue.resid} ({residue.base_class}); got {names!r}"
        )

    joined = " or ".join(f"name {name}" for name in names)
    return f"chain {residue.chain} and resid {residue.resid} and ({joined})"


def _generic_stacking_pair(first: StackingResidue, second: StackingResidue) -> str:
    return "\n".join(
        [
            "        stacking_pair {",
            f"          base1 = chain {first.chain} and resid {first.resid}",
            f"          base2 = chain {second.chain} and resid {second.resid}",
            "        }",
        ]
    )


def _manual_parallelity(first: PairResidue, second: PairResidue) -> str:
    # Match Phenix's stacking_pair defaults exactly: sigma 0.027 and target 0°.
    # The only difference is that NARestraints supplies the two atom planes
    # explicitly instead of asking Phenix to infer them from residue names.
    return "\n".join(
        [
            "    parallelity {",
            "      action = add",
            f"      atom_selection_1 = {_selection_for_base_plane(first)}",
            f"      atom_selection_2 = {_selection_for_base_plane(second)}",
            "      sigma = 0.027",
            "      target_angle_deg = 0",
            "    }",
        ]
    )


def generate_chain_stacking_restraints(
    residues: Sequence[StackingResidue],
) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    """Generate stacking for one chain without losing modified-base stacks.

    Returns ``(phenix_stacking_pairs, manual_parallelities, warnings)``.

    Canonical/canonical neighbours stay on Phenix's normal ``stacking_pair``
    path. If either residue is modified/noncanonical and both residues have
    reviewed workbook mappings, the stack is represented by an explicit
    geometry-restraint parallelity instead. If the modified residue cannot be
    mapped yet, retain the generic stacking_pair rather than silently dropping
    the physical relationship, and report a warning for the caller.
    """
    generic_blocks: list[str] = []
    manual_blocks: list[str] = []
    warnings: list[str] = []

    for first, second in zip(residues, residues[1:]):
        if first.chain != second.chain:
            continue

        if first.is_standard and second.is_standard:
            generic_blocks.append(_generic_stacking_pair(first, second))
            continue

        if first.mapped is not None and second.mapped is not None:
            try:
                manual_blocks.append(_manual_parallelity(first.mapped, second.mapped))
                continue
            except ValueError as exc:
                warnings.append(
                    f"Could not build explicit stacking for {first.chain}:{first.resid} "
                    f"({first.residue_name}) <-> {second.chain}:{second.resid} "
                    f"({second.residue_name}): {exc}. Falling back to Phenix stacking_pair."
                )
        else:
            missing = []
            if first.mapped is None:
                missing.append(f"{first.chain}:{first.resid} {first.residue_name}")
            if second.mapped is None:
                missing.append(f"{second.chain}:{second.resid} {second.residue_name}")
            warnings.append(
                "Could not map modified stacking residue(s) "
                + ", ".join(missing)
                + "; falling back to Phenix stacking_pair."
            )

        generic_blocks.append(_generic_stacking_pair(first, second))

    return (
        "\n\n".join(generic_blocks),
        tuple(manual_blocks),
        tuple(warnings),
    )
