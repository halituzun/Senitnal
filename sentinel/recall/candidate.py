"""Candidate-recall subject-class whitelist + intensity cap (T §14).

Per RECALL_PROTOCOL.md §14 and the Phase 8 build plan: a candidate
recall (one whose underlying memory record is at status CANDIDATE)
may only be emitted to the core for a narrow whitelist of subject
classes. Other classes are REJECTED at the protocol boundary.

Constitutional discipline:
    - Whitelist closed: {source_trust, procedural}
    - Candidate recall intensity capped by
      `candidate_recall_intensity_multiplier_max` (loader supplies)
"""

from __future__ import annotations

from sentinel.constitution.violations import InvariantViolation, ViolationContext
from sentinel.types.memory import SubjectClass

ALLOWED_CANDIDATE_RECALL_SUBJECT_CLASSES: frozenset[SubjectClass] = frozenset(
    {
        SubjectClass.SOURCE_TRUST,
        SubjectClass.PROCEDURAL,
    }
)


def validate_candidate_recall_subject(subject_class: SubjectClass) -> None:
    """Raise InvariantViolation if `subject_class` is not in the whitelist."""
    if subject_class not in ALLOWED_CANDIDATE_RECALL_SUBJECT_CLASSES:
        raise InvariantViolation(
            (
                f"candidate recall forbidden for subject_class "
                f"{subject_class.value!r}; whitelist = "
                f"{sorted(c.value for c in ALLOWED_CANDIDATE_RECALL_SUBJECT_CLASSES)!r}"
            ),
            ViolationContext(
                violation_code="RECALL_CANDIDATE_SUBJECT_CLASS_FORBIDDEN",
                source_ref="RECALL_PROTOCOL.md §14",
                evidence={
                    "subject_class": subject_class.value,
                    "allowed": sorted(c.value for c in ALLOWED_CANDIDATE_RECALL_SUBJECT_CLASSES),
                },
            ),
        )


def apply_candidate_recall_intensity_cap(
    intensity: float,
    *,
    multiplier_max: float,
) -> float:
    """Clamp `intensity` by `multiplier_max` (T §14). Inputs must be in [0,1]."""
    if not (0.0 <= intensity <= 1.0):
        raise ValueError(f"intensity {intensity!r} outside [0.0, 1.0]")
    if not (0.0 < multiplier_max <= 1.0):
        raise ValueError(f"multiplier_max {multiplier_max!r} outside (0.0, 1.0]")
    return min(intensity, multiplier_max)
