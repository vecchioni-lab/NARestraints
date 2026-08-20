from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
from Bio.PDB import PDBParser

from .builder import pair_residue_from_pdb
from .phenix import (
    AT_ANGLE_RESTRAINTS,
    AT_BONDS,
    AT_PARALLEL_A,
    AT_PARALLEL_T,
    GC_ANGLE_RESTRAINTS,
    GC_BONDS,
    GC_PARALLEL_C,
    GC_PARALLEL_G,
    DT_ANGLE_RESTRAINTS,
    DT_BONDS,
    PairResidue,
    atom_name,
)
from .recipe_library import recipe_for
from .validator import validate_and_fix_pdb
from .residue_library import load_residue_records


# Deliberately forgiving because this is intended for low-resolution models.
SEARCH_RADIUS = 8.0
BOND_SOFT_SIGMA = 0.40
MAX_PLANE_ANGLE = 25.0
MIN_SCORE = 45.0
MIN_RUN_SCORE = 35.0


@dataclass(frozen=True)
class Candidate:
    first: PairResidue
    second: PairResidue
    recipe: str
    score: float
    bond_distances: tuple[float, ...]
    angle_errors: tuple[float, ...]
    plane_angle: float


def _template(recipe_name: str):
    if recipe_name == "AT":
        return AT_ANGLE_RESTRAINTS, AT_BONDS, AT_PARALLEL_A, AT_PARALLEL_T
    if recipe_name == "D_T":
        return DT_ANGLE_RESTRAINTS, DT_BONDS, GC_PARALLEL_G, GC_PARALLEL_C
    return GC_ANGLE_RESTRAINTS, GC_BONDS, GC_PARALLEL_G, GC_PARALLEL_C


def _role_residues(first: PairResidue, second: PairResidue, recipe):
    if (
        first.base_class in recipe.role1_categories
        and second.base_class in recipe.role2_categories
    ):
        return first, second
    if (
        second.base_class in recipe.role1_categories
        and first.base_class in recipe.role2_categories
    ):
        return second, first
    return None


def _side_for_token(token: str, recipe_name: str) -> str:
    role = token.split(".", 1)[0]

    if recipe_name == "AT":
        return "left" if role == "A" else "right"

    if recipe_name == "D_T":
        return "left" if role == "D" else "right"

    # GC-like recipes use G-like geometry for recipe role 1 and
    # C-like geometry for recipe role 2, even for B:S, Z:P, K:X, etc.
    return "left" if role == "G" else "right"


def _atom_coord(residue, pair_residue: PairResidue, canonical: str, recipe_name: str):
    name = atom_name(pair_residue, canonical, recipe_name)
    return np.asarray(residue[name].coord, dtype=float)


def _angle(a, b, c) -> float:
    v1 = a - b
    v2 = c - b
    denom = np.linalg.norm(v1) * np.linalg.norm(v2)
    if denom == 0:
        return 180.0
    x = np.clip(np.dot(v1, v2) / denom, -1.0, 1.0)
    return math.degrees(math.acos(x))


def _plane(residue, pair_residue: PairResidue, canonical_names, recipe_name):
    points = []

    for canonical in canonical_names:
        try:
            points.append(
                _atom_coord(residue, pair_residue, canonical, recipe_name)
            )
        except (KeyError, ValueError):
            continue

    if len(points) < 3:
        return None

    points = np.asarray(points)
    center = points.mean(axis=0)
    _, _, vh = np.linalg.svd(points - center)
    normal = vh[-1]
    normal /= np.linalg.norm(normal)

    return center, normal


def _plane_angle(plane1, plane2) -> float:
    x = abs(float(np.dot(plane1[1], plane2[1])))
    return math.degrees(math.acos(np.clip(x, -1.0, 1.0)))


def _candidate_score(
    r1,
    r2,
    p1: PairResidue,
    p2: PairResidue,
    recipe,
) -> Candidate | None:
    roles = _role_residues(p1, p2, recipe)
    if roles is None:
        return None

    left_p, right_p = roles
    left_r, right_r = (r1, r2) if roles == (p1, p2) else (r2, r1)

    angles, bonds, left_plane_atoms, right_plane_atoms = _template(recipe.name)

    bond_distances = []

    for a1, a2, ideal, _sigma in bonds:
        role1, atom1 = a1.split(".", 1)
        role2, atom2 = a2.split(".", 1)

        side1 = _side_for_token(a1, recipe.name)
        side2 = _side_for_token(a2, recipe.name)

        try:
            c1 = _atom_coord(
                left_r if side1 == "left" else right_r,
                left_p if side1 == "left" else right_p,
                atom1,
                recipe.name,
            )
            c2 = _atom_coord(
                left_r if side2 == "left" else right_r,
                left_p if side2 == "left" else right_p,
                atom2,
                recipe.name,
            )
        except (KeyError, ValueError):
            return None

        bond_distances.append(float(np.linalg.norm(c1 - c2)))

    angle_errors = []

    for a1, a2, a3, ideal, _sigma in angles:
        coords = []

        for token in (a1, a2, a3):
            atom = token.split(".", 1)[1]
            side = _side_for_token(token, recipe.name)

            try:
                coords.append(
                    _atom_coord(
                        left_r if side == "left" else right_r,
                        left_p if side == "left" else right_p,
                        atom,
                        recipe.name,
                    )
                )
            except (KeyError, ValueError):
                return None

        angle_errors.append(abs(_angle(*coords) - ideal))

    left_plane = _plane(
        left_r, left_p, left_plane_atoms, recipe.name
    )
    right_plane = _plane(
        right_r, right_p, right_plane_atoms, recipe.name
    )

    if left_plane is None or right_plane is None:
        return None

    plane_angle = _plane_angle(left_plane, right_plane)
    center_distance = float(
        np.linalg.norm(left_plane[0] - right_plane[0])
    )

    if center_distance > SEARCH_RADIUS or plane_angle > MAX_PLANE_ANGLE:
        return None

    bond_score = sum(
        math.exp(-0.5 * ((d - ideal) / BOND_SOFT_SIGMA) ** 2)
        for d, (_, _, ideal, _) in zip(bond_distances, bonds)
    ) / len(bonds)

    angle_score = sum(
        math.exp(-0.5 * (error / 12.0) ** 2)
        for error in angle_errors
    ) / len(angle_errors)

    plane_score = math.exp(
        -0.5 * (plane_angle / 12.0) ** 2
    )

    center_score = math.exp(
        -0.5 * ((center_distance - 4.5) / 1.5) ** 2
    )

    score = 100.0 * (
        0.50 * bond_score
        + 0.25 * angle_score
        + 0.15 * plane_score
        + 0.10 * center_score
    )

    return Candidate(
        first=p1,
        second=p2,
        recipe=recipe.name,
        score=score,
        bond_distances=tuple(bond_distances),
        angle_errors=tuple(angle_errors),
        plane_angle=plane_angle,
    )


def _compatible_candidates(residues):
    for i, (r1, p1) in enumerate(residues):
        for r2, p2 in residues[i + 1:]:
            # Adjacent residues on the same chain are stacking neighbors,
            # not candidates for base pairing.
            if (
                r1.get_parent().id == r2.get_parent().id
                and abs(r1.id[1] - r2.id[1]) <= 1
            ):
                continue

            recipe = recipe_for(p1.base_class, p2.base_class)
            if recipe is None:
                continue

            candidate = _candidate_score(
                r1, r2, p1, p2, recipe
            )

            if candidate is not None:
                yield candidate


def _run_key(candidate: Candidate):
    try:
        a = int(candidate.first.resid)
        b = int(candidate.second.resid)
    except ValueError:
        return None
    return (
        candidate.first.chain,
        candidate.second.chain,
        a,
        b,
    )


def _can_extend(left: Candidate, right: Candidate) -> bool:
    """Whether right continues left on antiparallel tracks."""
    if (
        left.first.chain != right.first.chain
        or left.second.chain != right.second.chain
    ):
        return False
    try:
        da = int(right.first.resid) - int(left.first.resid)
        db = int(right.second.resid) - int(left.second.resid)
    except ValueError:
        return False
    return da == 1 and db == -1


def _build_runs(candidates: list[Candidate]) -> list[list[Candidate]]:
    """Build contiguous antiparallel runs from plausible candidates."""
    by_key = {}
    for c in candidates:
        key = _run_key(c)
        if key is not None:
            by_key[key] = c

    runs = []
    used = set()

    for c in sorted(candidates, key=lambda x: x.score, reverse=True):
        key = _run_key(c)
        if key is None or key in used:
            continue

        run = [c]
        used.add(key)

        # Extend forward.
        current = c
        while True:
            try:
                a = int(current.first.resid)
                b = int(current.second.resid)
            except ValueError:
                break

            next_key = (
                current.first.chain,
                current.second.chain,
                a + 1,
                b - 1,
            )
            nxt = by_key.get(next_key)
            if nxt is None or next_key in used:
                break
            run.append(nxt)
            used.add(next_key)
            current = nxt

        # Extend backward.
        current = c
        backwards = []
        while True:
            try:
                a = int(current.first.resid)
                b = int(current.second.resid)
            except ValueError:
                break

            prev_key = (
                current.first.chain,
                current.second.chain,
                a - 1,
                b + 1,
            )
            prv = by_key.get(prev_key)
            if prv is None or prev_key in used:
                break
            backwards.append(prv)
            used.add(prev_key)
            current = prv

        run = list(reversed(backwards)) + run
        runs.append(run)

    return runs


def _run_score(run: list[Candidate]) -> float:
    if not run:
        return 0.0

    # Continuous runs are much stronger evidence than isolated pairs.
    score = sum(c.score for c in run) / len(run)
    score += 10.0 * max(0, len(run) - 1)
    score += 5.0 * max(0, len(run) - 2)
    return score


def _infer_run_extensions(
    run: list[Candidate],
    residue_lookup: dict[tuple[str, int], tuple[object, PairResidue]],
):
    """
    Test one-residue extensions at both ends of a convincing run.

    We deliberately allow a weaker geometric score here: the existing run
    supplies structural evidence that an ugly low-resolution pair may belong.
    """
    additions = []
    messages = []

    if not run:
        return additions, messages

    ends = [
        (-1, +1, -1, "forward"),
        (0, -1, +1, "backward"),
    ]

    for index, da, db, direction in ends:
        edge = run[index]

        try:
            a = int(edge.first.resid) + da
            b = int(edge.second.resid) + db
        except ValueError:
            continue

        key = (
            edge.first.chain,
            a,
            edge.second.chain,
            b,
        )

        if (
            (edge.first.chain, a) not in residue_lookup
            or (edge.second.chain, b) not in residue_lookup
        ):
            messages.append(
                f"RUN EDGE: {edge.first.chain}{a} <-> "
                f"{edge.second.chain}{b} is outside the model"
            )
            continue

        r1, p1 = residue_lookup[(edge.first.chain, a)]
        r2, p2 = residue_lookup[(edge.second.chain, b)]

        recipe = recipe_for(p1.base_class, p2.base_class)
        if recipe is None:
            messages.append(
                f"RUN EDGE: {edge.first.chain}{a} <-> "
                f"{edge.second.chain}{b}: no configured recipe"
            )
            continue

        candidate = _candidate_score(r1, r2, p1, p2, recipe)

        if candidate is None:
            messages.append(
                f"RUN EDGE: {edge.first.chain}{a} <-> "
                f"{edge.second.chain}{b}: geometry could not be checked"
            )
            continue

        # A run can rescue a weaker individual pair, but not a completely
        # unreasonable one.
        if candidate.score >= 30.0:
            additions.append(
                Candidate(
                    candidate.first,
                    candidate.second,
                    candidate.recipe,
                    candidate.score + 20.0,
                    candidate.bond_distances,
                    candidate.angle_errors,
                    candidate.plane_angle,
                )
            )
            messages.append(
                f"RUN EDGE: {edge.first.chain}{a} <-> "
                f"{edge.second.chain}{b} score={candidate.score:.1f} "
                f"accepted as {direction} extension"
            )
        else:
            messages.append(
                f"RUN EDGE: {edge.first.chain}{a} <-> "
                f"{edge.second.chain}{b} score={candidate.score:.1f} "
                f"hard stop"
            )

    return additions, messages


def _infer_run_gaps(
    run: list[Candidate],
    residue_lookup: dict[tuple[str, int], tuple[object, PairResidue]],
):
    """Check one-residue holes inside an otherwise continuous run."""
    additions = []
    messages = []

    if len(run) < 2:
        return additions, messages

    ordered = sorted(run, key=lambda c: int(c.first.resid))

    for left, right in zip(ordered, ordered[1:]):
        try:
            da = int(right.first.resid) - int(left.first.resid)
            db = int(right.second.resid) - int(left.second.resid)
        except ValueError:
            continue

        if da != 2 or db != -2:
            continue

        a = int(left.first.resid) + 1
        b = int(left.second.resid) - 1

        key1 = (left.first.chain, a)
        key2 = (left.second.chain, b)

        if key1 not in residue_lookup or key2 not in residue_lookup:
            continue

        r1, p1 = residue_lookup[key1]
        r2, p2 = residue_lookup[key2]

        recipe = recipe_for(p1.base_class, p2.base_class)
        if recipe is None:
            messages.append(
                f"RUN GAP: {left.first.chain}{a} <-> "
                f"{left.second.chain}{b}: no configured recipe"
            )
            continue

        candidate = _candidate_score(r1, r2, p1, p2, recipe)

        if candidate is None:
            messages.append(
                f"RUN GAP: {left.first.chain}{a} <-> "
                f"{left.second.chain}{b}: geometry could not be checked"
            )
            continue

        if candidate.score >= 30.0:
            additions.append(
                Candidate(
                    candidate.first,
                    candidate.second,
                    candidate.recipe,
                    candidate.score + 25.0,
                    candidate.bond_distances,
                    candidate.angle_errors,
                    candidate.plane_angle,
                )
            )
            messages.append(
                f"RUN GAP: {left.first.chain}{a} <-> "
                f"{left.second.chain}{b} score={candidate.score:.1f} "
                f"accepted"
            )
        else:
            messages.append(
                f"RUN GAP: {left.first.chain}{a} <-> "
                f"{left.second.chain}{b} score={candidate.score:.1f} "
                f"hard stop"
            )

    return additions, messages


def _select_runs(
    candidates: list[Candidate],
    residue_lookup: dict[tuple[str, int], tuple[object, PairResidue]],
):
    """Select strong antiparallel runs, then fill gaps and extend edges."""
    # Only reasonably plausible candidates seed runs. We keep the threshold
    # lower than the final isolated-pair threshold because continuity matters.
    seeds = [c for c in candidates if c.score >= 45.0]
    runs = _build_runs(seeds)

    runs.sort(key=lambda r: (_run_score(r), len(r)), reverse=True)

    selected = []
    used = set()
    messages = []

    for run in runs:
        run_additions, run_messages = _infer_run_gaps(
            run, residue_lookup
        )
        edge_additions, edge_messages = _infer_run_extensions(
            run, residue_lookup
        )

        messages.extend(run_messages)
        messages.extend(edge_messages)

        proposed = list(run)
        proposed.extend(run_additions)
        proposed.extend(edge_additions)

        # Prefer the best available candidate at each residue position.
        proposed.sort(key=lambda c: c.score, reverse=True)

        accepted = []
        local_used = set()

        for candidate in proposed:
            a = (candidate.first.chain, candidate.first.resid)
            b = (candidate.second.chain, candidate.second.resid)

            if a in local_used or b in local_used:
                continue
            if a in used or b in used:
                continue

            accepted.append(candidate)
            local_used.update((a, b))

        # A run needs at least two internally compatible pairs to establish
        # enough structural context for its rescued additions.
        if len(accepted) < 2:
            continue

        selected.extend(accepted)
        used.update(local_used)

    # Finally allow isolated, high-confidence pairs not belonging to a run.
    for candidate in sorted(candidates, key=lambda c: c.score, reverse=True):
        a = (candidate.first.chain, candidate.first.resid)
        b = (candidate.second.chain, candidate.second.resid)

        if candidate.score < MIN_SCORE:
            continue
        if a in used or b in used:
            continue

        selected.append(candidate)
        used.update((a, b))

    selected.sort(
        key=lambda c: (
            c.first.chain,
            int(c.first.resid),
            c.second.chain,
            int(c.second.resid),
        )
    )

    return selected, messages


def guess_pairs(
    pdb_filename: str | Path,
) -> tuple[list[Candidate], list[str]]:
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure(
        "NARestraints", str(pdb_filename)
    )
    records = load_residue_records("data/Ligands.xlsx")

    residues = []

    for model in structure:
        for chain in model:
            for residue in chain.get_residues():
                try:
                    pair_residue = pair_residue_from_pdb(
                        records, residue
                    )
                except ValueError:
                    continue

                residues.append((residue, pair_residue))

    candidates = list(_compatible_candidates(residues))

    residue_lookup = {
        (p.chain, int(p.resid)): (r, p)
        for r, p in residues
        if p.resid.isdigit()
    }

    return _select_runs(candidates, residue_lookup)

def write_guess(
    filename: str | Path,
    candidates: Iterable[Candidate],
) -> None:
    lines = []

    for candidate in candidates:
        lines.append(
            f"{candidate.first.chain} {candidate.first.resid}"
        )
        lines.append(
            f"{candidate.second.chain} {candidate.second.resid}"
        )
        lines.append("")

    Path(filename).write_text(
        "\n".join(lines).rstrip() + "\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Guess nucleic-acid base pairs from low-resolution "
            "PDB geometry. This is independent of restraint generation."
        )
    )
    parser.add_argument("pdb", help="Input PDB file")
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output .txt filename (default: <PDB stem>-guessed.txt)",
    )
    parser.add_argument(
        "--expected-pairs",
        type=int,
        default=None,
        help="Expected number of base pairs; mismatch produces a warning",
    )

    args = parser.parse_args()

    pdb_path = Path(args.pdb)
    output = (
        args.output
        or pdb_path.with_name(
            pdb_path.stem + "-guessed.txt"
        )
    )

    fixed_pdb = validate_and_fix_pdb(args.pdb)
    candidates, messages = guess_pairs(fixed_pdb)

    print(f"BASE PAIRS FOUND: {len(candidates)}")

    if args.expected_pairs is not None:
        if len(candidates) != args.expected_pairs:
            print(
                f"WARNING: expected {args.expected_pairs} "
                f"base pairs, found {len(candidates)}"
            )
        else:
            print(
                f"EXPECTED COUNT MATCHES: {args.expected_pairs}"
            )

    for message in messages:
        print(message)

    for candidate in candidates:
        print(
            f"  {candidate.first.chain}{candidate.first.resid} "
            f"<-> {candidate.second.chain}{candidate.second.resid} "
            f"{candidate.recipe:3s} "
            f"score={candidate.score:5.1f} "
            f"bonds="
            + ",".join(
                f"{distance:.2f}"
                for distance in candidate.bond_distances
            )
            + f" plane={candidate.plane_angle:.1f}°"
        )

    write_guess(output, candidates)
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
