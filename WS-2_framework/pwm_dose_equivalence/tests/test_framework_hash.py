"""Tests for the content-addressed framework hash."""

from __future__ import annotations

import hashlib

from pwm_dose_equivalence.framework_hash import FRAMEWORK_SPEC, framework_hash


def test_hash_is_sha256_prefixed():
    h = framework_hash()
    assert h.startswith("sha256:")
    # 64 hex chars after the prefix
    assert len(h) == len("sha256:") + 64


def test_hash_is_stable_across_calls():
    assert framework_hash() == framework_hash()


def test_hash_matches_hashlib():
    expected = hashlib.sha256(FRAMEWORK_SPEC.encode("utf-8")).hexdigest()
    assert framework_hash() == f"sha256:{expected}"


def test_hash_changes_when_spec_changes():
    h_default = framework_hash()
    h_mutated = framework_hash(FRAMEWORK_SPEC + "\nadditional-field: x")
    assert h_default != h_mutated


def test_spec_contains_v02_marker():
    """Sanity: the spec advertises v0.2 so credentials issued under this
    library version are correctly versioned."""
    assert "v0.2" in FRAMEWORK_SPEC
