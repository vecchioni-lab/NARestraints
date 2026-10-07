# Changelog

## 1.1.3 — 2026-10-08 (release candidate; tag pending CI)

- Preserve the existing named B:S, Z:P, K:X and D:T recipes and their
  experimental identities. NARestraints' `GC` is the shared three-contact
  *geometry template*, not a user-forced G:C identity substitution.
- Correct the reversed Z:P and K:X roles: B/P/X are guanine-like (N1/N2/O6)
  and S/Z/K cytosine-like (O2/N3/N4). Keep B:S unchanged.
- Align modified-base stacking-plane selection with those role assignments.
- Replace misleading Z/K guanine-like synthetic fixtures and add tests using
  actual `Ligands.xlsx` records from the B, S, Z, P, K, X and D sheets,
  plus a thymine partner for the separate `D_T` recipe. Also verify pair order
  reversal and the exact contact/plane atom selections.
- D denotes the reviewed diaminopurine-like role in D:T; no D:A recipe is
  registered, and none is invented in this patch. I:C stays unchanged pending
  a separate evidence-based assessment; all other recipes and the ligand
  workbook are untouched.
- GitHub candidate CI passed Python 3.10/3.12/3.14 (source and installed
  wheel/sdist) before release version bump; final 1.1.3 CI must also pass.
  The user reported 21/21 focused and a green corrected full NARestraints
  regression from the independent candidate worktree.
- The corrected Z:P pair passed native NASolve PostMR with three checked
  P:Z contacts and no geometry-force override. After an independent
  NASolve Saenger-template compatibility correction for modified off-pair
  bases, native Phenix AutoRefine reached numerical SOLVED/refine-001 with
  frozen input integrity OK. User reported good visual bonds and planes in
  Coot (mild plane deviations acceptable).
- Real B:S/K:X native NASolve tests with unavailable local component
  dictionaries remain pending and are **not** represented as passing.
  The synthetic modified-base W challenge is not proof of the true
  experimental chemistry. Existing historical runs and the dirty local
  NARestraints feature checkout remain untouched.

## 1.1.2 — 2026-09-15

- Release the previously merged modified-residue stacking fix (PR #1): explicit
  parallelity restraints for mapped modified neighbours, native stacking for
  canonical neighbours, and a warning-preserving fallback for unknown mappings.
- Bump the distribution version from 1.1.1 so the release is distinguishable
  from the older installation that lacked the stacking module.
- Preserve the dictionary-audit handoff and add an authoritative current release
  checkpoint rather than losing historical reasoning during branch cleanup.
- Add wheel/source-distribution build and non-editable installation checks,
  including all console tools and the unchanged committed ligand workbook.
- No changes to pair recipes, sulfur target values, or the ligand workbook.
  NASolve's 1AP/OP3 integration and unfinished DE repair are separate projects.

## 1.1.1 — 2026-08-25

Installable package, bundled ligand workbook, working-directory-independent
resource lookup, and CLI entry points for restraints, guessing, and mirroring.
