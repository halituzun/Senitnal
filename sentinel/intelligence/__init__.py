"""V11 — Multi-source intelligence (core-adjacent, no network)."""

from sentinel.intelligence.conviction import (
    ActionabilityBand,
    LiveConvictionInput,
    LiveConvictionResult,
    evaluate_live_conviction,
)
from sentinel.intelligence.fusion import (
    SignalFusionInput,
    SignalFusionResult,
    compute_signal_fusion,
)
from sentinel.intelligence.live_activation import (
    LiveActivationInput,
    LiveActivationResult,
    LiveActivationStatus,
    LiveBudgetMode,
    LiveCapitalModel,
    evaluate_live_activation,
)
from sentinel.intelligence.net_edge import (
    NetEdgeBreakdown,
    compute_net_edge,
    is_net_edge_actionable,
)
from sentinel.intelligence.schemas import (
    CommodityMacroSnapshot,
    GelAlMetricsObservation,
    MacroEventKind,
    MacroEventSnapshot,
    MarketMicrostructureSnapshot,
    MultiSourceObservation,
    NewsEventSnapshot,
    NewsFamily,
    SocialPlatform,
    SocialSignalSnapshot,
    SourceFamily,
    TechnicalIndicatorSnapshot,
)

__all__ = [
    "ActionabilityBand",
    "CommodityMacroSnapshot",
    "GelAlMetricsObservation",
    "LiveActivationInput",
    "LiveActivationResult",
    "LiveActivationStatus",
    "LiveBudgetMode",
    "LiveCapitalModel",
    "LiveConvictionInput",
    "LiveConvictionResult",
    "MacroEventKind",
    "MacroEventSnapshot",
    "MarketMicrostructureSnapshot",
    "MultiSourceObservation",
    "NetEdgeBreakdown",
    "NewsEventSnapshot",
    "NewsFamily",
    "SignalFusionInput",
    "SignalFusionResult",
    "SocialPlatform",
    "SocialSignalSnapshot",
    "SourceFamily",
    "TechnicalIndicatorSnapshot",
    "compute_net_edge",
    "compute_signal_fusion",
    "evaluate_live_activation",
    "evaluate_live_conviction",
    "is_net_edge_actionable",
]
