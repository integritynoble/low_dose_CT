#!/usr/bin/env python3
"""Stage the PWM-LDCT v0.5 deposit tree and mint its content address.

Implements Steps 1 and 2 of ``deposit_procedure.md``: assemble exactly the
deposited artifacts, write ``manifest.sha256``, and compute the ``CONTENT_HASH``
that is cited in the paper and recorded in PhysioNet and Zenodo.

    python3 stage_deposit.py --source <built-records-root> --out <deposit-dir>
    python3 stage_deposit.py --source ... --out ... --dry-run   # report, copy nothing

The built records (``annotations/``, ``sim_lowdose/lidc/``, ``metadata/``,
``splits/``, ``deident_audit.jsonl``) are **not** in this repository; they come
from ``gs://low-dose-ct/pwm_ldct_v0_5`` or from the machine that built them.
Point ``--source`` at a directory holding them. The code half is taken from the
repository automatically.

What this refuses to do
-----------------------
The deposit excludes the AAPM/Mayo DICOM and their DUA-restricted pixel
derivatives (``deposit_procedure.md``, "What is deposited"); users regenerate
those locally. Eight Mayo-derived ``L506_*.npy`` files were once committed to
this repository and had to be removed from git history on 2026-09-05, so that
exclusion is enforced here as a **refusal**, not a silent skip: if a restricted
file is found anywhere in the staged tree the script stages nothing, reports
every offender, and exits non-zero. A quiet skip would let a DUA breach leave
no trace in the log.

Reproducibility note
--------------------
``manifest.sha256`` hashes raw bytes, so a text file checked out with CRLF
hashes differently from the same file with LF. The trap provenance in WS-4 hit
exactly this. The manifest written here always uses LF line endings, and the
repository's ``.gitattributes`` should keep the deposited text artifacts
byte-identical across platforms. Stage on one platform, or verify the
CONTENT_HASH agrees across them before publishing it.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import sys
from typing import Dict, Iterable, List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
WS1 = os.path.dirname(HERE)
REPO = os.path.dirname(WS1)

# --- what the deposit contains (deposit_procedure.md Step 1) ----------------
# Data records: staged from --source, since they are not in the repository.
DATA_PARTS = [
    ("annotations", "dir"),
    ("sim_lowdose/lidc", "dir"),
    ("metadata", "dir"),
    ("splits", "dir"),
    ("deident_audit.jsonl", "file"),
]
# Code: staged from the repository, under code/.
CODE_PARTS = [
    ("pwm_ldct_loader", os.path.join(WS1, "pwm_ldct_loader")),
    ("pipelines/pwm_ldct_prep", os.path.join(WS1, "pipelines", "pwm_ldct_prep")),
    ("baselines", os.path.join(WS1, "baselines")),
    ("schema", os.path.join(WS1, "schema")),
]

# --- build cruft: skipped silently, they are noise not hazards --------------
SKIP_DIRS = {"__pycache__", ".git", ".pytest_cache", ".venv", "node_modules"}
SKIP_SUFFIX = (".pyc", ".pyo", ".egg-info", ".bak", ".legacy", ".flag", ".log.err")

# --- DUA-restricted: staging REFUSES if any of these appear ----------------
# Mayo/AAPM patient pixel derivatives (LNNN_*.npy/npz), DICOM in any form, and
# the harmonized AAPM/Mayo HDF5 the procedure excludes by name.
RESTRICTED = [
    (re.compile(r"(^|/)L\d{3}_[^/]*\.(npy|npz)$", re.I),
     "Mayo/AAPM patient pixel derivative (LNNN_*.npy/npz)"),
    (re.compile(r"\.(dcm|dicom)$", re.I), "DICOM"),
    (re.compile(r"(^|/)DICOMDIR$", re.I), "DICOM directory record"),
    (re.compile(r"(^|/)(aapm|mayo)[^/]*\.(h5|hdf5)$", re.I),
     "harmonized AAPM/Mayo HDF5 (DUA-restricted)"),
]


def skipped(rel: str) -> bool:
    parts = rel.split("/")
    if any(p in SKIP_DIRS for p in parts):
        return True
    return rel.endswith(SKIP_SUFFIX)


def restricted_reason(rel: str) -> str | None:
    for pat, why in RESTRICTED:
        if pat.search(rel):
            return why
    return None


def walk(root: str) -> Iterable[str]:
    """Relative paths of every file under *root*, build cruft excluded."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for fn in sorted(filenames):
            rel = os.path.relpath(os.path.join(dirpath, fn), root).replace(os.sep, "/")
            if not skipped(rel):
                yield rel


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def collect(source: str) -> Tuple[List[Tuple[str, str]], List[str]]:
    """Return (pairs, missing) where pairs is [(src_abs, dest_rel), ...]."""
    pairs: List[Tuple[str, str]] = []
    missing: List[str] = []

    for rel, kind in DATA_PARTS:
        src = os.path.join(source, rel)
        if not os.path.exists(src):
            missing.append(rel)
            continue
        if kind == "file":
            pairs.append((src, rel))
        else:
            for sub in walk(src):
                pairs.append((os.path.join(src, sub), f"{rel}/{sub}"))

    for dest_rel, src in CODE_PARTS:
        if not os.path.isdir(src):
            missing.append(f"code/{dest_rel} (repo)")
            continue
        for sub in walk(src):
            pairs.append((os.path.join(src, sub), f"code/{dest_rel}/{sub}"))

    return pairs, missing


README = """\
# PWM-LDCT v0.5 — deposit

Openly licensed data records and code for the PWM Low-Dose CT benchmark, v0.5
(LIDC-IDRI first release).

The AAPM/Mayo DICOM and their DUA-restricted pixel derivatives are **not**
included; they are obtained from their own gatekeepers and regenerated locally.
See the Data Records table in the manuscript.

- Paper: see the associated publication linked from this record.
- Source repository: https://github.com/integritynoble/low_dose_CT
- Licences: annotations CC BY 4.0 / CC BY 3.0; simulated low-dose CC BY 3.0
  (LIDC-derived); code Apache-2.0.

Integrity: `manifest.sha256` lists a SHA-256 for every other file in this tree.
The deposit's content address is the SHA-256 of `manifest.sha256` itself; it is
recorded in the paper and in each deposit channel, and all channels must agree.

Verify with:

    python -c "from pwm_ldct_loader import validate; r=validate('.'); print(r.ok, r.errors[:3])"
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True,
                    help="directory holding the built data records "
                         "(annotations/, sim_lowdose/, metadata/, splits/, deident_audit.jsonl)")
    ap.add_argument("--out", required=True, help="deposit tree to create")
    ap.add_argument("--dry-run", action="store_true", help="report only; copy nothing")
    ap.add_argument("--force", action="store_true", help="overwrite a non-empty --out")
    args = ap.parse_args()

    if not os.path.isdir(args.source):
        print(f"error: --source is not a directory: {args.source}", file=sys.stderr)
        return 2

    pairs, missing = collect(args.source)
    if not pairs:
        print("error: nothing to stage; is --source the built-records root?", file=sys.stderr)
        return 2

    # --- the refusal, before anything is written ---------------------------
    offenders = [(rel, why) for _, rel in pairs
                 if (why := restricted_reason(rel)) is not None]
    if offenders:
        print("REFUSING to stage: DUA-restricted files are present.\n", file=sys.stderr)
        for rel, why in offenders:
            print(f"  {rel}\n      -> {why}", file=sys.stderr)
        print(f"\n{len(offenders)} restricted file(s). The deposit excludes the AAPM/Mayo "
              "DICOM and their pixel derivatives (deposit_procedure.md, 'What is "
              "deposited'). Remove them from the source tree, or correct --source, "
              "and run again. Nothing was written.", file=sys.stderr)
        return 3

    total = sum(os.path.getsize(src) for src, _ in pairs)
    print(f"staging {len(pairs)} files, {total/1048576:.1f} MB")
    if missing:
        print("\nWARNING: expected parts not found under --source (or the repo):")
        for m in missing:
            print(f"  missing: {m}")
        print("  A deposit without these is incomplete; check --source before publishing.")

    if args.dry_run:
        by_top: Dict[str, int] = {}
        for _, rel in pairs:
            by_top[rel.split("/")[0]] = by_top.get(rel.split("/")[0], 0) + 1
        print("\nwould stage:")
        for k in sorted(by_top):
            print(f"  {k:16s} {by_top[k]:5d} files")
        print("\n(dry run; nothing written, no manifest, no CONTENT_HASH)")
        return 0

    if os.path.exists(args.out) and os.listdir(args.out) and not args.force:
        print(f"error: {args.out} exists and is not empty (use --force)", file=sys.stderr)
        return 2

    for src, rel in pairs:
        dest = os.path.join(args.out, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(src, dest)

    with open(os.path.join(args.out, "README.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(README)

    # --- Step 2: manifest + content address --------------------------------
    entries = sorted(walk(args.out))
    entries = [e for e in entries if e != "manifest.sha256"]
    manifest_path = os.path.join(args.out, "manifest.sha256")
    with open(manifest_path, "w", encoding="utf-8", newline="\n") as fh:
        for rel in entries:
            fh.write(f"{sha256_file(os.path.join(args.out, rel))}  {rel}\n")

    content_hash = sha256_file(manifest_path)
    print(f"\nmanifest.sha256   {len(entries)} files")
    print(f"CONTENT_HASH      {content_hash}")
    print("\nRecord CONTENT_HASH in the paper, PhysioNet and Zenodo; all three must agree.")
    print("Next: validate the tree, then deposit_procedure.md Step 3.")
    print(f'  python -c "from pwm_ldct_loader import validate; '
          f"r=validate('{args.out}'); print(r.ok, r.errors[:3])\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
