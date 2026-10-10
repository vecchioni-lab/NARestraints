# NARestraints v1.1.3 — modified-pair role orientation

This is a **reviewed maintenance release** of NARestraints' explicit modified
base-pair geometry and stacking-plane selection. It succeeds v1.1.2 without
overwriting or retargeting that prior release or tag.

This document preserves the release-time evidence. The [current development
handoff](development-handoff.md) records subsequent NASolve combined-run
preparation/linkage/coverage checks and the still-pending geometry qualification.

## Corrected chemistry and unchanged boundaries

NARestraints recognizes B:S, Z:P and K:X as explicit **named modified pairs**.
Its current `GC` template denotes shared three-contact *geometric restraints*,
**not** conversion of residue identity or an automatically requested
`force = G:C`.

The orientation matters: the template's first role requires G-like
N1/N2/O6 mappings, and the second requires C-like O2/N3/N4 mappings.

| Reviewed family | G-like role | C-like role | Change |
| --- | --- | --- | --- |
| B:S | B | S | Already correct; unchanged |
| Z:P | P | Z | Fixed reversed role assignment |
| K:X | X | K | Fixed reversed role assignment |

The corresponding explicit stacking-plane templates follow the same roles.
The D:T hybrid retains its own `D_T` recipe and remains separate from DA:T
(canonical DNA adenine); no unsupported D:A recipe has been invented.
The existing I:C, A:G and G:T configurations have not been reinterpreted
through blanket family inference.

There are **no edits to** the committed
`restraints/data/Ligands.xlsx`, its atom maps, monomer dictionaries,
sulfur bond distances/uncertainties, or the Coot/Phenix integrations.
The existing `narestraints`, `narestraints-guesser` and
`narestraints-mirror` entry points remain available.

## Evidence and tests

- GitHub PR CI checks full source tests and both non-editable wheel/source
  installs on Python 3.10, 3.12 and 3.14. The unchanged committed workbook
  has explicit provenance validation. See the specific release workflow run
  for final pass/fail status.
- The added workbook-backed regression tests check B:S, Z:P, K:X and D:T
  roles from different workbook tabs; reverse pair order; actual mapped atom
  selections; pair hydrogen bonds, plane and stacking template choices.
- The source-only `scripts/stage_nasolve_pair_matrix.py` stages disjoint
  checked input copies for A:T, D:T, B:S, Z:P and K:X W-family challenges,
  with source hash manifests and no native engine execution. The staging
  safety tests run in PR CI. **The stager is a source-tree development helper,
  not a runtime entry point included in the NARestraints wheel.**
- A native NASolve W-family run with explicit Z:P and the reviewed 5CM:G
  and DF:A changes initially failed at Z's missing G-role N2 (v1.1.2).
  After the v1.1.3 candidate correction, native PostMR completed and a
  read-only audit confirmed P.N2/Z.O2, P.N1/Z.N3, P.O6/Z.N4 exactly once,
  no requested geometry-force override, and 42 sequence identities without
  mismatch. A separate narrow NASolve Saenger-overlay candidate was needed
  to replace two stale hardcoded W secondary-structure classes at 5CM:G and
  DF:A. That combined native Phenix AutoRefine returned **SOLVED
  (numerical), refine-001**, with frozen input integrity intact.
- The user inspected the refined model in Coot and reported good overall
  bonding/base-plane appearance, with tolerable nonzero plane deviations.
  Per-site experimental map/geometry validation remains separate.

**Scientific qualification boundary:** the diffraction dataset used in the
NASolve live challenge was *not* claimed to contain these synthetic modified
bases. The numerical result and Coot inspection demonstrate **software
integration**, not experimental confirmation or permission to deposit the
hypothetical structure. B:S/K:X-specific **native NASolve** checks may still
require component dictionaries unavailable in NASolve; they remain a distinct
planned campaign and are not marked complete by this release.

## Installation and provenance

Versioned GitHub release artifact (not a PyPI publication):

```bash
python3 -m venv .venv
.venv/bin/python -m pip install "git+https://github.com/vecchioni-lab/NARestraints.git@v1.1.3"
```

Build verification must check the exact distribution version, both wheel and
source archive, non-editable installation, console tools and unchanged bundled
workbook before the tag/release is created. Installed versions should be
confirmed from the **consuming project's Python environment**, not from
within a source checkout that may shadow the package.

The user's existing dirty `../NARestraints` feature checkout contains
separately owned unpublished scientific work, including workbook edits.
**No release workflow modifies that local checkout** or adopts its workbook.

The first native blocked Z:P run and the later unsuccessful Saenger run remain
immutable forensic evidence; the successful refinement lives in a newly
allocated numbered run. Neither history was rewritten by publishing this
maintenance release.
