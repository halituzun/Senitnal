"""V14 — Credential Vault reference schemas.

Stores references to credentials only.  No actual secret values are
ever held in these models; validators reject any attempt to pass raw
secret material.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

_SECRET_PATTERNS = frozenset(
    {
        "api_key",
        "api_secret",
        "secret",
        "password",
        "token",
        "private_key",
        "bearer",
        "hmac",
        "passphrase",
        "credentials",
    }
)

_MS_PER_DAY = 86_400_000


class CredentialKind(StrEnum):
    """Closed set of supported credential kinds."""

    API_KEY = "api_key"
    HMAC_SECRET = "hmac_secret"
    BEARER_TOKEN = "bearer_token"
    OAUTH2_CLIENT = "oauth2_client"


class CredentialReference(BaseModel, frozen=True, extra="forbid"):
    """Reference to a credential stored in an external vault.

    No actual secret is held here.  The label field must not contain
    raw secret material.
    """

    ref_id: str = Field(min_length=1)
    kind: CredentialKind
    adapter_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    created_at_ms: int = Field(ge=0)
    expires_at_ms: int | None = None
    is_active: bool = True

    @field_validator("label", mode="before")
    @classmethod
    def _label_has_no_secret_material(cls, v: object) -> object:
        if isinstance(v, str):
            lower = v.lower()
            for pat in _SECRET_PATTERNS:
                if pat in lower and len(v) > 32:
                    raise ValueError(
                        "label must not contain raw secret material"
                    )
        return v

    @model_validator(mode="after")
    def _expiry_after_creation(self) -> CredentialReference:
        if self.expires_at_ms is not None and self.expires_at_ms <= self.created_at_ms:
            raise ValueError("expires_at_ms must be after created_at_ms")
        return self


class CredentialVaultConfig(BaseModel, frozen=True, extra="forbid"):
    """Configuration for the credential reference vault."""

    vault_id: str = Field(min_length=1)
    rotation_reminder_days: int = Field(ge=1, default=90)
    allow_expired: Literal[False] = False
    credentials: tuple[CredentialReference, ...]

    @model_validator(mode="after")
    def _no_duplicate_refs(self) -> CredentialVaultConfig:
        ids = [c.ref_id for c in self.credentials]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate ref_id in credentials")
        return self


def is_credential_valid(ref: CredentialReference, now_ms: int) -> bool:
    """Return True if the credential is active and not expired."""
    return ref.is_active and not (
        ref.expires_at_ms is not None and now_ms >= ref.expires_at_ms
    )


def list_expiring_soon(
    config: CredentialVaultConfig,
    now_ms: int,
    horizon_days: int = 30,
) -> tuple[CredentialReference, ...]:
    """Return credentials expiring within horizon_days from now_ms."""
    horizon_ms = now_ms + horizon_days * _MS_PER_DAY
    return tuple(
        c
        for c in config.credentials
        if c.expires_at_ms is not None
        and now_ms < c.expires_at_ms <= horizon_ms
        and c.is_active
    )
