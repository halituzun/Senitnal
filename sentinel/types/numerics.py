"""Numerics governance enums — canonical vocabulary in code.

Per NUMERICS_GOVERNANCE.md §6-12 and the patch rounds applied through
phase closure:

This module pins the closed enumerations that every numerics artifact
must use. No model, no validator, no dependency logic lives here; those
land in the 7b → 7d commits (AllowedRange + NumericDependency → NumericEntry
→ NumericsArtifact).

Constitutional discipline:
    - Each enum is a closed set; widening requires spec revision
    - Legacy / pre-patch vocabulary (higher_is_weaker, forbidden_in_v0_1,
      numerics_family, low_band) is REJECTED at the type boundary
    - 8 spec_family values (1 per numerics artifact N-U); M itself is a
      meta-spec and does NOT have its own numerics artifact family

What this module deliberately does NOT contain:
    - NumericEntry (Commit 7c)
    - NumericsArtifact (Commit 7d)
    - AllowedRange / NumericDependency (Commit 7b)
    - CompatibilityClass (Commit 7d alongside artifact metadata)
    - No-default rule enforcement
    - Dependency expression validation
"""

from __future__ import annotations

from enum import StrEnum


class NumericUnit(StrEnum):
    """Closed set of numeric units (M §8 NumericEntry schema)."""

    COUNT = "count"
    MS = "ms"
    BYTES = "bytes"
    RATIO = "ratio"
    PERCENTAGE = "percentage"
    ENUM = "enum"
    ENUM_SET = "enum_set"
    BAND_NAME = "band_name"
    BOOL = "bool"


class Directionality(StrEnum):
    """How tightening / loosening a key affects safety (M §10)."""

    HIGHER_IS_STRICTER = "higher_is_stricter"
    LOWER_IS_STRICTER = "lower_is_stricter"
    BIDIRECTIONAL_SENSITIVE = "bidirectional_sensitive"
    NEUTRAL = "neutral"


class ChangeClass(StrEnum):
    """Compatibility class for a numeric change (M §7).

    Patched through phase closure. Legacy values such as
    `forbidden_in_v0_1` are NOT in this enum; they collapse to
    `forbidden`. U patches normalized `genesis_affecting` as a shift
    class; it lives here too.
    """

    CLARIFICATION = "clarification"
    OPERATIONAL_NO_BEHAVIOR_CHANGE = "operational_no_behavior_change"
    SAFETY_TIGHTENING = "safety_tightening"
    SAFETY_WEAKENING = "safety_weakening"
    GENESIS_AFFECTING = "genesis_affecting"
    FORBIDDEN = "forbidden"


class NumericRiskFamily(StrEnum):
    """Risk family for a numeric (M §5; 6 closed families)."""

    SAFETY_CRITICAL = "safety_critical"
    RESOURCE_LIMITS = "resource_limits"
    CALIBRATION_BANDS = "calibration_bands"
    IDENTITY_RETENTION = "identity_retention"
    OPERATIONAL_CONVENIENCE = "operational_convenience"
    EXPERIMENTAL = "experimental"


class RelationshipType(StrEnum):
    """NumericDependency relationship types (M §12, patch-applied).

    9 canonical values. Patches added the four `_or_equal` and `computed_*`
    forms; pre-patch vocabulary (e.g. plain `computed_less_than` without
    `_or_equal`) is NOT canonical and is rejected here.

    `computed_less_than_or_equal` / `computed_greater_than_or_equal` require
    the `expression` field on the NumericDependency (Commit 7b will model
    this requirement).
    """

    IMPLIES_MINIMUM_OF = "implies_minimum_of"
    MUST_BE_WITHIN_FACTOR_OF = "must_be_within_factor_of"
    MUST_BE_LESS_THAN = "must_be_less_than"
    MUST_BE_GREATER_THAN = "must_be_greater_than"
    MUST_BE_LESS_THAN_OR_EQUAL = "must_be_less_than_or_equal"
    MUST_BE_GREATER_THAN_OR_EQUAL = "must_be_greater_than_or_equal"
    COMPUTED_LESS_THAN_OR_EQUAL = "computed_less_than_or_equal"
    COMPUTED_GREATER_THAN_OR_EQUAL = "computed_greater_than_or_equal"
    MUST_CHANGE_TOGETHER = "must_change_together"


class SpecFamily(StrEnum):
    """Numerics artifact owning specifications (8 closed families).

    One per numerics artifact (N-U). NUMERICS_GOVERNANCE itself is the
    meta-spec and does NOT have its own numerics artifact family; it
    governs the others.
    """

    INGRESS_COMPILER = "ingress_compiler"
    REPLAY_PROTOCOL = "replay_protocol"
    MEMORY_WRITE_GATE = "memory_write_gate"
    OBSERVER_LEDGER = "observer_ledger"
    BACKUP_STRATEGY = "backup_strategy"
    BOOTSTRAP_GENOME = "bootstrap_genome"
    RECALL_PROTOCOL = "recall_protocol"
    ADAPTER_TRUST = "adapter_trust"
