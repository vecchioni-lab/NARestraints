
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from Bio.PDB import PDBParser

from .base_pairs import BasePairStretch
from .phenix import PairResidue, generate_pair_restraints, generate_stacking_restraints, write_phil
from .recipe_library import recipe_for
from .residue_library import find_residue, load_residue_records


_PAIR_CATEGORIES = {"A", "T", "G", "C", "D", "B", "S", "Z", "P", "K", "X", "I"}


def _record_score(record: dict, residue) -> int:
    """Prefer the residue-library mapping that actually matches the PDB atoms."""
    score = 0
    for key, value in record.items():
        if key in {
            "Ligand code", "Name", "Abbreviation", "Base Analog", "Phosphate",
            "Sugar Type", "SugarType", "Saenger", "Notes", "Ref", "Entries",
            "Function", "Source sheet", "Glycosidic atom",
        }:
            continue
        if value is not None and value != "" and residue.has_id(str(value).strip()):
            score += 1
    return score


def record_for_residue(records: list[dict], residue) -> dict:
    code = residue.get_resname().strip()
    matches = find_residue(records, code)
    if not matches:
        raise ValueError(
            f"Residue {code!r} is not present in the residue library."
        )
    return max(matches, key=lambda record: _record_score(record, residue))


def pair_residue_from_pdb(records: list[dict], residue) -> PairResidue:
    record = record_for_residue(records, residue)
    base_class = record.get("Base Analog")

    if base_class not in _PAIR_CATEGORIES:
        raise ValueError(
            f"{residue.get_resname().strip()} maps to unsupported Base Analog "
            f"{base_class!r}. Add it to the recipe/category configuration first."
        )

    atoms = {}
    for key, value in record.items():
        if key in {
            "Ligand code", "Name", "Abbreviation", "Base Analog", "Phosphate",
            "Sugar Type", "SugarType", "Saenger", "Notes", "Ref", "Entries",
            "Function", "Source sheet", "Glycosidic atom",
        }:
            continue
        if value is not None and value != "" and residue.has_id(str(value).strip()):
            atoms[key] = str(value).strip()

    return PairResidue(
        chain=residue.get_parent().get_id(),
        resid=str(residue.id[1]),
        atoms=atoms,
        base_class=base_class,
    )


def _get_residue(structure, chain: str, resid: str):
    model = next(structure.get_models())
    chain_obj = model[chain]
    # PDB insertion codes are retained if present; current input format is integer resid.
    for residue in chain_obj.get_residues():
        if str(residue.id[1]) == str(resid):
            return residue
    raise ValueError(f"Could not find {chain}:{resid} in the PDB.")


def build_phil_from_pdb(
    pdb_filename: str | Path,
    stretches: Iterable[BasePairStretch],
    output_filename: str | Path,
    *,
    parallels: bool = True,
    planes: bool = True,
    include_stacking: bool = True,
) -> None:
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("NARestraints", str(pdb_filename))
    records = load_residue_records("data/Ligands.xlsx")

    pair_blocks: list[str] = []
    all_chain_residues: list[PairResidue] = []

    for stretch in stretches:
        for pair in stretch.pairs():
            r1 = _get_residue(structure, pair.base1.chain, pair.base1.resid)
            r2 = _get_residue(structure, pair.base2.chain, pair.base2.resid)

            p1 = pair_residue_from_pdb(records, r1)
            p2 = pair_residue_from_pdb(records, r2)

            recipe = recipe_for(p1.base_class, p2.base_class)
            block = generate_pair_restraints(
                p1,
                p2,
                parallels=parallels,
                planes=planes,
            )
            if block is None:
                print(
                    "WARNING: No restraint recipe for pair "
                    f"{p1.chain}:{p1.resid} ({p1.base_class}) <-> "
                    f"{p2.chain}:{p2.resid} ({p2.base_class}); "
                    "skipping pair-specific restraints."
                )
                continue
            pair_blocks.append(block)

        stacking_block = ""
    if include_stacking:
        # Match the MATLAB behavior: stacking is generated for consecutive
        # residues in each PDB chain, independently of selected base pairs.
        for model in structure:
            for chain in model:
                residues = list(chain.get_residues())

                stacking_residues = [
                    (chain.id, str(residue.id[1]))
                    for residue in residues
                ]

                if len(stacking_residues) >= 2:
                    block = generate_stacking_restraints(stacking_residues)
                    if block:
                        stacking_block += (
                            "\n\n" if stacking_block else ""
                        ) + block

    write_phil(output_filename, pair_blocks, stacking_block)