"""Make the in-tree package importable without an install step (mirrors WS-1 baselines tests).

Also exposes the WS-2 ``pwm_dose_equivalence`` package: the sibling ``corpus_emit``
tool (loaded by path in emit_corpus) imports it to audit credentials, so the end-to-end
demo (test_demo.py) needs its ``src`` on ``sys.path`` in this repo-tree layout.
"""
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

_WS3_ROOT = Path(__file__).resolve().parents[2]
_WS2_SRC = _WS3_ROOT.parent / "WS-2_framework" / "pwm_dose_equivalence" / "src"
if _WS2_SRC.is_dir() and str(_WS2_SRC) not in sys.path:
    sys.path.insert(0, str(_WS2_SRC))
