# Changelog

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
