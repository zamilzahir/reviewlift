"""Tracing: logs every AI call — tier, model, cost, latency, escalation."""

import json
import time
from dataclasses import asdict, dataclass, field


@dataclass
class TraceEvent:
    tier: str
    model_used: str
    confidence: float
    cost_usd: float
    seconds_elapsed: float
    escalated: bool


@dataclass
class Tracer:
    events: list[TraceEvent] = field(default_factory=list)

    def log_call(self, tier, model_used, confidence, cost_usd, seconds_elapsed, escalated):
        self.events.append(TraceEvent(tier, model_used, confidence, cost_usd, seconds_elapsed, escalated))

    def summary(self) -> dict:
        by_tier: dict[str, int] = {}
        for event in self.events:
            by_tier[event.tier] = by_tier.get(event.tier, 0) + 1
        return {
            "total_calls": len(self.events),
            "calls_by_tier": by_tier,
            "escalations": sum(1 for e in self.events if e.escalated),
            "total_cost_usd": round(sum(e.cost_usd for e in self.events), 6),
            "total_seconds": round(sum(e.seconds_elapsed for e in self.events), 3),
        }

    def to_json(self) -> str:
        return json.dumps({"events": [asdict(e) for e in self.events], "summary": self.summary()}, indent=2)