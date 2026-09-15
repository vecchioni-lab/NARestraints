# NARestraints v1.1.2 — current release checkpoint

Updated 2026-09-15. Read this before the preserved historical
`development-handoff.md` and `README_PORT.md`.

## Scope and provenance

The scientific code is the merged modified-stacking fix from PR #1, commit
`1f20e9f15074d15caa9691bd3d55956b50d86837`. Mapped modified-residue stacks
become explicit parallelity restraints; canonical stacks retain Phenix's native
representation. The physical stack is not silently discarded when mapping is
unknown: that case retains a generic stack and emits a warning.

The release branch incorporates the previously unmerged documentation commit
`6e2132d1d9d375dfaec7216dee3e59754e5bcdcf`. Historical notes and the longer-term
backlog are preserved. The `restraints` Python code and committed ligand workbook
are unchanged by this packaging release. The workbook's Git blob is
`24dad3df897f982c8c771d77600f76e12f28b5a4`. Simon's uploaded working archive had
a different workbook; those local edits are not silently included in the release.

## Validation

Before this packaging change, Simon reported 25 NARestraints tests passed and
live Phenix 2.2.1-6174 interpretation of the modified stacking in ED. The later
NASolve run_004 exercised automatic PostMR/ReadySet and its frozen inputs:
34 native stacking parallelities plus 4 explicit modified-residue stacks,
3 manual base-pair parallelities, and 17 fallback base pairs. The posted summary
had no missing-plane warnings. These are preparation/interpretation checks,
not a complete scientific refinement validation.

The release workflow builds wheel and source distributions on Python 3.10,
3.12, and 3.14. Each is installed non-editably into a new environment and tested
outside the checkout; the 25-test suite, CLI generation/guessing/mirroring, and
bundled-workbook byte identity are checked. The workflow's actual pass/fail
result is the authority; the existence of this document alone is not evidence
that a build ran. SHA256SUMS accompanies the published artifacts. No PyPI upload
is made. The release job does not overwrite an existing tag or published release.

## Cross-repository status and explicit phosphate intent

NASolve PR #3 was merged as `ff7c825f817697661ea7a7940944caf93bf21760` after
Simon reported 497 tests and 145 subtests passed, with the corrected dependency
import and live ED run_004 checks. Its reviewed 1AP dictionary, selected-site
NASnoOP3 modification, ReadySet precedence, and campaign/recipe intent handling
belong to NASolve, not this NARestraints release.

The authoritative policy is **no OP3/O3P in working models without explicit
site intent**. The user can supply that intent in the dataset or by selecting
an annotated, versioned recipe. W/5W6W@1.1.0 deliberately declares D:1; this is
not an exception inferred from a terminal residue or an atom already present.
Campaigns freeze sites and provenance. Explicit dataset lists override recipe
lists; an explicit empty list opts out. Contradictory or ambiguous connectivity
still stops. Older handoff text about automatic terminal preservation is
superseded by this explicit-intent policy.

The installation mismatch is also resolved on Simon's laptop: NASolve had
loaded an older site-packages copy while a test inside NARestraints misleadingly
imported local source. A fresh install must be verified outside the checkout.
This release's distinct package version and clean-install gate address that
class of diagnostic error. Publishing does not change Simon's local environment.

## Still unfinished — do not claim completion

DE's monomer dictionary repair and a complete ED refinement comparison remain
open. The 3.04 A / 0.2 A sulfur-contact restraint is unchanged. The earlier
2.498 A contact was measured on the prepared starting model, not an established
final refined distance. The `Other` workbook extension, user-forced geometry
API, noncanonical-angle provenance, mapping cleanup, and broader mirroring
coverage remain backlog work in the historical handoff, not released features.
