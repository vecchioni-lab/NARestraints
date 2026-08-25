from __future__ import annotations

from pathlib import Path

from Bio.PDB import PDBParser, PDBIO

from .builder import record_for_residue
from .residue_library import load_residue_records


_METADATA_FIELDS = {
    "Ligand code", "Name", "Abbreviation", "Base Analog", "Phosphate",
    "Sugar Type", "SugarType", "Saenger", "Notes", "Ref", "Entries",
    "Function", "Source sheet", "Glycosidic atom",
}


def _element_from_atom_name(name: str) -> str:
    """Infer the element from a PDB atom name for the common nucleic-acid atoms."""
    name = name.strip().upper()
    if not name:
        return ""
    if name.startswith("CL"):
        return "CL"
    if name.startswith("BR"):
        return "BR"
    return name[0]


def find_atom_name_mismatches(pdb_filename: str | Path) -> tuple[list[tuple], list[str]]:
    """Return unambiguous atom-name fixes and fatal validation errors.

    A fix is (chain, resid, residue_name, old_atom_name, expected_atom_name).
    Only a unique same-element candidate is considered an automatic name fix.
    """
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("NARestraintsValidation", str(pdb_filename))
    records = load_residue_records()

    fixes: list[tuple] = []
    errors: list[str] = []

    for model in structure:
        for chain in model:
            for residue in chain.get_residues():
                try:
                    record = record_for_residue(records, residue)
                except ValueError:
                    # Unknown residue identity is a real problem for restraint
                    # generation; leave it to the normal builder to report.
                    continue

                for key, value in record.items():
                    if key in _METADATA_FIELDS or value is None or value == "/" or value == "":
                        continue

                    expected = str(value).strip()
                    if not expected:
                        continue

                    if residue.has_id(expected):
                        continue

                    element = _element_from_atom_name(expected)
                    candidates = [
                        atom
                        for atom in residue.get_atoms()
                        if (atom.element or _element_from_atom_name(atom.get_name())).strip().upper()
                        == element
                    ]

                    if len(candidates) == 1:
                        fixes.append(
                            (
                                chain.id,
                                str(residue.id[1]),
                                residue.get_resname().strip(),
                                candidates[0].get_name(),
                                expected,
                            )
                        )
                    elif len(candidates) == 0:
                        errors.append(
                            f"{chain.id}:{residue.id[1]} {residue.get_resname().strip()}: "
                            f"expected atom {expected}, but no {element} atom is present."
                        )
                    else:
                        names = ", ".join(atom.get_name() for atom in candidates)
                        errors.append(
                            f"{chain.id}:{residue.id[1]} {residue.get_resname().strip()}: "
                            f"expected atom {expected}, but found multiple {element} "
                            f"candidates ({names}); cannot resolve automatically."
                        )

    # Deduplicate repeated fixes caused by records containing the same mapping.
    fixes = list(dict.fromkeys(fixes))
    return fixes, errors


def create_fixed_pdb(
    pdb_filename: str | Path,
    fixes: list[tuple],
) -> Path:
    """Write a -fixed.pdb copy with only the requested atom-name changes."""
    source = Path(pdb_filename)
    output = source.with_name(f"{source.stem}-fixed{source.suffix}")

    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("NARestraintsFixed", str(source))

    by_residue = {}
    for chain, resid, residue_name, old_name, new_name in fixes:
        by_residue.setdefault((chain, resid), []).append((old_name, new_name))

    for model in structure:
        for chain in model:
            for residue in chain.get_residues():
                key = (chain.id, str(residue.id[1]))
                for old_name, new_name in by_residue.get(key, []):
                    if residue.has_id(old_name) and not residue.has_id(new_name):
                        atom = residue[old_name]
                        atom.id = new_name
                        atom.fullname = f"{new_name:>4}"

    io = PDBIO()
    io.set_structure(structure)
    io.save(str(output))
    return output


def validate_and_fix_pdb(pdb_filename: str | Path) -> Path:
    """Validate atom names and interactively create a fixed PDB if safe."""
    fixes, errors = find_atom_name_mismatches(pdb_filename)

    if errors:
        print("ERROR: PDB validation found unresolved atom-name problems:")
        for error in errors:
            print(f"  {error}")
        raise ValueError("PDB validation failed; no fixed PDB was created.")

    if not fixes:
        return Path(pdb_filename)

    print("Atom-name mismatches can be fixed unambiguously:")
    for chain, resid, residue_name, old_name, new_name in fixes:
        print(
            f"  {chain}:{resid} {residue_name}: "
            f"{old_name} -> {new_name}"
        )

    answer = input("Create fixed PDB and continue? [Y/n] ").strip().lower()
    if answer not in {"", "y", "yes"}:
        raise ValueError("PDB validation requires atom-name fixes; generation cancelled.")

    fixed = create_fixed_pdb(pdb_filename, fixes)
    print(f"Using fixed PDB: {fixed}")
    return fixed
