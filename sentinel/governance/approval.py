"""V9 — Human approval record schema."""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class HumanApprovalStatus(StrEnum):
    """Closed human approval status enum."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REVOKED = "revoked"


class HumanApprovalRecord(BaseModel):
    """Signed human approval record.

    Contains no trade-command fields — approval is **not** execution
    permission.  Cryptographic signature verification is out of V9
    scope; the schema validates presence (non-empty) only.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    approval_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    approver_ref: str = Field(min_length=1)
    status: HumanApprovalStatus
    created_at_ms: int = Field(ge=0)
    decided_at_ms: int | None = None
    expires_at_ms: int = Field(ge=0)
    approval_reason_hash: str | None = None
    signed_by: str = Field(min_length=1)
    signature: str = Field(min_length=1)
    provenance_hash: str = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_approval(self) -> Self:
        if self.expires_at_ms <= self.created_at_ms:
            raise ValueError(
                f"expires_at_ms ({self.expires_at_ms}) must be > created_at_ms "
                f"({self.created_at_ms})"
            )
        if self.decided_at_ms is not None and self.decided_at_ms < self.created_at_ms:
            raise ValueError(
                f"decided_at_ms ({self.decided_at_ms}) cannot precede created_at_ms "
                f"({self.created_at_ms})"
            )
        if (
            self.status
            in (
                HumanApprovalStatus.APPROVED,
                HumanApprovalStatus.REJECTED,
                HumanApprovalStatus.REVOKED,
            )
            and self.decided_at_ms is None
        ):
            raise ValueError(f"status={self.status.value} requires decided_at_ms to be populated")
        if self.status is HumanApprovalStatus.APPROVED and not self.approval_reason_hash:
            raise ValueError("approved approvals require approval_reason_hash to be non-empty")
        return self


def is_human_approval_valid(
    *,
    approval: HumanApprovalRecord,
    request_id: str,
    now_ms: int,
) -> bool:
    """Return True iff ``approval`` validly authorizes ``request_id``.

    Approval is **not** trade execution permission; it is a procedural
    gate on Sentinel's live-impacting governance path.
    """
    if approval.request_id != request_id:
        return False
    if approval.status is not HumanApprovalStatus.APPROVED:
        return False
    if now_ms > approval.expires_at_ms:
        return False
    return bool(approval.signature)


__all__ = [
    "HumanApprovalRecord",
    "HumanApprovalStatus",
    "is_human_approval_valid",
]
