"""Residue library for standard and modified nucleic acids."""

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

import openpyxl


def load_residue_records(workbook_path):
    """Return full residue records from the authoritative sheets."""
    workbook = openpyxl.load_workbook(workbook_path, read_only=True)

    records = []

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
            record["Glycosidic atom"] = row[headers.index("Function") + 1]

            records.append(record)

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
    metadata_fields = {
        "Ligand code",
        "Name",
        "Abbreviation",
        "Base Analog",
        "Phosphate",
        "Sugar Type",
        "Saenger",
        "Notes",
        "Ref",
        "Entries",
        "Function",
        "Source sheet",
        "Glycosidic atom",
    }

    return {
        value
        for key, value in record.items()
        if key not in metadata_fields and value is not None
    }