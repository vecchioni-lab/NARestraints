
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable


@dataclass(frozen=True)
class ResidueRef:
    chain: str
    resid: str

    def selection(self) -> str:
        return f"chain {self.chain} and resid {self.resid}"


@dataclass(frozen=True)
class BasePair:
    base1: ResidueRef
    base2: ResidueRef


@dataclass(frozen=True)
class BasePairStretch:
    base1: tuple[ResidueRef, ...]
    base2: tuple[ResidueRef, ...]

    def __post_init__(self):
        if len(self.base1) != len(self.base2):
            raise ValueError(
                "Base-pair ranges must contain the same number of residues."
            )

    def pairs(self) -> tuple[BasePair, ...]:
        return tuple(BasePair(a, b) for a, b in zip(self.base1, self.base2))


_RANGE_RE = re.compile(r"^(-?\d+)(?:(?::|-)(-?\d+))?$")


def parse_residue_range(token: str) -> list[str]:
    """Parse 103, 103:108, or 108:103 into residue IDs."""
    token = token.strip()
    match = _RANGE_RE.fullmatch(token)
    if not match:
        raise ValueError(f"Invalid residue range: {token!r}")

    start = int(match.group(1))
    end = match.group(2)

    if end is None:
        return [str(start)]

    end = int(end)
    step = 1 if end >= start else -1
    return [str(i) for i in range(start, end + step, step)]


def _parse_chain_range(line: str) -> tuple[str, list[str]]:
    parts = line.split()
    if len(parts) != 2:
        raise ValueError(
            f"Expected '<chain> <residue-or-range>', got: {line!r}"
        )
    chain, range_token = parts
    return chain, parse_residue_range(range_token)


def read_base_pair_file(filename: str | Path) -> list[BasePairStretch]:
    """
    Read a simple human-editable base-pair specification.

    Each non-empty block contains exactly two lines:

        A 103:108
        C 214:209

    Blank lines separate stretches. Lines beginning with # are comments.
    """
    path = Path(filename)
    blocks: list[list[str]] = []
    current: list[str] = []

    for raw in path.read_text().splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            if current:
                blocks.append(current)
                current = []
            continue
        current.append(line)

    if current:
        blocks.append(current)

    stretches: list[BasePairStretch] = []
    for block in blocks:
        if len(block) != 2:
            raise ValueError(
                "Each base-pair block must contain exactly two lines. "
                f"Got {len(block)} lines: {block!r}"
            )

        chain1, residues1 = _parse_chain_range(block[0])
        chain2, residues2 = _parse_chain_range(block[1])

        stretches.append(
            BasePairStretch(
                tuple(ResidueRef(chain1, r) for r in residues1),
                tuple(ResidueRef(chain2, r) for r in residues2),
            )
        )

    return stretches
