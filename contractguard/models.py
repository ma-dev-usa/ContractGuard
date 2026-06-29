from dataclasses import dataclass, field


@dataclass(frozen=True)
class Change:
    category: str
    severity: str
    location: str
    message: str
    recommendation: str
    breaking: bool = True


@dataclass
class ContractReport:
    old_title: str
    new_title: str
    result: str
    risk_level: str
    changes: list[Change] = field(default_factory=list)

    @property
    def breaking_count(self) -> int:
        return sum(1 for change in self.changes if change.breaking)
