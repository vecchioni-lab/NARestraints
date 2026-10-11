# NARestraints development handoff

Current checkpoint: **2026-10-11**, based on released **v1.1.3**
(`a9264f9eb4ec6071a4b4cd5356bec2b8b58b5691`) and the user's subsequent NASolve
native receipts. This is the active status/backlog; the full September handoff
and superseded port README are [archived with checksums](history/README.md).

**Unreleased workbook review, 2026-10-11:** the [human audit](workbook-audit-2026-10-11.md)
and [machine-readable cell manifest](workbook-audit-2026-10-11.json) document
138 corrections: swapped 5BU/BRU sugar metadata/abbreviations and sorting copies,
the reviewed DF S1 mapping, and all 129 literal C5 trailing-space mappings.
The original workbook hash remains the v1.1.3 historical receipt; corrected
source hash is `afed0f332c3d70cd14c395005fcbccf38201e2818bb9b765c86decda309707f5`.
Artifact Tool authored the values; transplantation of only authored cell-string
indices preserves every other cell value/type/style and unrelated XLSX part.
Focused regressions: initially 6 failed/2 passed for the first corrections,
then 1 failed/8 passed for the remaining 128 spaces; final **9 passed**.
Full command `env PYTHONDONTWRITEBYTECODE=1 ../docs-check-venv/bin/python -m pytest -q`
passes **42 tests (1.69 s)**. No recipe or loader behavior changes, package
release, laptop update, or native Phenix execution is claimed.

Read the [README](../README.md) for use and the [v1.1.3 release
record](release-v1.1.3.md) for release evidence. NASolve's
[current handoff](https://github.com/vecchioni-lab/NASolve/blob/cedar/docs/development-handoff.md)
and [native validation ledger](https://github.com/vecchioni-lab/NASolve/blob/cedar/docs/native-modified-pair-live-validation.md)
own its integration status and next execution steps.

## Completed and bounded evidence

- [x] Installable `restraints` package, bundled workbook, working-directory-independent
  resource lookup, and generation/guessing/mirroring console tools.
- [x] Modified stacking is implemented (PR #1) and released in v1.1.2 and v1.1.3:
  mapped modified neighbours use explicit parallelities; canonical neighbours
  retain native stacking; an unknown mapping retains a generic stack with a
  warning. The September ED interpretation accounted for all 38 expected stacks.
- [x] v1.1.3 corrects Z:P and K:X role orientation to P/X G-like and Z/K C-like;
  B:S remains B G-like/S C-like, and D:T retains its separate `D_T` recipe.
  Workbook-backed tests cover these roles, atom selections, and reversed order.
  The committed workbook and sulfur targets were not changed.
- [x] The source-tree pair-matrix stager creates isolated checked inputs and hash
  manifests. It is a development helper, not a packaged runtime command.
- [x] NASolve's earlier synthetic Z:P challenge reached native PostMR and numerical
  AutoRefine success after its separate Saenger-overlay correction. The user
  reported good bonds/planes in Coot; this is software-integration evidence.
- [x] The later combined WC-like challenge containing D:T, B:S, Z:P and K:X passed
  Phaser, PostMR with 42/42 target identities, a generic-linkage diagnostic, and
  exact custom-restraint coverage checks. These were native user-run diagnostics
  using a prepared bundle; the linkage diagnostic substituted a fresh IMC
  candidate. They are **not a completed geometry/refinement test or a
  from-scratch full-auto acceptance run**.

For the combined challenge, effective sugar/glycosidic torsions and phosphate
protonation still require review before geometry qualification. Frozen inputs,
native logs and exact counts belong in NASolve's ledger rather than a second
cross-repository transcript. Synthetic target chemistry on the donor diffraction
data does not establish experimental chemical identity.

## Ownership and immediate order

NARestraints owns atom mappings, reviewed pair recipes, stacking recipes and
mirroring. NASolve owns component acquisition/cache, justified dictionary
exceptions, numerical monomer preparation, polymer linkage, explicit phosphate
intent and propagation through PostMR/refinement. A component code or a SMILES
string alone does not select a reviewed pair recipe.

NASolve's first CIF Doctor slice now implements offline dictionary assessment,
explicit same-code comparison and bounded reviewed preparation, with report-only
PostMR audits around mutation and ReadySet. The
[human overview](https://github.com/vecchioni-lab/NASolve/blob/cedar/docs/cif-doctor-human-overview.md)
explains its algorithm, tools and limits. Native/proxy validation, broader
chemical descriptors, geometry qualification and guided Topo/Scout work remain
separate follow-up in the NASolve roadmap. Source self-consistency is distinct
from independent chemical validation; numerical restraint checks stay separate.
This adds neither a NARestraints monomer generator nor a geometry-trial gate.

The target preparation workflow remains a fresh full-auto run from ligand codes
and sequence context, with no student-maintained component patches. Routine
source caching must not grow the curated exception registry. The successful
prepared-bundle diagnostic does not yet satisfy that target.

## Open NARestraints work

- [x] **Legacy workbook mappings:** reviewed DF's canonical O2 mapping (`S2` in the
  legacy workbook versus reviewed A1AAZ/DF atom `S1`) and trimmed canonical C5 spaces,
  including S6G. The correction is implemented in unreleased source data.
  Keep downstream compatibility adapters until an upstream data change is
  reviewed, released and tested. Do not mutate an installed workbook at runtime.
- [ ] **PSU attachment metadata:** replace first-column glycosidic inference
  with an explicitly reviewed attachment/base-plane contract. Current PSU maps
  N1 as glycosidic and includes C1′ as a base atom; its CCD attaches C5–C1′.
  Coordinate loader, geometry, mirror and metadata-filter changes with tests.
- [ ] **Sulfur geometry:** audit the 3.04 A contact target / 0.2 A sigma against
  appropriate evidence. The historical 2.498 A contact was measured on a prepared
  starting model, not a demonstrated final refined distance. Keep the current
  values until a sound comparison separates monomer, starting-model and pair
  effects. DE monomer repair and the full ED comparison remain NASolve work.
- [ ] **Noncanonical angles:** `AG_IX` and `GU_XXVIII` have distance restraints but
  empty angle arrays. Add angles only from reviewed native or published geometry,
  with source provenance and atom-selection tests; do not invent precise targets.
- [ ] **Explicit geometry API:** allow a caller to select a reviewed G:C, A:T or
  G:T template independently of residue identity. Unknown templates must fail
  clearly; do not infer a geometry override from pH or relabel the residues.
- [ ] **`Other` extension lane:** `AUTHORITATIVE_SHEETS` still excludes `Other`
  and the builder limits pair categories. Permit reviewed mapping/manual use
  without inventing automatic pair eligibility or dropping unrelated output.
- [ ] **Mirroring coverage:** add DNA/RNA D→L→D, inventory, coordinate and modified/
  unsupported-residue policy checks beyond the installed CLI smoke check.
- [ ] **Small repository cleanup:** document workbook schema/recipe provenance;
  decide the role of `gu_phil.txt` and committed `.DS_Store` files before deleting
  them; review licensing. `pyproject.toml` is the installation declaration;
  `requirements.txt` is the existing pinned environment snapshot, not a second
  package specification. These files have not been changed by this docs pass.

## Maintenance contract

Preserve the public `restraints` import namespace. New scientific behavior needs
regression coverage and, for Phenix-facing syntax, an appropriate native check.
Release verification remains `bash scripts/verify_release.sh` and the recorded
CI result for the exact candidate, rather than a historical test count.

Before local implementation, inspect both repositories' status and verify the
NARestraints import in the consuming NASolve environment. The user's separate
dirty NARestraints feature checkout includes unpublished workbook edits; this
released baseline does not authorize overwriting or adopting them. Preserve
models, reflections, frozen runs and Free-R assignments.

Promote stable contracts to focused user documentation. Keep this handoff short;
retain prior evidence in the dated archive instead of appending another transcript.
Maintain a human feature descriptor explaining purpose, method, tools and
limitations for readers and manuscript authors. Update it whenever behavior,
dependencies or scientific claims change; distinguish implemented and planned work.
