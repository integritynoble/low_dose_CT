"""Tests for the artefact-class sub-score layer (low-dose-ct.md §7.5, P2-6)."""

from __future__ import annotations

import numpy as np
import pytest

from pwm_ldct_recon.artefacts import (
    ARTEFACT_CLASSES,
    ArtefactScore,
    artefact_class_names,
    empty_artefact_block,
    register_artefact_probe,
    validate_artefact_report,
)


def test_registry_has_expected_classes():
    names = artefact_class_names()
    assert "metal" in names
    assert "motion" in names
    assert "truncation" in names
    assert "ring_streak" in names


def test_artefact_score_ok_paired():
    s = ArtefactScore(artefact_class="metal", psnr_db=31.0, cnr=4.2)
    assert s.ok is True
    d = s.to_dict()
    assert d["fidelity"]["psnr_db"] == 31.0
    assert d["detectability"]["cnr"] == 4.2
    assert d["detectability"]["pass_threshold"] is True


def test_artefact_score_fails_rose_criterion():
    s = ArtefactScore(artefact_class="motion", psnr_db=31.0, cnr=1.5)
    assert s.ok is False


def test_artefact_score_nonfinite_not_ok():
    s = ArtefactScore(artefact_class="truncation", psnr_db=float("nan"), cnr=4.0)
    assert s.ok is False


def test_validate_artefact_report_accepts_valid():
    report = {
        "enabled": True,
        "artefact_scores": [
            ArtefactScore("metal", 30.0, 4.0).to_dict(),
            ArtefactScore("ring_streak", 28.0, 3.5).to_dict(),
        ],
    }
    assert validate_artefact_report(report) == []


def test_validate_artefact_report_rejects_unknown_class():
    report = {"artefact_scores": [{"artefact_class": "quantum_ghost", "fidelity": {"psnr_db": 1.0}, "detectability": {"cnr": 1.0}}]}
    problems = validate_artefact_report(report)
    assert any("unknown artefact_class" in p for p in problems)


def test_validate_artefact_report_rejects_unpaired():
    report = {"artefact_scores": [{"artefact_class": "metal", "fidelity": {"psnr_db": 1.0}}]}
    problems = validate_artefact_report(report)
    assert any("paired metrics required" in p for p in problems)


def test_validate_artefact_report_rejects_duplicate():
    report = {
        "artefact_scores": [
            ArtefactScore("metal", 30.0, 4.0).to_dict(),
            ArtefactScore("metal", 29.0, 3.9).to_dict(),
        ]
    }
    problems = validate_artefact_report(report)
    assert any("duplicate" in p for p in problems)


def test_empty_artefact_block_is_schema_shaped():
    block = empty_artefact_block()
    assert block["enabled"] is True
    assert block["artefact_scores"] == []
    assert validate_artefact_report(block) == []


def test_register_artefact_probe_additive():
    def probe(_input):
        return {"psnr_db": 25.0, "cnr": 3.2}

    register_artefact_probe("motion", probe)
    assert callable(ARTEFACT_CLASSES["motion"].get("probe"))
