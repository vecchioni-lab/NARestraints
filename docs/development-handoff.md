# NARestraints development handoff

Status: living design and maintenance notes, updated 2026-09-11.

This file records scientific and architectural decisions that should survive chat context. When a planned behavior becomes implemented and stable, promote the durable contract into the user README and/or focused documentation rather than letting this file become a second specification.

## Weekend checkpoint — 2026-09-11 (read first)

### What is complete, and what is not

- **Modified stacking is merged into NARestraints main.** PR #1, `Handle modified-residue stacking explicitly`, merge commit `1f20e9f15074d15caa9691bd3d55956b50d86837`. Simon rebuilt the migrated virtual environment on his new laptop, installed editable `.[test]`, and reported **25 tests passed**. A generated ED PHIL was then exercised with his real Phenix installation.
- **The 1AP dictionary plus site-specific linked-phosphate modification passed the ED model-interpretation diagnostic.** This is not yet an installed production fix or a completed refinement validation.
- **DE monomer geometry remains unresolved.** Neither the defective production DE dictionary nor the first replacement candidate is approved for new production use on the strength of this test.
- **No production dictionaries, coordinates, reflection files, or numbered runs were replaced during these isolated diagnostics.** The present checkpoint commit changes documentation only; it does not introduce the candidate dictionaries or apply the phosphate modification in NASolve.
- Repository ownership matters: pair/stacking recipes belong to **NARestraints**; bundled monomer dictionaries, coordinate phosphate cleanup, per-site CIF modifications, and propagation into refinement belong to **NASolve**. The existing `dictionary-audit` branch is in NARestraints. At this checkpoint there is no NASolve branch of that name; establish a suitable NASolve branch when implementing the downstream fix. Do not mistake this notes branch for an implemented NASolve dictionary patch.

### Successful 1AP interpretation test

Runtime: **Phenix 2.2.1-6174** on Simon's new macOS laptop. Executable supplied explicitly from `~/Applications/phenix-2.2.1-6174/bin/phenix.pdb_interpretation`.

Inputs:

- NASolve dataset/run: `examples/TestSets/ED/AutoMR/run_001`.
- Model: `PostMR/Model/readyset_model.pdb`, not an AutoRefine output.
- DE dictionary: the existing `PostMR/Restraints/DE.cif`, retained only to isolate the 1AP change.
- 1AP dictionary: CCP4 MonomerLibrary `1/1AP.cif`, Git blob `1be06d4bb0848891fd3e7dca22d217dd2ad1b69b`, with only `_chem_comp.group` changed from `NON-POLYMER` to `DNA`. Source: https://github.com/MonomerLibrary/monomers/blob/master/1/1AP.cif . The downloaded bytes were checked against that blob before adaptation; numerical restraints were not edited.
- NARestraints PHIL: `/tmp/ED_patched.phil`, generated using the patched NARestraints builder and `examples/Std_padd.txt`.
- A separate CIF modification and PHIL selection, shown below.

The complete 1AP dictionary initially produced one unresolved heavy-atom bond, three angles, one dihedral, and one chirality. A direct atom-inventory comparison confirmed **OP3 was the only dictionary heavy atom absent from B4**; there were no model-only heavy atoms. The counts match the OP3-dependent dictionary entries, including the phosphorus-centred chirality, not a missing sugar chirality.

Tested modification file `linked_phosphate.cif`:

```cif
data_mod_NASnoOP3
loop_
_chem_mod_atom.mod_id
_chem_mod_atom.function
_chem_mod_atom.atom_id
_chem_mod_atom.new_atom_id
_chem_mod_atom.new_type_symbol
_chem_mod_atom.new_type_energy
_chem_mod_atom.new_partial_charge
NASnoOP3 delete OP3 . . . .
```

Tested selection file `linked_phosphate.phil`:

```text
pdb_interpretation.apply_cif_modification {
  data_mod = NASnoOP3
  residue_selection = chain B and resid 4 and resname 1AP
}
```

The executable completed successfully. Simon's filtered log reported:

```text
Chain A: Classifications {'DNA': 21}; Link IDs {'rna3p': 20}
Chain B: Classifications {'DNA': 7}; Modifications used {'NASnoOP3': 1}; Link IDs {'rna3p': 6}
Chain C: Classifications {'DNA': 7}; Link IDs {'rna3p': 6}
Chain D: Classifications {'DNA': 7}; Link IDs {'rna3p': 6}
Total number of custom parallelities: 7
34 stacking parallelities
```

No `Unresolved non-hydrogen`, `Unknown residues`, `unknown nonbonded`, or `Chain breaks` entries appeared in that diagnostic's filtered output. The earlier modified-residue missing-plane warnings were absent in the initial patched-stacking interpretation output.

Stack accounting is **34 generic stacks + 4 explicit modified-residue stacks = 38 original stacking relationships**. The seven custom parallelities are those four stacks plus three pre-existing manual base-pair parallelities; they are not seven additional stacks. Repeated printing of the custom-restraint summary is not evidence of duplicate physical restraints.

Scope limitation: this isolated command did **not** include `5W6W_secondary_structure.eff`, the fallback canonical base-pair file. Its native secondary-structure summary therefore contained zero base pairs. That is expected for this diagnostic, not acceptable evidence of complete production pair coverage. Repeat integration validation with the normal non-overlapping NARestraints plus fallback EFF inputs before full refinement.

### OP3 policy — preserve the user's chemistry

OP3 is intentionally absent at an internally linked nucleotide phosphate. Do not add it back to satisfy a complete isolated-monomer dictionary. Simon notes that a genuine 5'-phosphorylated strand terminus is unusual in these designs, but it must remain supported explicitly.

NASolve's existing `src/nasolve/phosphate.py` removes OP3/O3P only with a verified incoming O3'-P connection and preserves unlinked/terminal cases. Preserve those connectivity guards and ambiguous-case failures. Do not generalize the successful B4 test into unconditional OP3 deletion or infer terminal chemistry solely from residue numbering.

Planned dictionary integration: retain a complete source dictionary, apply the OP3 deletion modification only to verified linked sites, and retain the full appropriate chemistry at genuine phosphorylated termini. A single residue code can occur both internally and terminally in one model. The test used a hand-written B4 selection; automatic site selection and artifact propagation are **not implemented by this checkpoint**.

### DE and sulfur audit: evidence to carry forward

The production NASolve `src/nasolve/data/ligands/DE.cif` was traced to an old eLBOW run using a Phaser PDB input. Observed defects include C3'-C2' target 1.221 A, an O2-H bond with single C2-O2, an S4-H bond with single C4-S4, and a hydrogen bonded directly to phosphorus. It needs a chemically reviewed replacement, not a one-number adjustment.

The first new DE SMILES/template optimization completed, but its candidate remains unapproved: it restored C2=O2, C4=S4, and N3-H connectivity and a 1.548 A C2'-C3' target, while producing P-O5' = 1.860 A and O5'-C5' = 1.340 A, an incomplete base-plane definition missing C5 and S4, and group `ligand`. It must not replace production merely because eLBOW exited successfully.

The attempted `phenix.elbow --chemical_component=1AP --id=1AP --opt` failed with an unexpected O4'-N1 bond of 6.207 A. The cause was not established; do not relax the bond-length check. The parameterized monomer-library route above succeeded at interpretation instead.

**Measurement provenance correction:** the reported 2.498 A N6(1AP B4)-S4(DE A12) contact was measured by `pdb_interpretation` on `readyset_model.pdb`, i.e. the prepared starting model. It does not establish the contact length in `AutoRefine/round_001/refined_001.pdb`. Simon separately observed visually short sulfur contacts in refined maps/models, but those still require an explicit coordinate measurement. Retain the existing 3.04 A target / 0.2 A sigma until sound monomer dictionaries and comparable refinements can separate initialization, monomer geometry, and pair-restraint effects.

### Local artifacts and exact reproduction

These are **historical local paths**, not committed or portable artifacts:

- Audit directory: `~/Desktop/nasolve-dictionary-audit.ly9SWS/`.
- Successful final test directory: `1AP-linked.Dh0108/` under that audit directory.
- Complete final log: `1AP-linked.Dh0108/interpretation.log`.
- Tested complete 1AP candidate: `1AP_library_DNA_candidate.cif` in the audit directory.
- Selected-site modification inputs: `1AP-linked.Dh0108/linked_phosphate.cif` and `linked_phosphate.phil`.
- Rejected/unapproved DE candidate: `DE.cif` in the audit directory; also supplied in chat for inspection. Do not confuse it with the production DE dictionary used in the successful 1AP diagnostic.
- Failed 1AP eLBOW log: `1AP_elbow.log` in the audit directory.
- Patched NARestraints PHIL: `/tmp/ED_patched.phil`. Copy it alongside the Desktop audit for preservation; that copy is a requested housekeeping step, **not confirmed complete here**. It is also regenerable from the checked model, recipe file, and merged builder.

Reproduction command, from the NARestraints repository root (using the original temporary PHIL location):

```bash
RUN="$PWD/../NASolve/examples/TestSets/ED/AutoMR/run_001"
AUDIT="$HOME/Desktop/nasolve-dictionary-audit.ly9SWS"
TEST="$AUDIT/1AP-linked.Dh0108"
"$HOME/Applications/phenix-2.2.1-6174/bin/phenix.pdb_interpretation" \
  "$RUN/PostMR/Model/readyset_model.pdb" \
  "$RUN/PostMR/Restraints/DE.cif" \
  "$AUDIT/1AP_library_DNA_candidate.cif" \
  "$TEST/linked_phosphate.cif" \
  "$TEST/linked_phosphate.phil" \
  /tmp/ED_patched.phil
```

Results above are from Simon's local executions and pasted output, not a Phenix execution by the remote documentation editor. No raw models, maps, diffraction data, or candidate CIF files are included in this documentation commit.

### Restart order next week

1. Read this checkpoint; check local Git status in both repositories before updating anything. Preserve Simon's local workbook/source edits and generated runs. Confirm the merged builder is the one NASolve imports; version `1.1.1` alone is not a commit identifier.
2. In NASolve, integrate the parameterized 1AP dictionary and connectivity-selected phosphate modification with provenance and regression coverage: internal site, true 5'-phosphorylated terminus, mixed internal/terminal instances of the same residue code, ambiguous connectivity, and propagation through PostMR, AutoRefine, subsequent checkpoints/RefineDoctor.
3. Replace DE using reviewed chemistry, complete plane definitions, correct atom mapping/stereochemistry, and validated DNA-link handling. Check the unchanged sugar/phosphate against an appropriate monomer reference, and source sulfur-specific geometry independently rather than indiscriminately copying O-based values.
4. Repeat model interpretation with both corrected dictionaries and the normal pair-restraint fallback file; then perform a fresh, provenance-preserving ED refinement comparison. Verify connectivity/typing, base-pair and stacking coverage, geometry metrics, maps, and the actual N6-S4 distance before/after. Preserve the old run and free-R assignments.
5. Return to the remaining sulfur-pair policy audit and NASolve campaign tests. Keep the existing force-template, `Other` extension, recipe-angle, and cleanup plans below; none is completed merely by the 1AP diagnostic.

## Current role

NARestraints converts nucleic-acid residue mappings and reviewed base-pair recipes into Phenix-compatible restraint PHIL. NASolve consumes it as a scientific dependency, but NARestraints should remain independently useful from its own CLI and Python API.

The project is already installable through `pyproject.toml` and exposes the `narestraints`, `narestraints-guesser`, and `narestraints-mirror` console scripts. The next cleanup should improve scientific behavior, tests, documentation, and repository presentation without gratuitously changing the import namespace that NASolve already uses.

## Immediate scientific fixes

### Modified-residue stacking must never disappear

**Implemented and merged in PR #1; see the weekend checkpoint for local unit tests and live ED interpretation evidence.** Previously, stacking generation emitted generic Phenix `stacking_pair` blocks for every consecutive residue in a chain. Phenix could fail to infer a base plane for modified residue names such as `DE`, even when the supplied monomer CIF contained an explicit `_chem_comp_plane_atom` definition. In the ED structure, the modified residue A:12 participates in two neighboring stacks and Phenix emitted two `Cannot make NA restraints ... no planarity definition` warnings.

Policy:

- canonical/canonical stacks may continue to use Phenix `stacking_pair`;
- stacks touching a mapped modified/noncanonical nucleotide use explicit `geometry_restraints.edits.parallelity` with NARestraints' reviewed/mapped base-plane atom selections for both residues;
- preserve every physical stacking relationship unless a caller explicitly disables stacking;
- if a modified residue cannot yet be mapped, the merged implementation retains generic `stacking_pair` with a warning rather than silently discarding the stack; this fallback is not a guarantee that Phenix can resolve it;
- regression tests cover canonical stacks, a modified residue with two neighbors, and the unmapped-residue fallback;
- live Phenix validation confirmed that the missing-plane warnings disappeared for the tested mapped ED case while all 38 expected stacks remained represented.

This is preferred to dropping stacking or adding residue-name hacks to NASolve.

### Upstream legacy atom-mapping fixes

NASolve currently carries compatibility adapters for two NARestraints workbook issues. Fix them upstream after tests so the downstream adapters can eventually be removed:

- `DF`: legacy canonical `O2 -> S2` should match the reviewed A1AAZ/PDB-compatible atom identity `S1`;
- `S6G`: trim the legacy `C5 ` value to `C5`.

Do not mutate an installed workbook at runtime. Correct the packaged authoritative data and retain regression coverage.

### Sulfur hydrogen-bond geometry audit

Current sulfur-containing GC-like recipes use a special sulfur contact target of 3.04 A with sigma 0.2 A, while loosening the other contacts in the same pair. A refined DE-containing test structure still looked visually short at the sulfur contact. The numerical 2.498 A observation is from the prepared starting model, as clarified in the weekend checkpoint.

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
