"""Tests for the candidate-recall subject-class whitelist + intensity cap."""

from __future__ import annotations

import pytest
from sentinel.constitution.violations import InvariantViolation
from sentinel.recall.candidate import (
    ALLOWED_CANDIDATE_RECALL_SUBJECT_CLASSES,
    apply_candidate_recall_intensity_cap,
    validate_candidate_recall_subject,
)
from sentinel.types.memory import SubjectClass


class TestWhitelistShape:
    def test_two_subject_classes(self) -> None:
        assert (
            frozenset({SubjectClass.SOURCE_TRUST, SubjectClass.PROCEDURAL})
            == ALLOWED_CANDIDATE_RECALL_SUBJECT_CLASSES
        )


class TestValidateSubject:
    @pytest.mark.parametrize(
        "subject_class",
        list(ALLOWED_CANDIDATE_RECALL_SUBJECT_CLASSES),
    )
    def test_allowed_subject_accepted(self, subject_class: SubjectClass) -> None:
        validate_candidate_recall_subject(subject_class)

    @pytest.mark.parametrize(
        "subject_class",
        [sc for sc in SubjectClass if sc not in ALLOWED_CANDIDATE_RECALL_SUBJECT_CLASSES],
    )
    def test_other_subjects_rejected(self, subject_class: SubjectClass) -> None:
        with pytest.raises(InvariantViolation) as exc_info:
            validate_candidate_recall_subject(subject_class)
        assert exc_info.value.violation_code == "RECALL_CANDIDATE_SUBJECT_CLASS_FORBIDDEN"


class TestIntensityCap:
    def test_below_cap_returns_unchanged(self) -> None:
        assert apply_candidate_recall_intensity_cap(0.3, multiplier_max=0.5) == 0.3

    def test_above_cap_clamped(self) -> None:
        assert apply_candidate_recall_intensity_cap(0.9, multiplier_max=0.5) == 0.5

    def test_intensity_out_of_range_raises(self) -> None:
        with pytest.raises(ValueError):
            apply_candidate_recall_intensity_cap(1.1, multiplier_max=0.5)
        with pytest.raises(ValueError):
            apply_candidate_recall_intensity_cap(-0.1, multiplier_max=0.5)

    def test_multiplier_out_of_range_raises(self) -> None:
        with pytest.raises(ValueError):
            apply_candidate_recall_intensity_cap(0.3, multiplier_max=0.0)
        with pytest.raises(ValueError):
            apply_candidate_recall_intensity_cap(0.3, multiplier_max=1.5)
