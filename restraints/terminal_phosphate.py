from __future__ import annotations

from collections.abc import Iterable


# CSD-derived terminal phosphomonoester geometry from
# Kowiel et al., Nucleic Acids Research 44 (2016) 8479-8489,
# terminal C-O-PO3(2-) analysis / Supplementary Table S3.
#
# Only the three angles involving the explicitly present OP3 atom are emitted
# here. Phenix already supplies the ordinary nucleotide P/OP1/OP2/O5' geometry,
# and in current Phenix versions also recognizes the P-OP3 bond. Adding only
# the missing OP3 angles avoids duplicate bond restraints while closing the
# rotational degree of freedom observed for terminal OP3 during refinement.
TERMINAL_OP3_ANGLES = (
    ("OP1", "P", "OP3", 114.0, 0.7),
    ("OP2", "P", "OP3", 112.8, 1.0),
    ("OP3", "P", "O5'", 102.9, 1.2),
)

_REQUIRED_ATOMS = frozenset({"P", "OP1", "OP2", "OP3", "O5'"})


def _selection(chain: str, resid: str, atom: str) -> str:
    return f"chain {chain} and resid {resid} and name {atom}"


def _angle_block(
    chain: str,
    resid: str,
    atom1: str,
    atom2: str,
    atom3: str,
    ideal: float,
    sigma: float,
) -> str:
    return "\n".join(
        [
            "    angle {",
            "      action = add",
            f"      atom_selection_1 = {_selection(chain, resid, atom1)}",
            f"      atom_selection_2 = {_selection(chain, resid, atom2)}",
            f"      atom_selection_3 = {_selection(chain, resid, atom3)}",
            f"      angle_ideal = {ideal:g}",
            f"      sigma = {sigma:g}",
            "    }",
        ]
    )


def generate_terminal_phosphate_restraints(
    chain: str,
    resid: str,
    atom_names: Iterable[str],
) -> str:
    """Return the missing OP3 angle restraints for one declared 5'-phosphate.

    This is intentionally explicit-site chemistry. The caller must already have
    decided that the residue is a terminal phosphomonoester; this function does
    not infer terminal status from coordinates or distances. All five atoms
    required to define the local phosphate geometry must be present.
    """
    chain = str(chain).strip()
    resid = str(resid).strip()
    if not chain or not resid:
        raise ValueError("Terminal phosphate site requires non-empty chain and residue id")

    present = {str(name).strip().upper().replace("O1P", "OP1").replace("O2P", "OP2").replace("O3P", "OP3") for name in atom_names}
    missing = sorted(_REQUIRED_ATOMS - present)
    if missing:
        raise ValueError(
            f"Terminal phosphate {chain}:{resid} is missing required atom(s): "
            + ", ".join(missing)
        )

    return "\n\n".join(
        _angle_block(chain, resid, atom1, atom2, atom3, ideal, sigma)
        for atom1, atom2, atom3, ideal, sigma in TERMINAL_OP3_ANGLES
    )
