from dataclasses import dataclass, field


@dataclass
class ReviewFinding:
    file: str
    line: int
    message: str
    severity: str  # "info" | "warning" | "critical"


@dataclass
class ReviewResult:
    findings: list[ReviewFinding] = field(default_factory=list)
    confidence: float = 1.0
    model_used: str = "free"
    cost_usd: float = 0.0
    seconds_elapsed: float = 0.0


@dataclass
class CostReport:
    total_cost_usd: float = 0.0
    free_calls: int = 0   # low + mid tier — both local Ollama, $0
    smart_calls: int = 0  # advanced tier only — the only paid calls
    seconds_elapsed: float = 0.0