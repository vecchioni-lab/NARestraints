"""Residue library for standard and modified nucleic acids."""

from importlib.resources import as_file, files

import openpyxl

AUTHORITATIVE_SHEETS = [
    "adenine",
    "thymine",
    "guanine",
    "cytosine",
    "D",
    "B",
    "S",
    "Z",
    "P",
    "I",
    "X",
    "K",
    "unique",
]


# These columns describe a residue or its sugar attachment. They never supply
# a base atom for pairing, stacking or automatic atom-name repair.
_BASE_METADATA = {
    "Ligand code", "Name", "Abbreviation", "Base Analog", "Phosphate",
    "Sugar Type", "SugarType", "Saenger", "Notes", "Ref", "Entries",
    "Function", "Source sheet", "Glycosidic atom", "Backbone attachment atom",
    "A:T acceptor role",
}


def base_atom_items(record):
    """Yield workbook roles belonging to the base, including mapped substituents."""
    backbone = record.get("Backbone attachment atom")
    for role, atom in record.items():
        if role not in _BASE_METADATA and atom is not None and atom != backbone:
            yield role, atom


def load_residue_records(workbook_path=None):
    """Return residue records from a workbook or the bundled default.

    ``workbook_path`` remains optional for backward compatibility with callers
    that supply an explicit path.  When it is omitted, the active
    ``restraints/data/Ligands.xlsx`` package resource is used, independently of
    the process's current working directory.
    """
    if workbook_path is not None:
        return _load_residue_records(workbook_path)

    workbook_resource = files(__package__).joinpath("data", "Ligands.xlsx")
    with as_file(workbook_resource) as bundled_workbook:
        return _load_residue_records(bundled_workbook)


def _load_residue_records(workbook_path):
    """Load residue records from a resolved filesystem path."""
    workbook = openpyxl.load_workbook(workbook_path, read_only=True)

    records = []
    try:
        for sheet_name in AUTHORITATIVE_SHEETS:
            sheet = workbook[sheet_name]

            rows = [
                [cell.value for cell in row]
                for row in sheet.iter_rows()
                if any(cell.value is not None for cell in row)
            ]

            headers = rows[0]

            for row in rows[1:]:
                if row[0] is None:
                    continue

                record = {
                    header: value
                    for header, value in zip(headers, row)
                    if header is not None
                }
                record["Ligand code"] = str(record["Ligand code"])
                record["Source sheet"] = sheet_name
                if not record.get("Glycosidic atom"):
                    record["Glycosidic atom"] = row[headers.index("Function") + 1]
                if not record.get("Backbone attachment atom"):
                    record.pop("Backbone attachment atom", None)

                if not record.get("A:T acceptor role"):
                    record.pop("A:T acceptor role", None)
                records.append(record)
    finally:
        workbook.close()

    return records


def find_residue(records, ligand_code):
    """Return all records matching a ligand code."""
    ligand_code = str(ligand_code)

    return [
        record
        for record in records
        if record["Ligand code"] == ligand_code
    ]


def canonical_atom_name(record, canonical_position):
    """Return the actual PDB atom name for a canonical base position."""
    return record.get(canonical_position)


def heterocycle_atom_names(record):
    """Return actual PDB atom names that belong to the mapped heterocycle."""
    return {atom for _, atom in base_atom_items(record)}
