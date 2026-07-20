"""Credential dataclasses and JSON schema.

A signal-equivalence credential is a 5-tuple ``(r, T, ε, α, Π)`` plus the
verdict and the bootstrap CI, packaged with the framework-version hash so
a third party can verify the credential by recomputing the bootstrap.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Literal


class Verdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INDETERMINATE = "INDETERMINATE"


Modality = Literal["CT", "MRI", "PET"]
Estimator = Literal["percentile", "delong", "bca"]


@dataclass
class Task:
    """A clinical task with its performance metric and optional target.

    ``name`` is a stable slug (e.g. ``"lung_nodule_5mm"``). ``metric`` is one of
    ``"auc"``, ``"dice"``, ``"mae"``, ``"contrast_recovery"`` — used by the
    estimator to choose the right default CI variant. ``ground_truth_protocol``
    is a slug that should resolve to a normative protocol document by SHA-256
    hash (see ``framework_hash`` module).
    """

    name: str
    metric: Literal["auc", "dice", "mae", "contrast_recovery"] = "auc"
    target: float | None = None
    ground_truth_protocol: str | None = None


@dataclass
class Credential:
    """The inner credential — the methodologically load-bearing payload."""

    method: str
    reference_method: str
    signal_ratio: float
    modality: Modality
    task: Task
    subpopulation: str
    epsilon: float
    alpha: float
    estimator: Estimator
    n_test: int
    n_bootstrap: int
    seed: int
    delta_mean: float
    delta_ci_low: float
    delta_ci_high: float
    verdict: Verdict
    sample_size_check: dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalEquivalenceCredential:
    """A complete published credential, including the framework-version hash.

    Serialise via ``to_json()`` (string) or ``to_dict()`` (dict). The
    ``framework_hash`` field is the SHA-256 hash of the framework definition
    the credential was issued under; a verifier resolves it to retrieve the
    exact framework version and re-run the bootstrap.
    """

    schema_version: str
    framework_hash: str
    credential: Credential

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # Coerce nested enum
        d["credential"]["verdict"] = (
            self.credential.verdict.value
            if isinstance(self.credential.verdict, Verdict)
            else self.credential.verdict
        )
        return d

    def to_json(self, indent: int | None = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=False)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> SignalEquivalenceCredential:
        c = d["credential"]
        task_d = c["task"]
        task = Task(
            name=task_d["name"],
            metric=task_d.get("metric", "auc"),
            target=task_d.get("target"),
            ground_truth_protocol=task_d.get("ground_truth_protocol"),
        )
        cred = Credential(
            method=c["method"],
            reference_method=c["reference_method"],
            signal_ratio=c["signal_ratio"],
            modality=c["modality"],
            task=task,
            subpopulation=c["subpopulation"],
            epsilon=c["epsilon"],
            alpha=c["alpha"],
            estimator=c["estimator"],
            n_test=c["n_test"],
            n_bootstrap=c["n_bootstrap"],
            seed=c["seed"],
            delta_mean=c["delta_mean"],
            delta_ci_low=c["delta_ci_low"],
            delta_ci_high=c["delta_ci_high"],
            verdict=Verdict(c["verdict"]),
            sample_size_check=c.get("sample_size_check", {}),
        )
        return cls(
            schema_version=d["schema_version"],
            framework_hash=d["framework_hash"],
            credential=cred,
        )

    @classmethod
    def from_json(cls, s: str) -> SignalEquivalenceCredential:
        return cls.from_dict(json.loads(s))
