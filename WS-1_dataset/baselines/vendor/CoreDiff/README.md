# CoreDiff — fetched, not vendored

CoreDiff (Gao et al., *IEEE TMI* 2023; arXiv:2304.01814) is **not** redistributed here.

Its upstream repository carries **no licence and no copyright notice**, which under
default copyright means all rights reserved. A copy was vendored into this tree until
2026-09-13 and was removed before this repository was made public: redistributing a
third party's source without a licence grant is not ours to do, and the right affected
belongs to the CoreDiff authors rather than to this project.

Nothing reproducible is lost. Fetch it yourself:

    ./fetch.sh                       # clones upstream into this directory
    ./fetch.sh <commit-sha>          # pin a specific revision

Upstream: https://github.com/qgao21/CoreDiff

## Which revision?

The vendored copy did not record the upstream commit it was taken from, so this
project cannot pin one honestly. If you are reproducing the v0.5 CoreDiff numbers,
record the SHA you fetched alongside your results — and if you are the author of those
numbers, add the SHA here so the next person does not have the same gap.

## What depends on this

`baselines/src/pwm_ldct_baselines/models/corediff_wrapper.py` adds this directory to
`sys.path` and imports `models.corediff.*` from it. Without the fetch, constructing the
CoreDiff baseline raises a `ModuleNotFoundError` naming this file. Every other baseline
— RED-CNN, LEARN, CTformer, and the Gaussian-blur trap — is unaffected.
