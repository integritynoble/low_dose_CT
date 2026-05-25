from pwm_ldct_loader.splits import _bucket, assign_split


def test_deterministic():
    assert assign_split("lidc-0001", 42) == assign_split("lidc-0001", 42)


def test_buckets_in_range():
    assert all(0 <= _bucket(f"p{i}", 42) < 100 for i in range(100))


def test_only_valid_split_labels():
    labels = {assign_split(f"mayo-{i:03d}", 42) for i in range(300)}
    assert labels <= {"train", "val", "test"}


def test_roughly_60_20_20():
    n = 5000
    labels = [assign_split(f"pt-{i:05d}", 42) for i in range(n)]
    frac = {k: labels.count(k) / n for k in ("train", "val", "test")}
    assert abs(frac["train"] - 0.60) < 0.05
    assert abs(frac["val"] - 0.20) < 0.05
    assert abs(frac["test"] - 0.20) < 0.05


def test_seed_changes_some_assignments():
    changed = [assign_split(f"x{i}", 1) != assign_split(f"x{i}", 2) for i in range(300)]
    assert any(changed)
