
from __future__ import annotations

import argparse

from .base_pairs import read_base_pair_file
from .builder import build_phil_from_pdb


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate Phenix nucleic-acid restraints from a PDB and base-pair range file."
    )
    parser.add_argument("pdb", help="Input PDB file")
    parser.add_argument("pairs", help="Base-pair specification text file")
    parser.add_argument(
        "-o", "--output", default=None,
        help="Output .phil filename (default: <PDB stem>.phil)",
    )
    parser.add_argument("--no-parallels", action="store_true")
    parser.add_argument("--no-planes", action="store_true")
    parser.add_argument("--no-stacking", action="store_true")

    args = parser.parse_args()

    output = args.output
    if output is None:
        output = args.pdb.rsplit(".", 1)[0] + ".phil"

    stretches = read_base_pair_file(args.pairs)

    build_phil_from_pdb(
        args.pdb,
        stretches,
        output,
        parallels=not args.no_parallels,
        planes=not args.no_planes,
        include_stacking=not args.no_stacking,
    )

    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
