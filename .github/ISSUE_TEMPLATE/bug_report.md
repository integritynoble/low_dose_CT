---
name: Bug report
about: Report a defect in code, data, or documentation
title: "[bug] "
labels: ["bug"]
assignees: []
---

## Workstream

<!-- Which subproject does this bug affect? Tick all that apply. -->

- [ ] WS-1 — PWM-LDCT dataset / pipeline
- [ ] WS-2 — Signal-equivalence framework (`pwm_dose_equivalence` library, manuscript, proofs)
- [ ] WS-3 — Reference reconstruction method
- [ ] WS-4 — Leaderboard / community submissions
- [ ] Other (please describe)

## Summary

<!-- A one-sentence statement of what is broken. -->

## Environment

<!-- Fill in whichever fields are relevant. -->

* OS:
* Python version:
* `pwm_dose_equivalence` version: `python -c "import pwm_dose_equivalence; print(pwm_dose_equivalence.__version__)"`
* NumPy version:
* SciPy version:
* Git commit (if installed from source): `git rev-parse HEAD`

## Minimal reproducer

<!-- Smallest piece of code, data, or command that exhibits the bug.
     Inline a Python snippet, a `pwm-audit` invocation, or a dataset
     command. Include any input files as attachments. -->

```python
# Replace with the smallest reproducer you can construct.
```

## Expected behaviour

<!-- What you expected to happen. Cite the relevant section of the
     manuscript, the reading guide, or the library README if applicable. -->

## Actual behaviour

<!-- What actually happened. Paste full tracebacks; do not truncate. -->

```
Paste output / traceback here.
```

## Additional context

<!-- Anything else relevant. For credential-audit issues, please use the
     "Credential audit issue" template instead so we ask the right
     follow-up questions. -->
