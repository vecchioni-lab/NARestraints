# Changelog

## Unreleased

- Add explicit-site 5'-terminal phosphomonoester geometry support for Phenix.
  Declared terminal phosphate sites receive the three OP3-centered angle
  restraints missing from the standard nucleotide dictionary while leaving
  Phenix's existing P-OP3 bond and ordinary P/OP1/OP2/O5' restraints intact.
- Use CSD-derived terminal phosphomonoester targets from Kowiel et al., Nucleic
  Acids Research 44 (2016): OP1-P-OP3 114.0(7) degrees, OP2-P-OP3 112.8(10)
  degrees, and OP3-P-O5' 102.9(12) degrees. The API is explicit-site only and
  fails closed when the required phosphate atoms are absent; no terminal state
  is inferred from coordinates or residue names.
- No changes to pair recipes, sulfur-contact targets, or the ligand workbook.
  Live Phenix/NASolve refinement validation is still required before release.

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
