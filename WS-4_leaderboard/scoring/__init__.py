"""scoring package for the WS-4 leaderboard."""
from .task_spec import BLUR_SPEC, TASK_SPEC
from .verify import check_paired_submission, check_submission_result, extract_paired_methods
from .leaderboard import (BLUR_ENTRY_ID, REFERENCE_ENTRY_ID, TRAP_MIN_SEPARATION,
                          add_submission, assert_trap_present, assert_trap_ranks_last,
                          blur_entry, compute_spread, load, new_leaderboard, save,
                          sort_entries)
from .heldout import (HeldOutSet, OWN_PRINCIPAL, SubmissionEnvelope,
                      assert_no_write_path, authorize_write, make_heldout_set,
                      referee_append)
from .observer_sensitivity import (OBSERVER_A, OBSERVER_B, publish_observer_channels,
                                   rank_shift_report, report_observer_sensitivity)
from .rung_registry import load_registry, render_markdown, update_status, validate_registry

__all__ = [
    "BLUR_ENTRY_ID", "REFERENCE_ENTRY_ID", "TRAP_MIN_SEPARATION", "TASK_SPEC", "BLUR_SPEC",
    "check_paired_submission", "check_submission_result", "extract_paired_methods",
    "add_submission", "assert_trap_present", "assert_trap_ranks_last", "blur_entry",
    "compute_spread", "load", "new_leaderboard", "save", "sort_entries",
    "HeldOutSet", "OWN_PRINCIPAL", "SubmissionEnvelope", "assert_no_write_path",
    "authorize_write", "make_heldout_set", "referee_append",
    "OBSERVER_A", "OBSERVER_B", "publish_observer_channels", "rank_shift_report",
    "report_observer_sensitivity",
    "load_registry", "render_markdown", "update_status", "validate_registry",
]
