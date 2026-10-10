# NARestraints: Python restraint-builder layer

Generate Phenix nucleic-acid restraints from a PDB plus a small human-readable
base-pair specification file.

## Base-pair file

```text
A 103:108
C 214:209

A 109:115
B 125:119
```

Blank lines separate stretches. A range can run forward or backward.

## Explicit recipe library

Pair identity and restraint recipe are deliberately separate. The current
recipe library is:

```text
A-T -> AT
G-C -> GC
D-T -> GC
B-S -> GC
Z-P -> GC
K-X -> GC
I-C -> AT
```

Pairs not in this table are **not guessed**. They produce a non-fatal warning
and their pair-specific restraints are skipped. The rest of the PHIL file is
still generated. Thus G-T, for example, remains unsupported until a future
wobble recipe is deliberately added.

The recipe library lives in `restraints/recipe_library.py` so it can be
extended without rewriting the PHIL generator.

## Run

```bash
python -m pytest
python -m restraints examples/d2d3.pdb example_pairs.txt -o d2d3.phil
```

The current AT and GC recipes reproduce the angle, bond, parallelity and
planarity logic in the supplied MATLAB script. Residue atom mappings come from
`data/Ligands.xlsx`.
