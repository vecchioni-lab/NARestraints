#!/usr/bin/env python3
"""
Mirror D/L nucleic-acid PDBs using the residue/atom definitions in
data/Ligands.xlsx.

Geometry:
    X -> -X

Residue mappings:
    DNA:
        DA <-> 0DA
        DG <-> 0DG
        DC <-> 0DC
        DT <-> 0DT

    RNA:
        A <-> 0A
        G <-> 0G
        C <-> 0C
        U <-> 0U

Atom names are taken directly from Ligands.xlsx. Nothing is inferred.

For each residue, ALL atom names are mapped first while the original residue
name is still present. Only after that is the residue name changed. This is
important for mappings such as DA <-> 0DA, where the atom names differ.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from Bio.PDB import PDBIO, PDBParser, Select
from openpyxl import load_workbook


DNA_PAIRS = {
    "DA": "0DA",
    "DG": "0DG",
    "DC": "0DC",
    "DT": "0DT",
}

RNA_PAIRS = {
    "A": "0A",
    "G": "0G",
    "C": "0C",
    "U": "0U",
}


class KeepAll(Select):
    def accept_atom(self, atom):
        return True


def normalise_code(value):
    if value is None:
        return ""
    return str(value).strip()


def load_ligand_definitions(xlsx_path):
    """
    Read atom definitions from Ligands.xlsx.

    Returns:
        {
            residue_code: [atom_name, atom_name, ...]
        }

    The spreadsheet is the authoritative source for atom naming.
    """

    wb = load_workbook(
        xlsx_path,
        read_only=True,
        data_only=True,
    )

    definitions = {}

    metadata_columns = {
        "Name",
        "Abbreviation",
        "Base Analog",
        "Phosphate",
        "Sugar Type",
        "Saenger",
        "Notes",
        "Ref",
        "Entries",
        "Function",
        "C7-mod",
        "C5-mod",
    }

    for ws in wb.worksheets:

        rows = ws.iter_rows(values_only=True)

        try:
            headers = list(next(rows))
        except StopIteration:
            continue

        if "Ligand code" not in headers:
            continue

        code_index = headers.index("Ligand code")

        atom_indices = [
            i
            for i, header in enumerate(headers)
            if (
                header is not None
                and header != "Ligand code"
                and header not in metadata_columns
            )
        ]

        for row in rows:

            if code_index >= len(row):
                continue

            code = normalise_code(row[code_index])

            if not code:
                continue

            atoms = []

            for i in atom_indices:

                if i >= len(row):
                    continue

                value = row[i]

                if value is None:
                    continue

                value = str(value).strip()

                if not value or value == "/":
                    continue

                atoms.append(value)

            if atoms:
                definitions.setdefault(code, atoms)

    wb.close()

    return definitions


def build_atom_maps(xlsx_path):
    """
    Construct explicit atom-name mappings for each D/L residue pair.

    Corresponding atoms are taken in the order defined by Ligands.xlsx.
    """

    definitions = load_ligand_definitions(xlsx_path)

    atom_maps = {}

    all_pairs = (
        DNA_PAIRS,
        RNA_PAIRS,
    )

    for pair_group in all_pairs:

        for d_residue, l_residue in pair_group.items():

            if d_residue not in definitions:
                raise ValueError(
                    f"Missing residue definition in Ligands.xlsx: "
                    f"{d_residue}"
                )

            if l_residue not in definitions:
                raise ValueError(
                    f"Missing residue definition in Ligands.xlsx: "
                    f"{l_residue}"
                )

            d_atoms = definitions[d_residue]
            l_atoms = definitions[l_residue]

            if len(d_atoms) != len(l_atoms):
                raise ValueError(
                    f"Atom-definition length mismatch for "
                    f"{d_residue} <-> {l_residue}: "
                    f"{len(d_atoms)} vs {len(l_atoms)}"
                )

            forward_map = dict(zip(d_atoms, l_atoms))
            reverse_map = dict(zip(l_atoms, d_atoms))

            atom_maps[(d_residue, l_residue)] = forward_map
            atom_maps[(l_residue, d_residue)] = reverse_map

    return atom_maps


def find_residue_pair(resname):
    """
    Return:

        (current_residue_name, target_residue_name)

    or None if this is not a residue we mirror.
    """

    # DNA: D -> L
    if resname in DNA_PAIRS:
        return (
            resname,
            DNA_PAIRS[resname],
        )

    # DNA: L -> D
    for d_residue, l_residue in DNA_PAIRS.items():

        if resname == l_residue:
            return (
                resname,
                d_residue,
            )

    # RNA: normal -> 0*
    if resname in RNA_PAIRS:
        return (
            resname,
            RNA_PAIRS[resname],
        )

    # RNA: 0* -> normal
    for normal_residue, modified_residue in RNA_PAIRS.items():

        if resname == modified_residue:
            return (
                resname,
                normal_residue,
            )

    return None


def mirror_coordinates(atom):
    """
    Exact coordinate transformation from the MATLAB implementation:

        X -> -X
    """

    x, y, z = atom.get_coord()

    atom.set_coord(
        (
            -x,
            y,
            z,
        )
    )


def transform_residue(residue, atom_maps):
    """
    Mirror one residue.

    Crucially, the residue name is NOT changed until every atom has been
    mapped. This prevents DA -> 0DA mappings from becoming DA -> DA halfway
    through the residue.
    """

    source_resname = residue.get_resname().strip()

    pair = find_residue_pair(source_resname)

    # Non-D/L nucleic-acid or other residue:
    # still mirror coordinates, but don't rename anything.
    if pair is None:

        for atom in residue:
            mirror_coordinates(atom)

        return

    target_resname = pair[1]

    atom_map = atom_maps[pair]

    # ------------------------------------------------------------
    # First map every atom while the residue still has its original
    # identity.
    # ------------------------------------------------------------

    for atom in residue:

        source_atom_name = atom.get_name().strip()

        mirror_coordinates(atom)

        if source_atom_name in atom_map:
            target_atom_name = atom_map[source_atom_name]

            atom.name = target_atom_name
            atom.fullname = f"{target_atom_name:>4s}"

    # ------------------------------------------------------------
    # Only after ALL atoms have been renamed do we change the
    # residue name.
    # ------------------------------------------------------------

    residue.resname = target_resname


def mirror_pdb(
    input_pdb,
    output_pdb=None,
    ligands_xlsx=None,
):
    """
    Mirror a PDB and write the transformed structure.
    """

    input_pdb = Path(input_pdb)

    if output_pdb is None:

        output_pdb = (
            input_pdb.parent
            / f"{input_pdb.stem}_mirror.pdb"
        )

    else:

        output_pdb = Path(output_pdb)

    # Default spreadsheet location:
    #
    # NARestraints/
    #   data/
    #     Ligands.xlsx
    #
    # script:
    #
    # NARestraints/
    #   restraints/
    #     mirror_pdb.py
    #
    if ligands_xlsx is None:

        ligands_xlsx = (
            Path(__file__).resolve().parent.parent
            / "data"
            / "Ligands.xlsx"
        )

    else:

        ligands_xlsx = Path(ligands_xlsx)

    if not ligands_xlsx.exists():

        raise FileNotFoundError(
            f"Ligands spreadsheet not found: "
            f"{ligands_xlsx}"
        )

    atom_maps = build_atom_maps(
        ligands_xlsx
    )

    parser = PDBParser(
        QUIET=True
    )

    structure = parser.get_structure(
        "mirror",
        str(input_pdb),
    )

    for model in structure:

        for chain in model:

            for residue in chain:

                transform_residue(
                    residue,
                    atom_maps,
                )

    io = PDBIO()

    io.set_structure(
        structure
    )

    io.save(
        str(output_pdb),
        select=KeepAll(),
    )

    return output_pdb


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Mirror a D/L nucleic-acid PDB using "
            "the atom definitions in data/Ligands.xlsx."
        )
    )

    parser.add_argument(
        "pdb",
        help="Input PDB file",
    )

    parser.add_argument(
        "-o",
        "--output",
        help=(
            "Output PDB file "
            "(default: <input>_mirror.pdb)"
        ),
    )

    parser.add_argument(
        "--ligands",
        help=(
            "Path to Ligands.xlsx "
            "(default: data/Ligands.xlsx)"
        ),
    )

    args = parser.parse_args()

    output = mirror_pdb(
        args.pdb,
        args.output,
        args.ligands,
    )

    print(
        f"Wrote {output}"
    )


if __name__ == "__main__":
    main()