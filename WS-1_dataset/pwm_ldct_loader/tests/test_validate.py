import json
import os
import shutil

from pwm_ldct_loader import validate


def test_valid_fixture_passes(fixture_root):
    rep = validate(fixture_root)
    assert rep.ok, rep.errors
    assert rep.n_series == 2
    assert rep.n_patients == 2
    assert bool(rep) is True


def test_bad_schema_version_fails(fixture_root, tmp_path):
    dst = tmp_path / "copy"
    shutil.copytree(fixture_root, dst)
    mp = os.path.join(dst, "metadata", "lidc-0001_chest_fd.json")
    meta = json.load(open(mp))
    meta["schema_version"] = "9.9.9"
    json.dump(meta, open(mp, "w"))
    rep = validate(str(dst))
    assert not rep.ok
    assert any("schema_version" in e for e in rep.errors)


def test_missing_metadata_field_fails(fixture_root, tmp_path):
    dst = tmp_path / "copy2"
    shutil.copytree(fixture_root, dst)
    mp = os.path.join(dst, "metadata", "aapm-001_chest_fd.json")
    meta = json.load(open(mp))
    del meta["acquisition"]["recon_kernel"]
    json.dump(meta, open(mp, "w"))
    rep = validate(str(dst))
    assert not rep.ok
    assert any("recon_kernel" in e for e in rep.errors)
