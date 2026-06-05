# %% [markdown]
# # Tutorial 1 — CT lung-nodule detection at 25 % dose (AUC)
#
# This tutorial walks through computing a **signal-equivalence credential**
# for a CT lung-nodule detection task at 25 % tube-current dose, against a
# full-dose reference method. We use a synthetic per-patient AUC simulation
# so you can run this end-to-end on a laptop in under a minute.
#
# The file is a `.py` script with `#%%` cell markers — it runs as a normal
# Python script (`python 01_ct_lung_nodule_auc.py`) **and** as a Jupyter
# notebook (open in JupyterLab / VS Code / Spyder; cells render
# automatically).
#
# **What you will learn:**
# 1. How to express the candidate vs. reference method as paired per-case
#    positive-class and negative-class score arrays
# 2. How `signal_equivalence_credential(...)` auto-selects DeLong for AUC
#    tasks (per `theory/proofs/estimator.md` §4)
# 3. How to read the credential JSON (verdict, CI, framework hash)
# 4. How the v0.3 AUC default `ε = 0.05` interacts with realistic cohort
#    sizes (the §4a cohort-sizing implication)

# %% [markdown]
# ## 1. Setup

# %%
import numpy as np
from scipy import stats

from pwm_dose_equivalence import (
    Task, framework_hash, signal_equivalence_credential,
)

rng = np.random.default_rng(seed=42)

# %% [markdown]
# ## 2. Simulate paired per-case AUC scores
#
# In a real experiment, you would have:
# * `a_pos`, `a_neg`: your candidate reconstruction method's classifier
#    scores on the positive (nodule-present) and negative (nodule-absent)
#    cases of the test set.
# * `b_pos`, `b_neg`: the reference method's scores on the **same cases**
#    (paired-on-patient).
#
# Here we synthesise both using the canonical paired-binormal model with
# population AUC = 0.92 (typical lung-nodule operating point) and
# cross-method correlation $\rho = 0.5$. We make the candidate
# **truly equivalent** to the reference (same population mean for both),
# so the framework should issue `PASS`.

# %%
n_per_class = 400        # 800 patients total — well above the §4a P(PASS) ≈ 0.94 threshold
auc_target = 0.92
rho = 0.5

mu_pos = float(np.sqrt(2) * stats.norm.ppf(auc_target))
cov = np.array([[1.0, rho], [rho, 1.0]])
pos = rng.multivariate_normal([mu_pos, mu_pos], cov, size=n_per_class)
neg = rng.multivariate_normal([0.0, 0.0], cov, size=n_per_class)

a_pos, b_pos = pos[:, 0], pos[:, 1]
a_neg, b_neg = neg[:, 0], neg[:, 1]

print(f"n_pos = {n_per_class}, n_neg = {n_per_class}, n_total = {2 * n_per_class}")
print(f"target AUC for both methods ≈ {auc_target}")

# %% [markdown]
# ## 3. Issue the credential
#
# This single API call is the load-bearing operation. Three things happen:
#
# 1. The estimator auto-selects to **DeLong** because `task.metric == "auc"`.
#    Per `proofs/estimator.md` §4, DeLong is mildly conservative and
#    ~300× faster than the bootstrap variants. The library does this for
#    you; you don't have to pass `estimator="delong"` explicitly.
# 2. The credential's framework hash is the SHA-256 of the v0.2 framework
#    specification. A reader of your credential can recover the framework
#    definition by hash, independent of you.
# 3. The verdict is one of `PASS`, `FAIL`, or `INDETERMINATE`. The
#    framework refuses to force a binary verdict when the CI straddles
#    the equivalence band — that's correct conservative behaviour.

# %%
cred = signal_equivalence_credential(
    a_pos=a_pos, a_neg=a_neg, b_pos=b_pos, b_neg=b_neg,
    signal_ratio=0.25,
    modality="CT",
    task=Task(
        "lung_nodule_5mm",
        metric="auc",
        ground_truth_protocol="pwm-ldct/annotation-qa/v0.5#sha256:...",
    ),
    subpopulation="adult_chest_pwm_l3_test_v1",
    epsilon=0.05,           # v0.3 AUC default per V3-1
    alpha=0.05,
    seed=42,
)

print(f"Estimator used: {cred.credential.estimator}")
print(f"Δ̄  (observed) = {cred.credential.delta_mean:.4f}")
print(f"95 % CI       = [{cred.credential.delta_ci_low:.4f}, "
      f"{cred.credential.delta_ci_high:.4f}]")
print(f"Verdict        = {cred.credential.verdict.value}")

# %% [markdown]
# ## 4. Inspect the credential JSON
#
# This is what you would publish alongside your method. A reader can
# recompute the verdict by re-running the same library against your
# published method on the same test set under the same framework hash.

# %%
print(cred.to_json(indent=2))

# %% [markdown]
# ## 5. Verify the framework hash
#
# The hash is content-addressed — recomputing it from the canonical spec
# must produce the same digest. This is the audit-trail guarantee the
# manuscript's content-addressing argument makes.

# %%
import hashlib
from pwm_dose_equivalence import FRAMEWORK_SPEC

recomputed = "sha256:" + hashlib.sha256(
    FRAMEWORK_SPEC.encode("utf-8")
).hexdigest()
assert cred.framework_hash == recomputed == framework_hash()
print(f"framework_hash verified: {cred.framework_hash}")

# %% [markdown]
# ## 6. Cohort-sizing implication
#
# At the v0.3 AUC default `ε = 0.05` and the typical lung-nodule operating
# point AUC ≈ 0.92, the per-cell power simulation in
# `theory/proofs/estimator.md` §4a reports:
#
# | n   | P(`PASS`) under the null |
# |-----|--------------------------|
# | 100 | ≈ 0.05  (cohort too small) |
# | 200 | ≈ 0.40  (the WS-1 v0.5 cohort) |
# | 500 | ≈ 0.94  (close to nominal 1 − α) |
#
# The WS-1 v0.5 cohort of 208 unique paired patients sits in the
# INDETERMINATE-dominated regime even when methods are *truly* equivalent.
# Absence of a `PASS` verdict on the WS-1 cohort is therefore **not
# evidence of non-equivalence** — only of insufficient n.
#
# In this tutorial we used n = 800 (well above the §4a threshold), so the
# verdict above should be `PASS` in roughly 95 % of seeds. Note that at
# any specific seed it is still possible to land on INDETERMINATE if the
# bootstrap CI happens to brush against ±ε; that's the framework's
# correct conservative behaviour. Re-run with `seed = 43, 44, ...` to
# see the verdict distribution across seeds.
