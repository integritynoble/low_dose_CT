"""pwm_dose_equivalence — reference implementation of the signal-equivalence framework.

A reconstruction method is *signal-equivalent* to a reference method at level
:math:`(r, T, \\varepsilon, \\alpha)` over subpopulation :math:`\\Pi` iff its
expected task performance on reduced-signal scans is within :math:`\\varepsilon`
of the reference method's performance on full-signal scans, with confidence
:math:`\\geq 1 - \\alpha`.

This package implements that test for CT, MRI, and PET through a single
modality-agnostic API call::

    from pwm_dose_equivalence import signal_equivalence_credential, Task

    cred = signal_equivalence_credential(
        paired_a=method_scores_on_reduced,
        paired_b=reference_scores_on_full,
        signal_ratio=0.25,
        modality="CT",
        task=Task("lung_nodule_5mm", metric="auc"),
        subpopulation="adult_chest_pwm_l3_test_v1",
        epsilon=0.05,
        alpha=0.05,
    )
    print(cred.verdict)   # PASS / FAIL / INDETERMINATE
    print(cred.to_json())

See ``theory/proofs/`` in the project tree for the estimator-default and
sample-size-formula derivations the API defaults reflect.
"""

from pwm_dose_equivalence.api import signal_equivalence_credential
from pwm_dose_equivalence.credential import (
    Credential,
    SignalEquivalenceCredential,
    Task,
    Verdict,
)
from pwm_dose_equivalence.estimator import (
    delong_ci,
    percentile_ci,
)
from pwm_dose_equivalence.framework_hash import (
    FRAMEWORK_SPEC,
    framework_hash,
)
from pwm_dose_equivalence.operators import (
    Tr_ct,
    Tr_mri,
    Tr_pet,
)
from pwm_dose_equivalence.sample_size import (
    required_n_auc,
    required_n_general,
    required_n_bernstein,
)

__version__ = "0.1.0"

__all__ = [
    "Credential",
    "FRAMEWORK_SPEC",
    "SignalEquivalenceCredential",
    "Task",
    "Tr_ct",
    "Tr_mri",
    "Tr_pet",
    "Verdict",
    "__version__",
    "delong_ci",
    "framework_hash",
    "percentile_ci",
    "required_n_auc",
    "required_n_bernstein",
    "required_n_general",
    "signal_equivalence_credential",
]
