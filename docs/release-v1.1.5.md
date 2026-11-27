# NARestraints v1.1.5

In a canonical pseudouridine–adenine pair the N3–H donor faces adenine N1
and the O2 acceptor faces adenine N6. Attaching the sugar through ring C5
puts O2 on this pairing edge. In ordinary uridine the sugar attaches at N1
and O4 faces adenine N6. An older release selected two atoms that both
existed in the dictionary, even though one faced the other side of the base.

In 20 deposited NMR conformers across two RNA duplexes, pseudouridine O2
lies 2.92–2.94 Å from adenine N6. O4 lies 5.27–5.34 Å away. Each duplex
also contains an ordinary uridine–adenine pair with O4 next to N6. The
contact assignment agrees with solution studies. [Deb et al.](https://doi.org/10.1038/s41598-019-52637-0).
[Kierzek et al.](https://doi.org/10.1093/nar/gkt1330).

The same O2 contact measures 2.90 Å in the PSU crystal duplex 3CGP.
Two pairs in the 1.01 Å N1-methylpseudouridine structure 8PFQ measure
3.01 and 3.22 Å. The 1.32 Å crystal structure 8PFK gives 3.09 Å across
symmetry. These observations support PSU and the N1-methyl derivative B8H
directly. P2U and UY1 use the same neutral dioxopyrimidine ring and C5
attachment. Applying the pairing assignment to those two derivatives is
a chemical inference. [3CGP](https://www.rcsb.org/structure/3CGP).
[8PFQ and 8PFK study](https://doi.org/10.1002/cmdc.202300600).

The four rows declare `O2` in the optional `A:T acceptor role` column.
The pair writer and guesser use that mapped atom in the contact and its
associated angle. The physical atoms retain their existing names in the base
plane and stacking selections. A model missing the declared acceptor cannot
supply that contact. Older workbooks retain their earlier assignments.
Current evidence covers neutral canonical pairs to adenine. Alternative
pairing faces, metal coordination and protonation states need their own evidence.
[Exact workbook edits](workbook-audit-2026-11-27.json).

## Install

```bash
python -m pip install "https://github.com/vecchioni-lab/NARestraints/releases/download/v1.1.5/narestraints-1.1.5-py3-none-any.whl"
narestraints --help
```

Python 3.10 or newer is supported. The workbook SHA-256 is
`ad4e626dd2fa7d9fe6f05d059b8ff08b31d3f09b13027785b6303cb2df956c83`.
The release workflow builds and installs both wheel and source distribution
outside the source checkout on Python 3.10, 3.12 and 3.14.
