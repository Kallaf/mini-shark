# shark_race_engine.py
from dataclasses import dataclass, field
from enum import Enum, auto


class Decision(Enum):
    NOT_ENOUGH_DATA = auto()
    GOOD_INVESTMENT = auto()
    BAD_INVESTMENT = auto()


@dataclass
class Config:
    positive_threshold: int = 10
    negative_threshold: int = 10
    max_turns: int = 15


@dataclass
class RaceState:
    turns: int = 0
    positive: int = 0
    negative: int = 0
    history: list = field(default_factory=list)


class SharkRaceEngine:
    def __init__(self, cfg: Config = None):
        self.cfg = cfg or Config()
        self.state = RaceState()

    def reset(self):
        self.state = RaceState()

    def step(self, scores: dict):
        """
        scores = {
          "positive": int,
          "negative": int,
          "reason": str
        }
        """
        self.state.turns += 1
        pos = scores.get("positive", 0)
        neg = scores.get("negative", 0)
        reason = scores.get("reason", "")

        self.state.positive += pos
        self.state.negative += neg
        self.state.history.append(
            {"positive": pos, "negative": neg, "reason": reason}
        )

        # Decision logic
        decision, decided_reason = None, None
        if self.state.positive >= self.cfg.positive_threshold:
            decision = Decision.GOOD_INVESTMENT
            decided_reason = "positive threshold reached"
        elif self.state.negative >= self.cfg.negative_threshold:
            decision = Decision.BAD_INVESTMENT
            decided_reason = "negative threshold reached"
        elif self.state.turns >= self.cfg.max_turns:
            decision = Decision.NOT_ENOUGH_DATA
            decided_reason = "max turns reached"

        return {
            "decided": decision is not None,
            "decision": decision,
            "reason": decided_reason,
            "state": {
                "turns": self.state.turns,
                "positive": self.state.positive,
                "negative": self.state.negative,
                "history": self.state.history,
            },
        }
