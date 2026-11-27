# NARestraints

Version 1.1.5 uses the measured adenine-facing oxygen in four C-linked
pseudouridines. [Release notes](docs/release-v1.1.5.md).

For maintainers, document substantial features for human readers with purpose,
inputs/outputs, method, tools, evidence and limitations, including a methods
paragraph when useful for publication. Update that feature description whenever
its behavior or dependencies change; keep planned capabilities explicit.

Generate Phenix nucleic-acid restraint PHIL from a PDB model and a reviewed
base-pair range file. NARestraints also provides a base-pair guesser and a D/L
nucleic-acid mirroring tool. It is usable independently of NASolve.

## Install the latest stable release

In the intended Python environment, run

```bash
python -m pip install --upgrade --no-cache-dir "NARestraints @ https://github.com/vecchioni-lab/NARestraints/releases/latest/download/narestraints.tar.gz"
```

GitHub serves the tested source archive for its latest release. Its bytes match
that release's numbered source archive. For a repeatable analysis, record the
installed version and use its numbered release.

## Install version 1.1.5

Use a dedicated Python environment (Python 3.10 or later):

```bash
python3 -m venv .venv
.venv/bin/python -m pip install "git+https://github.com/vecchioni-lab/NARestraints.git@v1.1.5"
```

To install the tested wheel directly into an existing environment, run

```bash
python -m pip install "https://github.com/vecchioni-lab/NARestraints/releases/download/v1.1.5/narestraints-1.1.5-py3-none-any.whl"
```

The wheel includes the `restraints` package and its ligand workbook. GitHub
also hosts the source archive and SHA-256 checksums. Phenix and Coot are
separate applications. [Release downloads](https://github.com/vecchioni-lab/NARestraints/releases/tag/v1.1.5).

For development, use `python -m pip install -e '.[test]'` from the checkout.
When NASolve uses an editable NARestraints checkout, install it with NASolve's
own interpreter, and check imports from inside NASolve or outside both projects.
Running an import check inside NARestraints can hide an older installed copy.

## Command-line tools

From an activated environment, using explicit input paths:

```bash
narestraints input.pdb pairs.txt -o restraints.phil
narestraints-guesser input.pdb -o guessed-pairs.txt
narestraints-mirror input.pdb -o mirrored.pdb
```

`python -m restraints` is also supported. Run each command with `--help` for
options. The guesser accepts `--non-canonical` to opt into its existing
noncanonical recipes. Review guessed pairs before using them for refinement.

A range file contains two chain/range lines per paired stretch:

```text
A 103:108
C 214:209

A 109:115
B 125:119
```

Blank lines separate stretches; ranges may run forward or backward.

## Reviewed recipe library

Pair identity and restraint geometry are separate. Pair lookup is order-independent;
the mapped roles within a recipe are ordered.

| Pair | Recipe | First role / second role |
| --- | --- | --- |
| A:T | `AT` | A / T |
| G:C | `GC` | G / C |
| D:T | `D_T` | D / T |
| B:S | `GC` | B / S |
| Z:P | `GC` | P / Z |
| K:X | `GC` | X / K |
| I:C | `AT` | I / C |
| A:G | `AG_IX` | A / G |
| G:T | `GU_XXVIII` | G / T |

`AG_IX` and `GU_XXVIII` currently provide distance restraints without angle
arrays; the guesser requires `--non-canonical` to consider them. Among recognized
residue categories, a pair with no registered recipe produces a warning and
skips pair-specific restraints. Missing mappings or unsupported categories can
still stop generation; the `Other` extension is planned work. The explicit table
in `restraints/recipe_library.py` is the implementation authority; the bundled
atom mappings are in `restraints/data/Ligands.xlsx`.

### Which oxygen pairs with adenine

In a canonical pseudouridine–adenine pair, pseudouridine N3–H faces adenine
N1 and O2 faces adenine N6. In ordinary uridine–adenine, the corresponding
oxygen is O4. The optional `A:T acceptor role` column tells the builder and
pair guesser which mapped atom to use for the second contact and its angle.
PSU, P2U, B8H and UY1 declare O2. N1, O2 and O4 keep their chemical names
and their usual membership in base planes. The evidence for each compound
is described in the [pairing review](docs/release-v1.1.5.md).

### Explicit sugar attachment in version 1.1.4

For PSU, P2U, B8H and UY1, the base side of the glycosidic bond is C5 and the
backbone side is C1′. The optional `Glycosidic atom` and `Backbone attachment atom`
columns name those atoms. N1 still belongs to the uracil ring. Pair and stack
planes use the mapped base atoms. The guesser uses the named backbone atom when
present within its existing distance limit. Workbooks without the new columns
continue to use their existing mappings.
[Workbook changes and source dictionaries](docs/workbook-audit-2026-11-26.json).

## What changed in 1.1.3

B:S remains B=G-like/S=C-like; the reversed **Z:P** and **K:X** recipe roles
are corrected to **P=G-like/Z=C-like** and **X=G-like/K=C-like**, with the
same orientation used by modified-base stacking planes. These pairs retain
their independent identities; the shared GC geometry template is not
a `force = G:C` substitution. The distinct D:T recipe remains unchanged.
The committed `Ligands.xlsx`, atom mappings, monomer chemistry and
previous v1.1.2 release are not altered.

Workbook-tab coverage now verifies B:S, Z:P, K:X, D:T and reverse orientation.
A native NASolve Z:P preparation and subsequent numerically successful
refinement have been demonstrated using an independent NASolve W-template
compatibility correction. This does **not** prove the experimental chemistry
of the donor reflections or mark independent B:S/K:X native campaigns complete.

See [v1.1.3 release notes](docs/release-v1.1.3.md) for release evidence and
limitations. The [current development handoff](docs/development-handoff.md)
records later integration progress and open work: the combined WC-like native
preparation/linkage/coverage diagnostics passed, while geometry qualification
and a fresh full-auto acceptance run remain pending. Historical
[v1.1.2 release notes](docs/release-v1.1.2.md) and the
[archived handoff/port notes](docs/history/README.md) preserve prior evidence.

## Release verification

`bash scripts/verify_release.sh` builds wheel and source distributions, installs
each into a fresh environment, runs the full test suite from a separate directory,
and checks all three console tools and the bundled workbook. It is the Linux
release/CI harness; normal package use is not restricted to Linux.

The release workflow tests Python 3.10, 3.12, and 3.14. A push changing
`pyproject.toml` on `main` can publish **v1.1.5** only after those tests
pass; a manual dispatch on `main` can retry that same gated release. Existing tags and
releases are not overwritten. See the Actions result for execution status.
