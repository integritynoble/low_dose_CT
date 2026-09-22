"""scoring package for the WS-4 leaderboard."""
from .task_spec import BLUR_SPEC, TASK_SPEC
from .binding import (BIND_FAIL, BIND_PASS, BIND_UNVERIFIED, BindingResult,
                      check_input_binding, check_model_bytes, sha256_file)
from .verify import (check_claim_bound_provenance, check_input_bound_provenance,
                     check_paired_submission, check_submission_result,
                     extract_paired_methods)
from .leaderboard import (BLUR_ENTRY_ID, REFERENCE_ENTRY_ID, TRAP_RANK_FAIL,
                          TRAP_RANK_INDETERMINATE, TRAP_RANK_MISSING_STRATUM,
                          TRAP_RANK_NO_CLAIM, TRAP_RANK_PASS, add_submission,
                          assert_trap_present, assert_trap_ranks_last, blur_entry,
                          assert_trap_separates_in_every_group, check_trap_rank, compute_spread,
                          discriminating_value, load, new_leaderboard, save,
                          seed_vendor_trap_entries, sort_entries, trap_rank_by_group,
                          trap_rank_report, vendor_trap_entry_id)
from .heldout import (HeldOutSet, OWN_PRINCIPAL, SubmissionEnvelope,
                      assert_no_write_path, authorize_write, make_heldout_set,
                      referee_append)
from .verifier import (Verdict, check_claim_and_provenance,
                       check_publish_eligibility, check_runbundle_structure,
                       verify_published_vs_live, verify_runbundle)
from .observer_sensitivity import (OBSERVER_A, OBSERVER_B, publish_observer_channels,
                                   rank_shift_report, report_observer_sensitivity)
from .rung_registry import load_registry, render_markdown, update_status, validate_registry
from .gates import (PROBES, check_dose_curve, check_pairing_validation, check_roi_protocol,
                    exercise)

__all__ = [
    "BLUR_ENTRY_ID", "REFERENCE_ENTRY_ID", "TASK_SPEC", "BLUR_SPEC",
    "check_paired_submission", "check_submission_result", "extract_paired_methods",
    "add_submission", "blur_entry", "compute_spread", "load", "new_leaderboard", "save",
    "sort_entries", "assert_trap_present", "assert_trap_ranks_last", "check_trap_rank",
    "discriminating_value", "trap_rank_report", "trap_rank_by_group",
    "assert_trap_separates_in_every_group", "seed_vendor_trap_entries",
    "vendor_trap_entry_id",
    "TRAP_RANK_PASS", "TRAP_RANK_FAIL", "TRAP_RANK_INDETERMINATE",
    "TRAP_RANK_NO_CLAIM", "TRAP_RANK_MISSING_STRATUM",
    "HeldOutSet", "OWN_PRINCIPAL", "SubmissionEnvelope", "assert_no_write_path",
    "authorize_write", "make_heldout_set", "referee_append",
    "Verdict", "check_claim_and_provenance", "check_publish_eligibility",
    "check_runbundle_structure", "verify_published_vs_live", "verify_runbundle",
    "OBSERVER_A", "OBSERVER_B", "publish_observer_channels", "rank_shift_report",
    "report_observer_sensitivity",
    "load_registry", "render_markdown", "update_status", "validate_registry",
    "PROBES", "check_dose_curve", "check_pairing_validation", "check_roi_protocol", "exercise",
]
