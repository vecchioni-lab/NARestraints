"""Basic DNA geometry tools for restraints."""

import numpy as np
from restraints.residue_library import find_residue
from restraints.residue_library import heterocycle_atom_names

def distance(point_a, point_b):
    """Return the distance in Å between two 3D coordinates."""
    point_a = np.array(point_a, dtype=float)
    point_b = np.array(point_b, dtype=float)

    return np.linalg.norm(point_a - point_b)

def midpoint(point_a, point_b):
    """Return the midpoint between two 3D coordinates."""
    point_a = np.array(point_a, dtype=float)
    point_b = np.array(point_b, dtype=float)

    return (point_a + point_b) / 2

def recognized_residues(structure, residue_records):
    """Return residues whose PDB residue code exists in the restraints library."""
    recognized = []

    for residue in structure.get_residues():
        code = residue.get_resname().strip()

        if find_residue(residue_records, code):
            recognized.append(residue)

    return recognized

def canonical_atom_coordinate(residue, record, canonical_position):
    """Return coordinates for a canonical base position in a residue."""
    actual_atom_name = record.get(canonical_position)

    if actual_atom_name is None:
        return None

    if actual_atom_name not in residue:
        return None

    return residue[actual_atom_name].coord

def glycosidic_vector(residue, record):
    """Return the vector from the backbone attachment atom to the heterocycle."""
    attachment = find_sugar_attachment_atom(residue, record)

    if attachment is None:
        return None

    gly_name = record.get("Glycosidic atom")

    if gly_name is None or gly_name not in residue:
        return None

    gly_atom = residue[gly_name]

    return gly_atom.coord - attachment.coord

def find_sugar_attachment_atom(residue, record, max_bond_distance=1.8):
    """Find the non-heterocycle atom bonded to the glycosidic atom."""
    gly_name = record.get("Glycosidic atom")

    if gly_name is None or gly_name not in residue:
        return None

    gly_atom = residue[gly_name]
    heterocycle_atoms = heterocycle_atom_names(record)

    candidates = []

    for atom in residue.get_atoms():
        if atom.get_name() in heterocycle_atoms:
            continue

        distance = np.linalg.norm(atom.coord - gly_atom.coord)

        if distance <= max_bond_distance:
            candidates.append((distance, atom))

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]