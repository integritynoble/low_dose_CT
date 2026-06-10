"""Package the WS-3 derived-reconstruction corpus for deposit.

Two machine-derivable artifacts the deposit checklist (§3, §6) requires:

  1. ``MANIFEST.sha256`` — SHA-256 of every leaf file, ``sha256sum``-compatible
     (``<hash>␣␣<relpath>``), sorted by path. Verifiable with the system
     ``sha256sum -c MANIFEST.sha256`` or with :func:`verify_manifest`.
  2. ``dataset_metadata.json`` — the human-authored seed metadata with every
     machine-derivable field (per-record-type counts + sizes, top-level counts,
     total bytes) filled in from what is actually on disk.

The human fills the descriptive fields once (title, creators, DOI, licences,
related identifiers) in a *seed* file — by convention
``deposit/dataset_metadata.example.json`` — and this writer overlays the
counts. It never invents descriptive content.

CLI::

    python package_corpus.py package <corpus_root> --seed dataset_metadata.example.json
    python package_corpus.py verify  <corpus_root>

Programmatic::

    from package_corpus import package, verify_manifest
    report = package(corpus_root, seed_path)
    assert verify_manifest(corpus_root)["ok"]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Iterable

MANIFEST_NAME = "MANIFEST.sha256"
METADATA_NAME = "dataset_metadata.json"
_CHUNK = 1 << 20  # 1 MiB

__all__ = [
    "sha256_file",
    "iter_leaf_files",
    "write_manifest",
    "verify_manifest",
    "fill_metadata",
    "write_metadata",
    "package",
    "PackageError",
]


class PackageError(RuntimeError):
    """Raised on an inconsistency that should block deposit."""


# --------------------------------------------------------------------------- #
# Hashing + manifest
# --------------------------------------------------------------------------- #
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(_CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_leaf_files(corpus_root: Path, *, exclude: Iterable[str] = ()) -> list[Path]:
    """All files under ``corpus_root`` (sorted, posix-relative), minus ``exclude`` names."""
    exclude_set = set(exclude)
    files = [
        p
        for p in corpus_root.rglob("*")
        if p.is_file() and p.name not in exclude_set
    ]
    return sorted(files, key=lambda p: p.relative_to(corpus_root).as_posix())


def write_manifest(corpus_root: Path | str) -> Path:
    """Write ``MANIFEST.sha256`` covering every leaf file except the manifest itself.

    Run *after* :func:`write_metadata` so the manifest also covers
    ``dataset_metadata.json``.
    """
    corpus_root = Path(corpus_root)
    if not corpus_root.is_dir():
        raise PackageError(f"corpus root does not exist: {corpus_root}")
    lines = []
    for p in iter_leaf_files(corpus_root, exclude={MANIFEST_NAME}):
        rel = p.relative_to(corpus_root).as_posix()
        lines.append(f"{sha256_file(p)}  {rel}")
    manifest = corpus_root / MANIFEST_NAME
    manifest.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return manifest


def verify_manifest(corpus_root: Path | str) -> dict[str, Any]:
    """Recompute hashes and compare against the committed ``MANIFEST.sha256``.

    Returns ``{ok, n_checked, mismatched, missing, untracked}``. ``untracked``
    lists on-disk files absent from the manifest (excluding the manifest itself);
    a clean corpus has all four lists empty.
    """
    corpus_root = Path(corpus_root)
    manifest = corpus_root / MANIFEST_NAME
    if not manifest.exists():
        raise PackageError(f"no {MANIFEST_NAME} in {corpus_root}")

    recorded: dict[str, str] = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, rel = line.split("  ", 1)
        recorded[rel] = digest

    mismatched: list[str] = []
    missing: list[str] = []
    for rel, digest in recorded.items():
        p = corpus_root / rel
        if not p.exists():
            missing.append(rel)
        elif sha256_file(p) != digest:
            mismatched.append(rel)

    on_disk = {
        p.relative_to(corpus_root).as_posix()
        for p in iter_leaf_files(corpus_root, exclude={MANIFEST_NAME})
    }
    untracked = sorted(on_disk - set(recorded))

    return {
        "ok": not (mismatched or missing or untracked),
        "n_checked": len(recorded),
        "mismatched": sorted(mismatched),
        "missing": sorted(missing),
        "untracked": untracked,
    }


# --------------------------------------------------------------------------- #
# Metadata fill
# --------------------------------------------------------------------------- #
def _glob_stats(corpus_root: Path, path_glob: str) -> tuple[int, int]:
    """(count, total_bytes) of files matching a corpus-relative glob."""
    count = 0
    total = 0
    for p in corpus_root.glob(path_glob):
        if p.is_file():
            count += 1
            total += p.stat().st_size
    return count, total


def _derive_counts(corpus_root: Path) -> dict[str, Any]:
    """Top-level counts: distinct scans, patients, total data records, total bytes."""
    recon = corpus_root / "reconstructions"
    scan_dirs = (
        [d for d in recon.glob("*/*") if d.is_dir()] if recon.is_dir() else []
    )
    n_scans = len(scan_dirs)

    # Patients: read scan_meta.json patient ids if present, else fall back to scans.
    patients: set[str] = set()
    found_patient_field = False
    for meta in corpus_root.glob("reconstructions/*/*/r*/scan_meta.json"):
        try:
            d = json.loads(meta.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        pid = d.get("patient_id") or d.get("source_patient_id")
        if pid is not None:
            patients.add(str(pid))
            found_patient_field = True
    n_patients = len(patients) if found_patient_field else None

    total_bytes = sum(
        p.stat().st_size
        for p in iter_leaf_files(corpus_root, exclude={MANIFEST_NAME})
    )
    return {
        "n_scans": n_scans,
        "n_patients": n_patients,
        "total_bytes": total_bytes,
    }


def fill_metadata(seed: dict[str, Any], corpus_root: Path | str) -> dict[str, Any]:
    """Return a copy of ``seed`` with counts/sizes filled from disk.

    Fills, per ``record_types[]`` entry, ``count`` and ``total_bytes`` from its
    ``path_glob``; fills ``counts.{n_scans, n_records_total, total_bytes}`` and,
    when ``scan_meta.json`` carries a patient id, ``counts.n_patients``.
    Descriptive fields are left untouched.
    """
    corpus_root = Path(corpus_root)
    md = json.loads(json.dumps(seed))  # deep copy

    n_records_total = 0
    for rt in md.get("record_types", []):
        glob = rt.get("path_glob")
        if not glob:
            continue
        count, total = _glob_stats(corpus_root, glob)
        rt["count"] = count
        rt["total_bytes"] = total
        if rt.get("type") != "index":  # the jsonl index is not a data record
            n_records_total += count

    derived = _derive_counts(corpus_root)
    counts = md.setdefault("counts", {})
    counts["n_scans"] = derived["n_scans"]
    counts["n_records_total"] = n_records_total
    counts["total_bytes"] = derived["total_bytes"]
    if derived["n_patients"] is not None:
        counts["n_patients"] = derived["n_patients"]
    return md


def write_metadata(corpus_root: Path | str, seed_path: Path | str) -> Path:
    """Fill the seed metadata from disk and write ``dataset_metadata.json``."""
    corpus_root = Path(corpus_root)
    seed = json.loads(Path(seed_path).read_text(encoding="utf-8"))
    md = fill_metadata(seed, corpus_root)
    out = corpus_root / METADATA_NAME
    out.write_text(json.dumps(md, indent=2) + "\n", encoding="utf-8")
    return out


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def _validate_against_schema(md: dict[str, Any], schema_path: Path) -> list[str]:
    try:
        import jsonschema
    except ImportError:
        return []  # validation is best-effort; skipped if jsonschema absent
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = sorted(
        jsonschema.Draft7Validator(schema).iter_errors(md),
        key=lambda e: e.path,
    )
    return [f"{list(e.path)}: {e.message}" for e in errors]


def package(
    corpus_root: Path | str,
    seed_path: Path | str,
    *,
    schema_path: Path | str | None = None,
    require_schema_valid: bool = False,
) -> dict[str, Any]:
    """Write ``dataset_metadata.json`` then ``MANIFEST.sha256``; return a report.

    Order matters: metadata is written first so the manifest covers it. When a
    schema is given, the filled metadata is validated; with
    ``require_schema_valid`` a violation raises :class:`PackageError`.
    """
    corpus_root = Path(corpus_root)
    meta_path = write_metadata(corpus_root, seed_path)
    md = json.loads(meta_path.read_text(encoding="utf-8"))

    schema_errors: list[str] = []
    if schema_path is not None:
        schema_errors = _validate_against_schema(md, Path(schema_path))
        if schema_errors and require_schema_valid:
            raise PackageError(f"metadata fails schema: {schema_errors}")

    manifest_path = write_manifest(corpus_root)
    n_files = len(manifest_path.read_text(encoding="utf-8").splitlines())

    return {
        "metadata": str(meta_path),
        "manifest": str(manifest_path),
        "n_files_in_manifest": n_files,
        "counts": md.get("counts", {}),
        "record_type_counts": {
            rt["type"]: rt.get("count", 0) for rt in md.get("record_types", [])
        },
        "schema_errors": schema_errors,
    }


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Package or verify the WS-3 corpus.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_pkg = sub.add_parser("package", help="write dataset_metadata.json + MANIFEST.sha256")
    p_pkg.add_argument("corpus_root", type=Path)
    p_pkg.add_argument(
        "--seed",
        type=Path,
        default=Path(__file__).with_name("dataset_metadata.example.json"),
        help="seed metadata with descriptive fields (default: dataset_metadata.example.json)",
    )
    p_pkg.add_argument(
        "--schema",
        type=Path,
        default=Path(__file__).with_name("dataset_metadata.schema.json"),
    )
    p_pkg.add_argument("--require-schema-valid", action="store_true")

    p_ver = sub.add_parser("verify", help="verify MANIFEST.sha256 against disk")
    p_ver.add_argument("corpus_root", type=Path)

    args = parser.parse_args(argv)

    if args.cmd == "package":
        report = package(
            args.corpus_root,
            args.seed,
            schema_path=args.schema,
            require_schema_valid=args.require_schema_valid,
        )
        print(json.dumps(report, indent=2))
        return 1 if report["schema_errors"] and args.require_schema_valid else 0

    if args.cmd == "verify":
        report = verify_manifest(args.corpus_root)
        print(json.dumps(report, indent=2))
        return 0 if report["ok"] else 1

    return 2


if __name__ == "__main__":
    sys.exit(main())
