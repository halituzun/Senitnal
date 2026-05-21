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
from sentinel.intelligence.historical_backtest import (
    BacktestAggregate,
    aggregate_records,
)
from sentinel.intelligence.historical_similarity import (
    HistoricalSimilarityInput,
    HistoricalSimilarityResult,
    evaluate_historical_similarity,
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
from sentinel.intelligence.reaction_memory import (
    InMemoryReactionMemoryStore,
    ReactionMemoryRecord,
    ReactionPattern,
    is_record_usable_for_live,
)
from sentinel.intelligence.reaction_taxonomy import (
    HistoricalEventFamily,
    MarketReactionMeasurement,
    ReactionWindow,
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
    "BacktestAggregate",
    "CommodityMacroSnapshot",
    "GelAlMetricsObservation",
    "HistoricalEventFamily",
    "HistoricalSimilarityInput",
    "HistoricalSimilarityResult",
    "InMemoryReactionMemoryStore",
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
    "MarketReactionMeasurement",
    "MultiSourceObservation",
    "NetEdgeBreakdown",
    "NewsEventSnapshot",
    "NewsFamily",
    "ReactionMemoryRecord",
    "ReactionPattern",
    "ReactionWindow",
    "SignalFusionInput",
    "SignalFusionResult",
    "SocialPlatform",
    "SocialSignalSnapshot",
    "SourceFamily",
    "TechnicalIndicatorSnapshot",
    "aggregate_records",
    "compute_net_edge",
    "compute_signal_fusion",
    "evaluate_historical_similarity",
    "evaluate_live_activation",
    "evaluate_live_conviction",
    "is_net_edge_actionable",
    "is_record_usable_for_live",
]
