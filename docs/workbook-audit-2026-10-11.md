# Reviewed ligand-workbook metadata corrections

The 11 October 2026 review found two swapped bromouridine sugar descriptions,
an already documented DF atom-mapping defect and a systematic trailing-space
defect in canonical C5 mappings in the active `restraints/data/Ligands.xlsx`.
The user authorized both the reviewed metadata corrections and all whitespace
cleanup. The patch changes 138 cells: the ten initially reviewed cells below
plus 128 additional C5 mapping cells. It changes workbook metadata and exact
atom-name mappings; it does not change pair recipes, contact targets, bond
orders, protonation or numerical CIF restraints.

The workbook before this patch has SHA-256
`94a66af42081188fd95f3fdcbe04cb01bed8f1826772597272320a8b4c0433b2`.
The historical workbook under `data/` is not the active package resource and is
not changed. There is no new package release implied by this patch; installed
v1.1.3 distributions retain their original workbook until explicitly updated.

The corrected workbook has SHA-256
`afed0f332c3d70cd14c395005fcbccf38201e2818bb9b765c86decda309707f5`.

## Exact reviewed changes

The [machine-readable audit manifest](workbook-audit-2026-10-11.json) records
every one of the 138 changed cells, its original and corrected value, and the
workbook hashes. The table lists the ten initially reviewed changes; the
systematic C5 cleanup is described immediately below it.

| Sheet | Cell | Component / field | Before | After |
|---|---|---|---|---|
| thymine | F27 | 5BU sugar type | DNA | RNA |
| thymine | C27 | 5BU abbreviation | 5-bromo-dU | 5-bromo-rU |
| thymine | F62 | BRU sugar type | RNA | DNA |
| thymine | C62 | BRU abbreviation | 5-bromo-rU | 5-bromo-dU |
| sort | G429 | 5BU sugar type, sorting view | DNA | RNA |
| sort | D429 | 5BU abbreviation, sorting view | 5-bromo-dU | 5-bromo-rU |
| sort | G428 | BRU sugar type, sorting view | RNA | DNA |
| sort | D428 | BRU abbreviation, sorting view | 5-bromo-rU | 5-bromo-dU |
| thymine | N208 | DF canonical O2 atom mapping | S2 | S1 |
| guanine | O120 | S6G canonical C5 atom mapping | `C5 ` (trailing space) | C5 |

5BU is labelled `RNA LINKING` in its public Chemical Component Dictionary
(CCD) entry and includes O2′. BRU is labelled `DNA LINKING` and lacks O2′.
The CCD component names agree with this distinction. Their existing workbook
names are retained; the swapped sugar types and ribose/deoxyribose shorthand
are corrected in both the active mapping sheet and its sorting view.

DF is the existing reviewed A1AAZ/2-thio-thymidine mapping. The NASolve
dictionary already used for this reviewed identity contains S1, has a declared
C2–S1 double bond and contains no S2. Correcting the workbook's canonical O2
mapping to S1 aligns the atom selection with that dictionary. It does not
declare every file bearing the code DF chemically equivalent, select a new
sulfur contact target or authorize an unreviewed numerical dictionary.

S6G's literal trailing space in C5 was already listed in the development
handoff. Removing it preserves the same atom identity and lets exact-name
lookups find C5. Existing downstream compatibility adapters remain in place
until an upstream release and downstream validation justify their removal.

The complete whitespace cleanup trims all 129 literal `C5 ` values found in
the canonical C5 role column: 125 cells selected from `guanine!O2:O133`, plus
`B!O2:O5`. S6G's `guanine!O120` is one of those 129 cells and is already counted
in the table above. Only cells whose original atom-role value is exactly
`C5 ` are changed; empty cells, other mapped atoms and descriptive metadata
are retained. The manifest provides the individual selected cells rather than
implying that every cell in the guanine range was edited.

## Evidence snapshots

The exact source bytes used for this review are identified below. Public URLs
may later serve a revised CCD entry; the recorded hashes identify this review's
snapshots.

| Source | SHA-256 |
|---|---|
| [RCSB CCD 5BU](https://files.rcsb.org/ligands/download/5BU.cif) | `3599af77d7ae2dce4eed308c7d3470497cfca5b2b69e4b83a321142ccd6e9402` |
| [RCSB CCD BRU](https://files.rcsb.org/ligands/download/BRU.cif) | `0f8e6f09421dd289801eab0f254b1767e0140a1c1b0052cd60e671e369ffda43` |
| [RCSB CCD PSU](https://files.rcsb.org/ligands/download/PSU.cif) | `297308d5c29e331d4099cb99e4871e01adf4f8c2ebb68f3e8fcff94d5e557af5` |
| NASolve `src/nasolve/data/ligands/DF.cif`, reviewed A1AAZ/DF mapping | `27f83c85e89605b5a0b3b02f062da62d7a348b3b346e5df5774a65c7c143e55e` |

## Deliberately deferred findings

PSU requires a coordinated geometry metadata change. Its CCD graph attaches
the sugar through C5–C1′. The current loader infers the glycosidic atom from the
first atom-mapping column, yielding N1 for PSU. The sheet also maps its C7 role
to C1′ (`thymine!T117`), so the helper that collects base atoms includes that
sugar atom. Changing only the inferred glycosidic atom would still exclude the
true sugar attachment from the attachment search and could leave an incorrect
base-plane selection. This patch does not alter PSU.

A future implementation should use explicitly named glycosidic and backbone
attachment fields, exclude backbone atoms from base-plane/heterocycle
selection, and update the loader, all metadata filters and geometry tests
together. Ordinary pyrimidines must retain their existing N1 attachment unless
independent component evidence establishes another atom.

Historical 7MG naming, the proposed 8RO/DE relationship, hydrogen attachment,
protonation and sulfur contact targets remain unchanged. Component labels,
base-family assignments and DNA/RNA linkage labels alone do not establish
those chemical choices.

## Validation contract

Six workbook-backed regression cases in `tests/test_residue_library.py` check
the active 5BU/BRU sugar descriptions and abbreviations, the DF/S6G exact atom
mappings and both sorting-view copies. Before the patch, the focused command
returned **6 failed, 2 passed**, with all six new cases exposing the intended
defects:

```bash
python -m pytest -q tests/test_residue_library.py
```

A seventh added regression inspects canonical C5 mappings across every loaded
workbook record and rejects leading or trailing whitespace. After the first
ten cells were corrected and before the remaining whitespace cleanup, the
focused command returned **1 failed, 8 passed**, with the new regression
reporting exactly 128 remaining mappings containing whitespace.

Artifact Tool authored the corrections. Only the authored cell-string indices
were transplanted into the original XLSX parts: all other cell values, types,
styles, sheet order/dimensions and unrelated uncompressed parts are preserved.
The [manifest](workbook-audit-2026-10-11.json) records the verification.
Final focused tests pass **9 cases**; the full suite passes **42 tests**.
The development handoff records the commands and scope. Native refinement
behavior is not tested by these workbook regressions.
