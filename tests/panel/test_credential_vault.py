"""V14 — Credential Vault tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sentinel.panel.credential_vault import (
    CredentialKind,
    CredentialReference,
    CredentialVaultConfig,
    is_credential_valid,
    list_expiring_soon,
)

NOW_MS = 1_000_000_000  # ~11.5 days in ms — large enough for past/future offsets
DAY_MS = 86_400_000


def _ref(
    ref_id: str = "ref-1",
    kind: CredentialKind = CredentialKind.API_KEY,
    adapter_id: str = "taapi",
    label: str = "TAAPI production key ref",
    created_at_ms: int = NOW_MS,
    expires_at_ms: int | None = NOW_MS + 90 * DAY_MS,
    is_active: bool = True,
) -> CredentialReference:
    return CredentialReference(
        ref_id=ref_id,
        kind=kind,
        adapter_id=adapter_id,
        label=label,
        created_at_ms=created_at_ms,
        expires_at_ms=expires_at_ms,
        is_active=is_active,
    )


class TestCredentialReference:
    def test_basic_valid(self) -> None:
        r = _ref()
        assert r.ref_id == "ref-1"
        assert r.kind is CredentialKind.API_KEY

    def test_expiry_must_be_after_creation(self) -> None:
        with pytest.raises(ValidationError):
            _ref(expires_at_ms=NOW_MS - 1)

    def test_no_expiry_allowed(self) -> None:
        r = _ref(expires_at_ms=None)
        assert r.expires_at_ms is None

    def test_all_kinds(self) -> None:
        for kind in CredentialKind:
            r = _ref(kind=kind)
            assert r.kind is kind

    def test_frozen(self) -> None:
        r = _ref()
        with pytest.raises((TypeError, ValidationError)):
            r.is_active = False  # type: ignore[misc]


class TestIsCredentialValid:
    def test_active_not_expired(self) -> None:
        r = _ref(expires_at_ms=NOW_MS + DAY_MS)
        assert is_credential_valid(r, NOW_MS) is True

    def test_inactive(self) -> None:
        r = _ref(is_active=False)
        assert is_credential_valid(r, NOW_MS) is False

    def test_expired(self) -> None:
        r = _ref(created_at_ms=NOW_MS - 2 * DAY_MS, expires_at_ms=NOW_MS - 1)
        assert is_credential_valid(r, NOW_MS) is False

    def test_no_expiry_is_valid(self) -> None:
        r = _ref(expires_at_ms=None)
        assert is_credential_valid(r, NOW_MS) is True


class TestCredentialVaultConfig:
    def test_basic_vault(self) -> None:
        cfg = CredentialVaultConfig(
            vault_id="vault-1",
            credentials=(_ref("r1"), _ref("r2", adapter_id="gelal")),
        )
        assert len(cfg.credentials) == 2
        assert cfg.allow_expired is False

    def test_duplicate_ref_id_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CredentialVaultConfig(
                vault_id="vault-dup",
                credentials=(_ref("same"), _ref("same")),
            )

    def test_allow_expired_always_false(self) -> None:
        cfg = CredentialVaultConfig(vault_id="v", credentials=())
        assert cfg.allow_expired is False


class TestListExpiringSoon:
    def test_finds_expiring_within_horizon(self) -> None:
        soon = _ref("soon", expires_at_ms=NOW_MS + 10 * DAY_MS)
        later = _ref("later", adapter_id="gelal", expires_at_ms=NOW_MS + 60 * DAY_MS)
        cfg = CredentialVaultConfig(vault_id="v", credentials=(soon, later))
        result = list_expiring_soon(cfg, NOW_MS, horizon_days=30)
        ids = [r.ref_id for r in result]
        assert "soon" in ids
        assert "later" not in ids

    def test_inactive_excluded(self) -> None:
        inactive = _ref("inactive", expires_at_ms=NOW_MS + 5 * DAY_MS, is_active=False)
        cfg = CredentialVaultConfig(vault_id="v", credentials=(inactive,))
        result = list_expiring_soon(cfg, NOW_MS, horizon_days=30)
        assert len(result) == 0

    def test_already_expired_excluded(self) -> None:
        expired = _ref("expired", created_at_ms=NOW_MS - 2 * DAY_MS, expires_at_ms=NOW_MS - 1)
        cfg = CredentialVaultConfig(vault_id="v", credentials=(expired,))
        result = list_expiring_soon(cfg, NOW_MS, horizon_days=30)
        assert len(result) == 0

    def test_no_expiry_excluded(self) -> None:
        no_exp = _ref("no-exp", expires_at_ms=None)
        cfg = CredentialVaultConfig(vault_id="v", credentials=(no_exp,))
        result = list_expiring_soon(cfg, NOW_MS)
        assert len(result) == 0
