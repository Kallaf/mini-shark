# shark_negotiation_engine.py
from dataclasses import dataclass, field
from enum import Enum, auto


class NegotiationDecision(Enum):
    CONTINUE = auto()
    DEAL = auto()
    OUT = auto()


@dataclass
class NegotiationConfig:
    concession_threshold: int = 5
    annoyance_threshold: int = 5
    max_turns: int = 8


@dataclass
class NegotiationState:
    turns: int = 0
    concessions: int = 0
    annoyance: int = 0
    history: list = field(default_factory=list)


class SharkNegotiationEngine:
    def __init__(self, cfg: NegotiationConfig = None):
        self.cfg = cfg or NegotiationConfig()
        self.state = NegotiationState()

    def reset(self):
        self.state = NegotiationState()

    def step(self, scores: dict):
        """
        scores = {
          "concession": int,
          "annoyance": int,
          "reason": str
        }
        """
        self.state.turns += 1
        con = scores.get("concession", 0)
        ann = scores.get("annoyance", 0)
        reason = scores.get("reason", "")

        self.state.concessions += con
        self.state.annoyance += ann
        self.state.history.append(
            {"concession": con, "annoyance": ann, "reason": reason}
        )

        decision, decided_reason = NegotiationDecision.CONTINUE, None
        if self.state.concessions >= self.cfg.concession_threshold:
            decision = NegotiationDecision.DEAL
            decided_reason = "founder made enough concessions"
        elif self.state.annoyance >= self.cfg.annoyance_threshold:
            decision = NegotiationDecision.OUT
            decided_reason = "too much over-negotiation"
        elif self.state.turns >= self.cfg.max_turns:
            decision = NegotiationDecision.OUT
            decided_reason = "max turns exceeded"

        return {
            "decided": decision != NegotiationDecision.CONTINUE,
            "decision": decision,
            "reason": decided_reason,
            "state": {
                "turns": self.state.turns,
                "concessions": self.state.concessions,
                "annoyance": self.state.annoyance,
                "history": self.state.history,
            },
        }
