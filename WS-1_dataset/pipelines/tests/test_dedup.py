"""Cross-source de-duplication in write_splits: a physical patient appearing in two sources
(same canonical key) is assigned to ONE split and listed once (no leakage, no double-count)."""
import json
import os

from pwm_ldct_prep.writers import write_splits


def _meta(out, pid, ckey, seed=42):
    os.makedirs(os.path.join(out, "metadata"), exist_ok=True)
    series = f"{pid}_abdomen_fd"
    json.dump(
        {"patient_id": pid, "series_id": series, "lowdose_sim": {"seed": seed},
         "provenance": {"canonical_patient_key": ckey}},
        open(os.path.join(out, "metadata", f"{series}.json"), "w"),
    )


def test_cross_source_dedup(tmp_path):
    out = str(tmp_path / "tree")
    # mayo-0001 and aapm-0001 are the SAME physical patient (shared canonical key)
    _meta(out, "mayo-0001", "SHAREDKEYAAAA")
    _meta(out, "aapm-0001", "SHAREDKEYAAAA")
    _meta(out, "mayo-0002", "OTHERKEYBBBBB")
    write_splits(out)

    splits = {s: open(os.path.join(out, "splits", f"{s}.txt")).read().split()
              for s in ("train", "val", "test")}
    listed = [p for v in splits.values() for p in v]

    # the duplicate is listed once, as the deterministic representative (smallest id)
    assert "aapm-0001" in listed and "mayo-0001" not in listed
    assert "mayo-0002" in listed
    # no patient appears in two splits (no leakage); two distinct physical patients total
    assert len(listed) == len(set(listed)) == 2
