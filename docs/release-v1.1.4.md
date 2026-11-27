# NARestraints v1.1.4

This release corrects how NARestraints identifies the bond from the sugar
to the base in PSU, P2U, B8H and UY1. In all four, C1′ bonds to C5.
The base ring retains N1, and the intended Watson–Crick contacts to adenine
were emitted using N3 and O4. The oxygen assignment was corrected to O2 in
[v1.1.5](release-v1.1.5.md) after checking experimental pairs. The updated workbook and loader also keep the sugar out of
the base-pair plane and parallelity selection.

The release includes the October workbook review of 5BU/BRU sugar metadata,
the DF sulfur atom mapping and 129 trailing spaces in C5 atom names.
Existing range files, command names and explicit workbook paths continue to
work. The package accepts older workbooks. Use the new workbook and its
matching loader together. [November cell and source audit](https://github.com/vecchioni-lab/NARestraints/blob/v1.1.4/docs/workbook-audit-2026-11-26.json).
[October cell audit](https://github.com/vecchioni-lab/NARestraints/blob/v1.1.4/docs/workbook-audit-2026-10-11.md).

For the four pseudouridines, complete named bond graphs agreed between
wwPDB and the reference files shipped with Phenix 2.2.1-6174. Each of the
other 614 workbook records matched the October source. On the eight-component
design, Phenix resolved ten intended pairing distances, sixteen angles, four
planes and four parallel groups. The only changed selections removed UY1
C1′ from one plane and one parallel group. These were monomer selection
checks. Refining the complete mixed scaffold is a separate NASolve milestone.

## Install

```bash
python -m pip install "https://github.com/vecchioni-lab/NARestraints/releases/download/v1.1.4/narestraints-1.1.4-py3-none-any.whl"
narestraints --help
```

Python 3.10 or later is required. The source archive and SHA256SUMS accompany
the wheel. The packaged workbook has SHA-256
`baa41d80189f16e337cbd294ce91322eb40b68b144222c2d0cf696cb63a4607c`.
The GitHub workflow builds both distributions, installs each outside the
checkout and checks the builder, guesser, mirror and workbook on Python 3.10,
3.12 and 3.14. The release publishes the artifacts tested on Python 3.12.
