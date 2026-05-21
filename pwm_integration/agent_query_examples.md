# Agent Query Examples — Track 7 Integration

**Status:** ⏳ Examples to validate once L2/L3/L4 specs are registered on mainnet.
**Workstream:** Cross-cutting — connects WS-1 / WS-2 / WS-3 / WS-4 to Track 7 agent infrastructure.

---

## Why this file exists

PWM's flagship sentence — *"if your low-dose CT method is not on the PWM Low-Dose CT Challenge leaderboard, it is not state-of-the-art"* — becomes literally true the first time an AI agent (Track 7) successfully queries the protocol and receives a verifiable, non-empty answer pointing to this challenge.

These query examples are the **acceptance test** for that capability. Target: D9 + 540.

---

## Example 1 — Find the current SOTA

**Agent intent:** "What is the state-of-the-art reconstruction method for 25% dose chest CT?"

**Query (sketch):**

```python
from pwm_client import PWMClient

pwm = PWMClient(network="mainnet")

# Find all L4 certs against the low-dose CT benchmark
certs = pwm.find_l4_certs(
    l3_spec_name="pwm_low_dose_ct_benchmark",
    l3_spec_version=">=1.0.0"
)

# Filter to chest anatomy at 25% dose with passing 5-tuple credential
chest_certs = [
    c for c in certs
    if c.has_credential(
        task="lung_nodule_5mm_detection",
        dose_ratio=0.25,
        verdict="PASS"
    )
]

# Rank by leaderboard score
top = max(chest_certs, key=lambda c: c.score(metric="task_AUC", dose=0.25))

print(top.method_name, top.paper, top.runbundle_cid)
```

**Expected response (D9 + 540):**

```
pwm_reference_reconstruction_method v1.0
arxiv:TBD (MICCAI 2028)
ipfs://TBD
```

This is the **first non-empty answer** — the moment the killer-app sentence is provable.

---

## Example 2 — Verify a vendor claim

**Agent intent:** "Vendor X claims 50% dose reduction. Is that claim certified under the PWM framework?"

```python
# Pull the L2 dose-equivalence framework spec
l2 = pwm.get_l2_spec("dose_equivalence_v1")

# Find any L4 cert for vendor X's method
vendor_cert = pwm.find_l4_certs(method_name=f"{vendor}_reconstruction_v*")

if not vendor_cert:
    return "Vendor X has no PWM-certified method. Claim is unverifiable under the framework."

# Check the credential matches the claim
for cert in vendor_cert:
    for cred in cert.dose_equivalence_credentials:
        if cred.dose_ratio == 0.50 and cred.verdict == "PASS":
            return (
                f"Vendor X's method {cert.method_name} is dose-equivalent at 50% dose "
                f"for task {cred.task} with margin ε={cred.epsilon} at α={cred.alpha} "
                f"over subpopulation {cred.subpopulation}. "
                f"Cert: {cert.runbundle_cid}"
            )

return "Vendor X has PWM-certified methods, but none for 50% dose. Claim is unverified."
```

This is the **value proposition** of L2 + L4 together — vendor marketing claims become *testable* against the protocol.

---

## Example 3 — Find a method that fits compute budget

**Agent intent:** "What's the best low-dose CT method I can run on an L4 GPU with 24 GB?"

```python
certs = pwm.find_l4_certs(
    l3_spec_name="pwm_low_dose_ct_benchmark"
)

feasible = [c for c in certs if c.gpu_memory_gb <= 24]
top_feasible = max(feasible, key=lambda c: c.score("PSNR", dose=0.25))

print(top_feasible.method_name, top_feasible.runbundle_cid)
```

This is **why the L4 cert records `gpu_memory_gb` and `inference_seconds_per_slice`** — agents can route requests to feasible methods.

---

## Example 4 — Reproduce a result

**Agent intent:** "Reproduce the published 25% dose PSNR of the PWM reference method."

```python
cert = pwm.get_l4_cert("pwm_reference_reconstruction_method", "1.0.0")
runbundle = cert.pull_runbundle()  # IPFS fetch

# Locally:
# docker run --gpus all \
#     -v /data/pwm_l3_test:/data \
#     -v $(pwd)/output:/output \
#     {runbundle.docker_image} \
#     eval --dataset /data --dose 0.25 --out /output/results.json

# Compare /output/results.json to cert.published_results
assert verify_results_match(local_results, cert.published_results, tolerance="fp")
```

This is **what makes PWM a reproducibility protocol** — every cert is independently re-runnable.

---

## Acceptance criteria for "Track 7 hook works"

D9 + 540 demo: a live Track 7 agent runs Example 1 against PWM mainnet, receives the PWM reference method as the answer, and produces a human-readable summary citing the method, the paper, and the leaderboard score.

This demo is the **operational definition** of Track 9's flagship status.

---

## Cross-references

- L2 spec: [`l2_spec.md`](l2_spec.md)
- L3 spec: [`l3_spec.md`](l3_spec.md)
- L4 cert: [`l4_cert.md`](l4_cert.md)
