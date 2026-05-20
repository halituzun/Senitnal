"""V9 — Human approval tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.governance.approval import (
    HumanApprovalRecord,
    HumanApprovalStatus,
    is_human_approval_valid,
)

from tests.governance._fixtures import make_approval


class TestApprovalSchema:
    def test_valid_approved_accepted(self) -> None:
        a = make_approval()
        assert a.status is HumanApprovalStatus.APPROVED

    def test_approved_without_reason_rejected(self) -> None:
        with pytest.raises(ValidationError):
            HumanApprovalRecord(
                approval_id="a",
                request_id="r",
                approver_ref="op",
                status=HumanApprovalStatus.APPROVED,
                created_at_ms=900_000,
                decided_at_ms=950_000,
                expires_at_ms=2_000_000,
                approval_reason_hash=None,
                signed_by="op",
                signature="sig",
                provenance_hash="sha256:p",
            )

    def test_expires_before_created_rejected(self) -> None:
        with pytest.raises(ValidationError):
            HumanApprovalRecord(
                approval_id="a",
                request_id="r",
                approver_ref="op",
                status=HumanApprovalStatus.APPROVED,
                created_at_ms=2_000_000,
                decided_at_ms=2_000_000,
                expires_at_ms=1_000_000,
                approval_reason_hash="sha256:reason",
                signed_by="op",
                signature="sig",
                provenance_hash="sha256:p",
            )

    def test_decided_at_required_for_approved(self) -> None:
        with pytest.raises(ValidationError):
            HumanApprovalRecord(
                approval_id="a",
                request_id="r",
                approver_ref="op",
                status=HumanApprovalStatus.APPROVED,
                created_at_ms=900_000,
                decided_at_ms=None,
                expires_at_ms=2_000_000,
                approval_reason_hash="sha256:reason",
                signed_by="op",
                signature="sig",
                provenance_hash="sha256:p",
            )


class TestApprovalValidity:
    def test_valid_approval(self) -> None:
        a = make_approval()
        assert is_human_approval_valid(approval=a, request_id="gov-req-1", now_ms=1_000_000) is True

    def test_wrong_request_invalid(self) -> None:
        a = make_approval()
        assert is_human_approval_valid(approval=a, request_id="wrong", now_ms=1_000_000) is False

    def test_pending_invalid(self) -> None:
        a = HumanApprovalRecord(
            approval_id="a",
            request_id="gov-req-1",
            approver_ref="op",
            status=HumanApprovalStatus.PENDING,
            created_at_ms=900_000,
            expires_at_ms=2_000_000,
            signed_by="op",
            signature="sig",
            provenance_hash="sha256:p",
        )
        assert (
            is_human_approval_valid(approval=a, request_id="gov-req-1", now_ms=1_000_000) is False
        )

    def test_revoked_invalid(self) -> None:
        a = HumanApprovalRecord(
            approval_id="a",
            request_id="gov-req-1",
            approver_ref="op",
            status=HumanApprovalStatus.REVOKED,
            created_at_ms=900_000,
            decided_at_ms=950_000,
            expires_at_ms=2_000_000,
            signed_by="op",
            signature="sig",
            provenance_hash="sha256:p",
        )
        assert (
            is_human_approval_valid(approval=a, request_id="gov-req-1", now_ms=1_000_000) is False
        )

    def test_expired_invalid(self) -> None:
        a = make_approval(expires_at_ms=1_000_000)
        assert (
            is_human_approval_valid(approval=a, request_id="gov-req-1", now_ms=2_000_000) is False
        )

    def test_rejected_invalid(self) -> None:
        a = HumanApprovalRecord(
            approval_id="a",
            request_id="gov-req-1",
            approver_ref="op",
            status=HumanApprovalStatus.REJECTED,
            created_at_ms=900_000,
            decided_at_ms=950_000,
            expires_at_ms=2_000_000,
            signed_by="op",
            signature="sig",
            provenance_hash="sha256:p",
        )
        assert (
            is_human_approval_valid(approval=a, request_id="gov-req-1", now_ms=1_000_000) is False
        )
