# NARestraints development handoff

Status: living design and maintenance notes, updated 2026-09-11.

This file records scientific and architectural decisions that should survive chat context. When a planned behavior becomes implemented and stable, promote the durable contract into the user README and/or focused documentation rather than letting this file become a second specification.

## Current role

NARestraints converts nucleic-acid residue mappings and reviewed base-pair recipes into Phenix-compatible restraint PHIL. NASolve consumes it as a scientific dependency, but NARestraints should remain independently useful from its own CLI and Python API.

The project is already installable through `pyproject.toml` and exposes the `narestraints`, `narestraints-guesser`, and `narestraints-mirror` console scripts. The next cleanup should improve scientific behavior, tests, documentation, and repository presentation without gratuitously changing the import namespace that NASolve already uses.

## Immediate scientific fixes

### Modified-residue stacking must never disappear

Current stacking generation emits generic Phenix `stacking_pair` blocks for every consecutive residue in a chain. Phenix can fail to infer a base plane for modified residue names such as `DE`, even when the supplied monomer CIF contains an explicit `_chem_comp_plane_atom` definition. In a tested ED structure, the modified residue A:12 participates in two neighboring stacks and Phenix emitted two `Cannot make NA restraints ... no planarity definition` warnings.

Policy:

- canonical/canonical stacks may continue to use Phenix `stacking_pair`;
- any stack containing a modified/noncanonical nucleotide should be emitted as an explicit `geometry_restraints.edits.parallelity` using NARestraints' own reviewed/mapped base-plane atom selections for both residues;
- preserve every physical stacking relationship unless a caller explicitly disables stacking;
- regression tests should verify that a modified residue with two neighbors produces two explicit manual stacking restraints rather than two generic `stacking_pair` blocks;
- live Phenix validation should confirm that the missing-plane warnings disappear while all expected stacks remain restrained.

This is preferred to dropping stacking or adding residue-name hacks to NASolve.

### Upstream legacy atom-mapping fixes

NASolve currently carries compatibility adapters for two NARestraints workbook issues. Fix them upstream after tests so the downstream adapters can eventually be removed:

- `DF`: legacy canonical `O2 -> S2` should match the reviewed A1AAZ/PDB-compatible atom identity `S1`;
- `S6G`: trim the legacy `C5 ` value to `C5`.

Do not mutate an installed workbook at runtime. Correct the packaged authoritative data and retain regression coverage.

### Sulfur hydrogen-bond geometry audit

Current sulfur-containing GC-like recipes use a special sulfur contact target of 3.04 A with sigma 0.2 A, while loosening the other contacts in the same pair. A refined DE-containing test structure still looked visually short at the sulfur contact.

Do not change this value by intuition alone. Audit the structural/literature basis, inspect representative refined geometries, and either retain the value with documentation or replace it with a reviewed target and uncertainty. Keep the sulfur-specific policy explicit and tested.

## Noncanonical pair recipes

`A:G` (`AG_IX`) and `G:T` (`GU_XXVIII`) are already explicit noncanonical recipes, but their angle arrays are currently empty. Their hydrogen-bond distance restraints are present.

Source hierarchy for adding angle targets:

1. Prefer an existing Phenix/cctbx nucleic-acid restraint definition when it corresponds unambiguously to the intended geometry.
2. Otherwise use published structural/statistical values for the specific pair geometry (Saenger/Leontis-Westhof class as applicable), recording the source.
3. If only a small literature set is available, use a conservative mean and generous sigma rather than false precision.
4. Only as a last fallback, derive chemically analogous angle targets from validated canonical hydrogen-bond geometries, clearly labelling them as provisional and using broad uncertainties.

Do not silently invent angles. Add source/provenance comments next to the constants and tests that exercise the exact atom selections.

## User-selected geometry independent of residue identity

Keep chemical identity and restraint geometry separate. A user may know contextual chemistry that the generic mapper cannot infer, for example a `G:Z` pair at high pH where Z is deprotonated and should be restrained with a C-like geometry.

NASolve may expose syntax such as `force = G:C`, but NARestraints should provide the underlying API primitive: apply a reviewed geometry recipe to actual residue identities without mutating or relabelling those residues.

Initial reviewed force-template targets requested by the project are:

- `G:C`
- `A:T`
- `G:T`

Unknown force templates should fail closed. Do not infer them automatically from pH or other experimental context unless a future reviewed policy explicitly does so.

## Open extension lane: the `Other` workbook sheet

The ligand workbook must leave the door open to new/manual bases that are not yet part of the curated automatic recipe catalogue.

Treat the `Other` sheet as an explicit extension lane rather than ignoring it or allowing an unfamiliar residue to break the whole program.

Desired behavior:

- records on `Other` may be loaded and resolved by ligand code for atom mapping and validation;
- a residue may therefore be recognized even when its base-pair geometry recipe is not known;
- lack of a reviewed automatic pair recipe should not crash unrelated restraint generation;
- automatic pair restraints for an unknown category remain fail-closed with a clear warning/diagnostic;
- callers should still be able to construct manual pair/stacking restraints from the mapped atoms or explicitly select a reviewed geometry template;
- future new-base development should not require adding another hard-coded workbook sheet name for every new chemical family;
- provenance should report that a record came from `Other`, along with its ligand code and any explicitly chosen geometry recipe.

A good internal separation is: **residue recognition/mapping is permissive; automatic scientific recipe selection is conservative.**

The current `AUTHORITATIVE_SHEETS` list in `residue_library.py` does not include `Other`; that is an implementation item to change with tests. The builder also currently rejects `Base Analog` values outside a fixed `_PAIR_CATEGORIES` set; manual/extension residues need a path that remains mappable without pretending an unsupported automatic pair recipe exists.

## L/D mirroring

The recovered D/L mirroring code supports DNA and RNA name/atom transformations using the workbook as authoritative mapping. Add first-class tests for:

- D -> L -> D round trips;
- atom/residue inventories;
- coordinates under the defined X -> -X mirror transform;
- DNA and RNA examples;
- modified or unsupported residues failing/remaining unchanged according to an explicit policy.

NASolve relies on this scientifically, so it should not remain validated only by historical manual checks.

## Repository cleanup / presentation

Target a small, readable research-software repository:

```text
NARestraints/
├── README.md                  # human-facing overview and quick start
├── AGENTS.md                  # machine/collaborator maintenance contract
├── CHANGELOG.md
├── pyproject.toml
├── docs/
│   ├── architecture.md
│   ├── recipes.md
│   ├── ligand-mapping.md
│   └── development-handoff.md
├── restraints/
│   ├── ...
│   └── data/Ligands.xlsx
├── examples/
└── tests/
```

Cleanup items:

- remove committed `.DS_Store` and ignore it;
- merge useful `README_PORT.md` material into the main README and retire the duplicate when safe;
- decide whether large root artifacts such as `gu_phil.txt` are reproducible fixtures, reference outputs, or historical debris; move or remove accordingly rather than leaving unexplained files at repo root;
- clarify why both `requirements.txt` and `pyproject.toml` exist, or make one clearly authoritative for installation and the other a development lock/snapshot;
- add a license before presenting the project as reusable public software;
- document the workbook schema, source sheets, extension lane, and recipe provenance.

Do not rename the Python package `restraints` merely for aesthetics unless a compatibility migration is deliberately planned; NASolve already imports this namespace.

## Validation philosophy

Every scientific change should add a regression test that fails before the change. For Phenix-facing syntax, also validate at least one real generated PHIL against a supported Phenix runtime when practical.

Keep these distinctions explicit:

- residue identity and atom mapping;
- automatic pair-recipe eligibility;
- pair geometry;
- stacking geometry;
- monomer dictionary geometry;
- L/D mirroring;
- user/context-selected geometry overrides.

The software should be permissive about recognizing new chemistry, conservative about inventing scientific restraints, and explicit about provenance whenever user context overrides automatic behavior.
