"""Re-dump CREDENTIAL_JSON_SCHEMA to the top-level credential_schema.json file.

The repository-level ``credential_schema.json`` is a published artifact for
non-Python validators (a download URL, a JSON-Schema-aware editor's
``$schema`` reference, etc.). Keeping it byte-identical to the Python-side
``CREDENTIAL_JSON_SCHEMA`` constant is the discipline: run this script after
any schema edit, and ``tests/test_schema_artifact.py`` catches drift.

Run::

    python3 scripts/dump_schema.py
"""

from __future__ import annotations

import json
from pathlib import Path

from pwm_dose_equivalence.credential_schema import CREDENTIAL_JSON_SCHEMA

DEST = Path(__file__).resolve().parent.parent / "credential_schema.json"


def dump() -> None:
    with DEST.open("w", encoding="utf-8") as f:
        json.dump(CREDENTIAL_JSON_SCHEMA, f, indent=2, ensure_ascii=False)
        f.write("\n")


if __name__ == "__main__":  # pragma: no cover
    dump()
    print(f"Wrote {DEST}")
