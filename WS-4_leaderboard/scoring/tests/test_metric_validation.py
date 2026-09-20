"""Invalid numeric evidence must not become a published board entry."""
import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scoring import add_submission, check_paired_submission, new_leaderboard, save
from scoring.task_spec import (DETECTABILITY_FIELDS, FIDELITY_FIELDS,
                               FREQ_SUPPLEMENTARY_FIELDS, TASK_LABEL)
from scoring.verify import provenance_sha256

FIELDS = FIDELITY_FIELDS + DETECTABILITY_FIELDS + FREQ_SUPPLEMENTARY_FIELDS
INVALID = [float('nan'), float('inf'), float('-inf'), True, False, '0.63', [], {}]
WS4 = Path(__file__).resolve().parents[2]


def claim_block():
    """§2-D: a self-consistent claim + evidence block bound to the WS-4 task."""
    manifest = {"corpus": "LIDC lowdose_sim", "r": 0.25, "seed": 42, "n_patients": 2}
    weights = {"arch": "conv", "params": 1000}
    return {
        "claim": {
            "task_id": TASK_LABEL,
            "protocol_id": "detectability-freq-v1",
            "data_manifest_sha256": provenance_sha256(manifest),
            "model_sha256": provenance_sha256(weights),
            "evaluator_version": "pwm_ldct_recon-2026-09-14",
        },
        "evidence": {"data_manifest": manifest, "model_weights": weights},
    }


def metrics():
    return {'psnr_db': 40.0, 'ssim': 0.9, 'bander_roi': 3.85,
            'task': 'SKE-Gaussian20HU-s2px'}


@pytest.mark.parametrize('field', FIELDS)
@pytest.mark.parametrize('value', INVALID)
def test_invalid_reported_metric_is_rejected(field, value):
    payload = metrics()
    payload[field] = value
    errors = check_paired_submission(payload)
    assert any(field in e and 'finite number' in e for e in errors)
    board = new_leaderboard()
    before = copy.deepcopy(board)
    with pytest.raises(ValueError, match='finite number'):
        add_submission(board, payload, method='invalid')
    assert board == before


def test_valid_numbers_and_absent_optional_metrics_remain_accepted():
    payload = metrics()
    payload.update(cnr_mean=None, npwe_mean=0, bander_full=0.0)
    assert check_paired_submission(payload) == []
    payload['psnr_db'] = None
    assert check_paired_submission(payload) == []  # SSIM alone is valid fidelity.
    payload['bander_roi'] = None
    assert check_paired_submission(payload)  # Required evidence is now absent.


def test_invalid_later_method_does_not_partially_mutate_board():
    board = new_leaderboard()
    before = copy.deepcopy(board)
    payload = {'validation': {'paired_methods': {
        'good': {'psnr_db': 40.0,
                 'detectability': {'bander_roi': 3.85, 'task': TASK_LABEL}},
        'bad': {'psnr_db': 40.0,
                'detectability': {'bander_roi': float('nan'), 'task': TASK_LABEL}},
    }}}
    payload.update(claim_block())
    with pytest.raises(ValueError, match='finite number'):
        add_submission(board, payload, method='mixed')
    assert board == before


@pytest.mark.parametrize('existing_board', [False, True])
@pytest.mark.parametrize('value', INVALID)
def test_cli_refuses_invalid_evidence_before_writing(tmp_path, existing_board, value):
    board_path = tmp_path / 'board.json'
    if existing_board:
        save(new_leaderboard(), board_path)
    before = board_path.read_bytes() if existing_board else None
    payload = {'validation': {'paired_methods': {
        'good': {'psnr_db': 40.0,
                 'detectability': {'bander_roi': 3.85, 'task': TASK_LABEL}},
        'bad': {'psnr_db': 40.0,
                'detectability': {'bander_roi': value, 'task': TASK_LABEL}},
    }}}
    payload.update(claim_block())
    result_path = tmp_path / 'result.json'
    result_path.write_text(json.dumps(payload), encoding='utf-8')
    env = dict(os.environ, PYTHONPATH=str(WS4), PYTHONDONTWRITEBYTECODE='1')
    for command in ('validate', 'submit'):
        args = [sys.executable, '-m', 'scoring.cli', command, '--result', str(result_path)]
        if command == 'submit':
            args += ['--method', 'invalid', '--out', str(board_path)]
        result = subprocess.run(args, cwd=tmp_path, env=env, capture_output=True, text=True)
        assert result.returncode == 1, result.stdout + result.stderr
        assert 'bander_roi' in result.stdout + result.stderr
        assert (board_path.read_bytes() if board_path.exists() else None) == before


def test_cli_valid_submission_publishes(tmp_path):
    result_path = tmp_path / 'result.json'
    payload = metrics()
    payload.update(claim_block())
    result_path.write_text(json.dumps(payload), encoding='utf-8')
    board_path = tmp_path / 'board.json'
    result = subprocess.run(
        [sys.executable, '-m', 'scoring.cli', 'submit', '--result', str(result_path),
         '--method', 'valid', '--out', str(board_path)], cwd=tmp_path,
        env=dict(os.environ, PYTHONPATH=str(WS4)), capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'accepted' in result.stdout
    assert any(e['method'] == 'valid' for e in json.loads(board_path.read_text())['entries'])
