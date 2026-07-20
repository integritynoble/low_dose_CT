---
name: Credential audit issue
about: "`audit_credential` / `pwm-audit` returned a verdict you disagree with"
title: "[audit] "
labels: ["audit", "WS-2"]
assignees: []
---

<!-- Use this template when you believe `audit_credential` or the
     `pwm-audit` CLI returned the wrong verdict on a credential.
     For general bugs, use the "Bug report" template instead. -->

## Summary

<!-- One sentence: what did the audit say, and what did you expect? -->

## Library version

```
python -c "import pwm_dose_equivalence; print(pwm_dose_equivalence.__version__)"
```

Also include: NumPy version, SciPy version, Python version, OS.

## The credential JSON

<!-- Attach the credential JSON file. If it contains anything
     sensitive (patient data references, internal subpopulation
     slugs), redact those fields but keep the audit-relevant fields
     (delta_*, verdict, framework_hash, epsilon, alpha, estimator,
     n_test, sample_size_check) intact and DO NOT change their
     numeric values. -->

## Audit output

<!-- Paste the full output of:

       pwm-audit <your_credential.json> --json

     and:

       pwm-audit <your_credential.json>

     Do not truncate. -->

```json
{ paste --json output here }
```

```
paste human-readable output here
```

## Why you think the audit is wrong

<!-- Concretely: which check do you think misfired? Cite the section
     of credential_reading_guide.md or estimator.md that supports
     your expectation. Two examples:

     * "Section 3 of the reading guide says PASS requires the CI
       fully inside (-epsilon, epsilon), and my CI is [-0.04,
       0.04] with epsilon=0.05, so I expected PASS, but the audit
       returned INDETERMINATE."

     * "The audit warned that BCa is opt-in only, but my
       credential reports both a percentile companion and a BCa
       headline, so the warning seems spurious." -->

## Suspected severity

- [ ] **Critical** — credential audits as `ok=True` but does not match its CI (potential credential-forgery surface). **Please use SECURITY.md private channel instead.**
- [ ] **High** — audit produces the wrong verdict deterministically on a credential issued by the library itself.
- [ ] **Medium** — audit produces the wrong verdict on a credential issued by another tool.
- [ ] **Low** — audit produces a confusing warning or error message but the verdict is correct.

## Additional context

<!-- Links to the issuing method's code; relevant manuscript or
     proofs sections; prior issues / discussions on the same
     credential class. -->
