# `pwm_integration/` — On-chain artifacts for PWM mainnet

The three on-chain artifacts that make the low-dose CT work **PWM-flagship** rather than generic medical-imaging research. Without these on chain, the workstreams produce publishable papers; *with* them on chain, an AI agent (Track 7) can query the protocol and receive a verifiable answer pointing to the leaderboard top entry, the framework definition, and the dataset hash.

---

## Goals

1. **Register three specs on PWMRegistry** by their target dates:
   - **L2** — Signal-equivalence framework (gates WS-2 manuscript submission)
   - **L3** — Benchmark dataset (gates WS-1 manuscript submission)
   - **L4** — Reference reconstruction method cert (gates WS-3 manuscript submission)
2. **Prove the Track 7 agent-query loop returns non-empty.** An AI agent runs the canonical query *"what is the SOTA for 25% dose chest CT?"* against PWM mainnet and receives the L4 cert + leaderboard top entry. This is the operational definition of flagship status.
3. **Establish the canonical pattern for Track 8b reference-cert grants.** The WS-1 → L3 pattern is what every future PWM grand challenge (MRI, cancer, weather, etc.) inherits. Cleanliness here scales.

---

## Three artifacts

| Layer | Spec | Source workstream | Target on-chain date |
|---|---|---|---|
| **L2** | Signal-equivalence framework formal definition | WS-2 (`framework/`) | D9 + 365 |
| **L3** | Benchmark dataset specification (schema + access + scoring rules) | WS-1 (`dataset/`) | D9 + 365 |
| **L4 v1** | Reference method cert (unrolled iterative, RunBundle hash + 5-tuple results) | WS-3 (`reference_method/`) | D9 + 540 |
| **L4 v2** | Foundation-model reference method cert | WS-6 (`foundation_model/`) | D9 + 1095 (Year 3, contingent on R21 funding) |

The L2 spec is intentionally modality-general (covers CT dose reduction, MRI accelerated reconstruction, PET low-activity) so a single framework anchor serves all future signal-reduction grand challenges.

---

## Authoring sequence

1. **L3 spec** ([`l3_spec.md`](l3_spec.md)) — **first**, because the framework depends on the dataset format. Technical content authored alongside `WS-1_dataset/schema/` in Phase 1. Final draft frozen when dataset is locked.
2. **L2 spec** ([`l2_spec.md`](l2_spec.md)) — **second**, after Phase 1 framework pilot validates the definition is implementable. Final draft frozen at WS-2 manuscript submission and hashes [`../WS-2_framework/theory/dose-equivalence-framework.md`](../WS-2_framework/theory/dose-equivalence-framework.md).
3. **L4 cert** ([`l4_cert.md`](l4_cert.md)) — **third**, after `WS-3_reference_method/v1/` is trained, evaluated, and packaged into a RunBundle. Final draft frozen when RunBundle CID is published to IPFS.

---

## Tasks

### Phase 1 — Stub maturation (D9 + 0 → D9 + 90)

| # | Task | Output |
|---|---|---|
| 1.1 | L3 stub aligned with WS-1 Phase 1 schema decisions | [`l3_spec.md`](l3_spec.md) v0.1 ✅ |
| 1.2 | L2 stub aligned with WS-2 v0.1 formal definition | [`l2_spec.md`](l2_spec.md) v0.1 ✅ |
| 1.3 | L4 stub aligned with WS-3 RunBundle format | [`l4_cert.md`](l4_cert.md) v0.1 ✅ |
| 1.4 | Agent query examples drafted (4 canonical queries) | [`agent_query_examples.md`](agent_query_examples.md) ✅ |

### Phase 2 — Registry format finalization (D9 + 90 → D9 + 180)

| # | Task | Output |
|---|---|---|
| 2.1 | PWM Registry spec stabilized post-mainnet (waits on protocol team) | Registry payload format locked |
| 2.2 | L2 / L3 / L4 payload schemas updated to final registry format | Updated spec files |
| 2.3 | Local validation tooling — given a spec markdown file, produce the exact registry payload bytes | `tools/spec_to_payload.py` |

### Phase 3 — On-chain registration (D9 + 270 → D9 + 540)

| # | Task | Output |
|---|---|---|
| 3.1 | L3 spec v1.0.0 finalized; content hash computed; registry tx submitted | L3 hash on chain @ D9 + 365 |
| 3.2 | L2 spec v1.0.0 finalized; content hash computed; registry tx submitted | L2 hash on chain @ D9 + 365 |
| 3.3 | L4 cert v1.0.0 finalized; RunBundle CID populated; registry tx submitted | L4 hash on chain @ D9 + 540 |

### Phase 4 — Agent-query proof (D9 + 540)

| # | Task | Output |
|---|---|---|
| 4.1 | Track 7 agent runs Example 1 (SOTA query) against mainnet | Live demo recorded |
| 4.2 | Agent runs Example 2 (vendor claim verification) | Live demo recorded |
| 4.3 | Agent runs Example 4 (reproduce a published result) | Live demo recorded |
| 4.4 | Document the demo as the operational definition of Track 9 flagship status | `agent_query_examples.md` updated with demo results |

---

## Timeline (D9-anchored)

| Date | Milestone | Status |
|---|---|---|
| D9 + 0 | All three stubs + agent query examples in this folder | ✅ done |
| D9 + 90 | Stubs aligned with Phase 1 workstream artifacts | pending |
| D9 + 180 | PWM Registry payload format locked; spec files updated | pending |
| D9 + 365 | **L2 + L3 specs registered on PWMRegistry** | pending |
| D9 + 540 | **L4 cert registered on PWMRegistry; agent-query loop proven** | pending |

---

## Done when

- [ ] L2 + L3 + L4 specs all registered on PWM mainnet
- [ ] First Track 7 agent query for "SOTA 25% dose chest CT" returns non-empty (D9 + 540 target)
- [ ] WS-1's L3 cert is the canonical example Track 8b reference-cert grants reproduce
- [ ] Three other future PWM grand challenges (MRI / cancer / etc.) inherit the L3 pattern cleanly

---

## Files

| File | Purpose |
|---|---|
| [`l2_spec.md`](l2_spec.md) | Signal-equivalence framework L2 spec (formal definition + registry payload) |
| [`l3_spec.md`](l3_spec.md) | Benchmark L3 spec (schema + access + scoring + content hash) |
| [`l4_cert.md`](l4_cert.md) | Reference-method L4 cert (RunBundle CID + 5-tuple results + verification) |
| [`agent_query_examples.md`](agent_query_examples.md) | Four canonical Track 7 agent queries against this challenge |

---

## Why these three artifacts matter

Without L2 / L3 / L4 on chain, the work is publishable medical-imaging research — useful but not flagship. With them on chain, an AI agent (Track 7) can ask:

> *"What is the current state-of-the-art reconstruction method for 25% dose chest CT?"*

…and receive a verifiable, cryptographically authenticated answer pointing to the leaderboard top entry, the framework definition, and the dataset hash. **The first time this query returns a non-empty answer (target D9 + 540) is the moment PWM's killer-app sentence becomes literally true.**

---

## Registry payload contract

Each `.md` file in this folder must include a clearly delimited "Registry payload" section at the bottom — the exact bytes that get hashed and registered on chain. The format follows the PWM Registry spec (`pwm-team/registry/` in the parent PWM repo; format will stabilize post-mainnet).

---

## Cross-references

- [`../WS-1_dataset/`](../WS-1_dataset/) — produces the L3 spec content
- [`../WS-2_framework/theory/dose-equivalence-framework.md`](../WS-2_framework/theory/dose-equivalence-framework.md) — what L2 spec hashes
- [`../WS-3_reference_method/`](../WS-3_reference_method/) — produces the L4 cert content
- [`../WS-4_leaderboard/`](../WS-4_leaderboard/) — submission contract anchors on L3 + L2 specs
