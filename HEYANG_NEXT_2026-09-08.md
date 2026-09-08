# Review and next steps — heyang, 8 September 2026

Supersedes the ordered list in [`HEYANG_NEXT_STEPS.md`](HEYANG_NEXT_STEPS.md), which was written against
`86cce03`. **Main is now `ee0c6a6`, thirty-four commits and about 3,700 lines later**, so several items on that
page are done and one of its assumptions has changed. Read this first and that page second.

---

## What you finished, and what it was worth

**The trap-rank gate exists now** (item C). It was the sharpest item on the old list, because a trap that is
reported and never enforced is decoration. `scoring/tests/test_trap_rank.py` is 344 lines and the gate is
exercised in both directions. Independent confirmation, from a machine that is not this one and did not write
it: a real entry passes at 8.92 times separation and a smoother fails at 0.232. That is the behaviour claimed,
checked by someone who had no stake in it.

**The round-4 merge held.** WS-1's manuscript went from scaffolding to a filled paper at zero outstanding
markers, and nothing in the subsequent thirty-four commits has had to undo it.

**The R6 recalculation remains the strongest integrity artifact here**: independent environment, independent
toolchain, byte-level verification. Two later findings lean on it and neither contradicted it.

## What changed underneath you since that list

Four things, and the first two affect work you were about to do.

**1. The submission gate had a bypass, and it is closed.** `assert_no_referee_paths` walked dictionary values
but never their keys, and it was never applied to `method_name` at all. A referee-owned path placed in a key,
or in the method name, passed the gate and reached the board. Found while checking an unrelated audit,
reproduced end to end through `scoring.cli submit`, and fixed in `015295d4` with a test covering each hole
separately. Nine of its twelve assertions fail on the parent commit.

**Why it matters to you:** the gate is the thing standing between a submitter and the referee's own files. If
you were treating it as sound, it was not, and the same shape may be elsewhere — see task 2.

**2. Nobody outside can run this repository.** It is private, so the five-gate demonstration cannot be obtained
by a reader. A clean machine confirmed that today. The gates work; they are simply not gettable. That is the
owner's decision to make, and it changes what any paper here can claim a reader will check.

**3. The scoring suite needs pytest, and says so nowhere.** On a clean machine with nothing installed, seven of
the scoring tests fail on `import pytest`. The claims they check are fine. A reader who clones and runs the
suite sees seven errors and concludes the package is broken.

**4. Documented test counts have drifted again** (issue #21, follow-on to #6). Three more places, two of which
disagree with each other. The substantive claims are unaffected; the numbers printed beside them are not.

---

## What to do next, in order

### 1. Issue #21 — the test-count drift
Mechanical, an hour, and it buys back trust in every other number in the documentation. Fix all three places,
and add whatever check would have caught it: a count that is asserted somewhere is a count that cannot drift
silently. **Done when** the documented figures match a fresh run and something fails if they stop matching.

### 2. The gate audit — does anything else walk values but not keys?
The bypass was one instance of a shape: a traversal that misses dictionary keys, or a submitter-controlled
field nobody checks. Go through every gate and validator in `scoring/` and ask both questions of each.
**Done when** every gate is listed with a yes or no for each question, and anything answering wrong has a test
that fails today.

### 3. Issue #4 — WS-2 prose reconciliation
Still prose only, and this is now firmer than when it was written. Independent checks established that the CT
results table **cannot** be filled: the metric exists nowhere in the repository, the majority-vote ground truth
has not been built, one of the four methods has not started, and the manuscript itself places that table in a
later phase and says so twice. So do the tense and claim reconciliation, and **do not** fill the tables.
**Done when** every past-tense claim matches something that actually ran.

### 4. Make the suite runnable, or say what it needs
Either make the seven tests degrade gracefully without pytest, or state the requirement in the instructions.
Either is acceptable; silence is not. **Done when** a reader who follows the published steps gets a passing
suite or a clear message naming what to install.

### 5. Issue #5 — the R6 re-run, and read this before starting
Route (a) was decided, and there is now a further ruling that route (a) is **original-machine-only**. If you are
not on that machine, this is not yours to start, and the honest move is to say so on the issue rather than
approximate it elsewhere.

## Not yours yet

**The detector.** Six raise sites, and everything downstream of it is a deterministic stub, which two
independent machines have now confirmed from the source. Implementing it needs the heavy dependency, pinned
weights and a data path, and the scope has not been accepted. Do not start it on your own initiative.

**Anything needing a DOI, an author list, licensing, or the phantom scan.** Unchanged: those are the Director's,
not yours.

---

*Written after an independent review of the repository at `ee0c6a6`. Every claim above is checkable: the gate
bypass is commit `015295d4`, the reproduction figures came from a machine that did not write them, and the
seven import failures are reproducible on any clean clone.*
