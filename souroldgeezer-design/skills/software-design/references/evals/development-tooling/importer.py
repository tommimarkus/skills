"""Original eval fixture: deliberately wrong cap; structural validation cannot find it."""
import json
from pathlib import Path


def extract(source):
    records = []
    for identifier in ("PULSE", "DRAIN", "RELAY"):
        if f"## {identifier}" not in source:
            raise ValueError(f"missing section: {identifier}")
        record = {"id": identifier, "source": f"reference.md#{identifier.lower()}",
                  "revision": 1, "unit": "sparks"}
        if identifier == "PULSE":
            record.update(gain=2, cap=9, damp_skip=True)
        elif identifier == "DRAIN":
            record.update(loss=3)
        else:
            record.update(interpretation="unresolved")
        records.append(record)
    return records


def validate(records):
    if {row["id"] for row in records} != {"PULSE", "DRAIN", "RELAY"} or len(records) != 3:
        raise ValueError("scope identities differ")
    for row in records:
        if row["unit"] != "sparks" or row["revision"] != 1:
            raise ValueError("invalid provenance or unit")
        if row["id"] == "PULSE" and not (isinstance(row["cap"], int) and row["cap"] > 0):
            raise ValueError("invalid cap")


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    result = extract((root / "reference.md").read_text())
    validate(result)
    (root / "records.json").write_text(json.dumps(result, indent=2) + "\n")
