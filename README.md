# NARestraints

Generate Phenix nucleic-acid restraint PHIL from a PDB model and a reviewed
base-pair range file. NARestraints also provides a base-pair guesser and a D/L
nucleic-acid mirroring tool. It is usable independently of NASolve.

## Install version 1.1.2

Use a dedicated Python environment (Python 3.10 or later):

```bash
python3 -m venv .venv
.venv/bin/python -m pip install "git+https://github.com/vecchioni-lab/NARestraints.git@v1.1.2"
```

The GitHub release also supplies a wheel and source archive. Install the wheel
with `python -m pip install /path/to/narestraints-1.1.2-py3-none-any.whl`
inside the intended environment. This is a GitHub release, not a PyPI upload.
The `restraints` import namespace and bundled `restraints/data/Ligands.xlsx`
remain unchanged. Phenix and Coot are separate applications, not bundled here.

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

## What changed in 1.1.2

Stacks touching mapped modified nucleotides now use explicit Phenix
parallelity restraints; canonical/canonical stacks retain `stacking_pair`.
Unmapped modified residues keep a generic stack with a warning rather than
silently losing the relationship. This fallback does not guarantee that Phenix
can resolve the missing mapping. No monomer-dictionary or sulfur-target change
is included in this release.

See [release notes and current handoff](docs/release-v1.1.2.md) first.
[Development handoff](docs/development-handoff.md) is preserved historical
context and the longer-term backlog; its older status and phosphate-policy
statements are superseded by the release checkpoint. `README_PORT.md` is a
historical porting note, not the current installation guide.

## Release verification

`bash scripts/verify_release.sh` builds wheel and source distributions, installs
each into a fresh environment, runs the 25-test suite from a separate directory,
and checks all three console tools and the bundled workbook. It is the Linux
release/CI harness; normal package use is not restricted to Linux.

The release workflow tests Python 3.10, 3.12, and 3.14. A push changing
`pyproject.toml` on `main` can publish v1.1.2 only after those tests pass; a
manual dispatch on `main` can retry that same gated release. Existing tags and
releases are not overwritten. See the Actions result for execution status.
