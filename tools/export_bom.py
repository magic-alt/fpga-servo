"""Export a review BOM from the authored native schematic symbols."""
from pathlib import Path
import csv
import re
from kicad_native import extract_forms, property_value, strip_form

root = Path(__file__).resolve().parents[1]
rows = []
for path in sorted((root / "hardware").glob("*.kicad_sch")):
    text = strip_form(path.read_text(encoding="utf-8"), "lib_symbols")
    for symbol in extract_forms(text, "symbol"):
        ref = property_value(symbol.text, "Reference")
        if not ref or ref.startswith("#"):
            continue
        mpn = property_value(symbol.text, "MPN") or "TBD"
        dnp = "(dnp yes)" in symbol.text
        note = "DNP; populate only after option review" if dnp else "Fitted"
        if "(on_board no)" in symbol.text:
            note = "External; NOT fitted to PCB"
            holder = property_value(symbol.text, "Holder_MPN")
            if holder:
                note += "; required holder " + holder
        if mpn == "TBD":
            note += "; exact MPN / rating qualification open"
        rows.append({
            "Ref": ref, "Qty": 1,
            "Value / Part": property_value(symbol.text, "Value"),
            "Manufacturer": property_value(symbol.text, "Manufacturer") or "TBD",
            "MPN": mpn,
            "Package": property_value(symbol.text, "Footprint"),
            "Function": property_value(symbol.text, "Description") or "See schematic",
            "Status / note": note,
        })
rows.sort(key=lambda row: (re.sub(r"\d+", "", row["Ref"]), int(re.search(r"\d+", row["Ref"]).group())))
with (root / "hardware/bom.csv").open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
print(f"BOM exported: {len(rows)} components")
