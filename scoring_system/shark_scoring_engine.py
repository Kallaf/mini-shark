from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple
import time

class Decision(Enum):
    NOT_ENOUGH_DATA = "not_enough_data"
    GOOD_INVESTMENT = "good_investment"
    BAD_INVESTMENT = "bad_investment"

class Reason(Enum):
    THRESHOLD = "threshold_crossed"
    RED_FLAG = "red_flag"
    GREEN_FLAG = "green_flag"
    TURN_LIMIT = "turn_limit"
    WEIGHT_EXHAUSTED = "weight_exhausted"   # new
    MANUAL = "manual"
    CONTINUE = "continue"

@dataclass
class ParamEval:
    weight: float
    score: float  # positive or negative, typically in [-5,5]
    evidence: Optional[str] = None
    updated_at: float = field(default_factory=time.time)

    def contribution(self) -> float:
        return self.weight * self.score

@dataclass
class Config:
    positive_threshold: float = 3.0
    negative_threshold: float = -3.0
    min_total_weight_for_decision: float = 1.5

    # New "exhaustion" rule: if we've collected *too much* weighted info
    # without crossing decision thresholds, the shark opts out.
    max_total_weight_for_exhaustion: float = 10

    # Conversation governance
    max_turns: int = 20

    # Negotiation fatigue
    max_frustration: int = 3

    # Flag scores (overrides). Keep magnitudes but controller uses presence primarily
    red_flag_override: float = -999.0
    green_flag_override: float = 999.0

    # Optional clipping for extreme parameter scores
    max_abs_parameter_score: float = 5.0

RED_FLAG_ALIASES = {
    "scam", "fraud_risk", "unrealistic_claims", "out_of_scope",
    "over_negotiation", "harassment", "safety_violation",
    "irrelevant_loop", "no_ownership", "legal_blocker"
}

GREEN_FLAG_ALIASES = {
    "unicorn_potential", "exceptional_founder", "strong_traction",
    "defensible_moat", "strategic_synergy", "compelling_terms"
}

@dataclass
class Tally:
    params: Dict[str, ParamEval] = field(default_factory=dict)
    flags_red: List[str] = field(default_factory=list)
    flags_green: List[str] = field(default_factory=list)
    history_total_scores: List[float] = field(default_factory=lambda: [0.0])
    history_new_params_count: List[int] = field(default_factory=lambda: [0])
    turn: int = 0
    frustration: int = 0
    decided: bool = False
    decision: Optional[Decision] = None
    reason: Optional[Reason] = None

    def total_weight(self) -> float:
        return sum(p.weight for p in self.params.values())

    def total_score(self) -> float:
        base = sum(p.contribution() for p in self.params.values())
        # small nudges (primary effect uses flags for overrides)
        if self.flags_green:
            base += 1.0
        if self.flags_red:
            base -= 1.0
        return base

class SharkScoringEngine:
    """Scoring controller.

    Changes compared to earlier versions:
     - Replaces the previous stalemate detector with a **weight-exhaustion** rule:
       if the accumulated total parameter weight reaches `max_total_weight_for_exhaustion`
       without crossing either positive/negative score thresholds, the Shark opts out.
     - Adds structured `decision_reasons` (human-readable) to explain decisions.
    """

    def __init__(self, cfg: Optional[Config] = None):
        self.cfg = cfg or Config()
        self.state = Tally()

    def reset(self):
        self.state = Tally()

    def _apply_params(self, parameters: Dict[str, Dict]) -> Tuple[int, float]:
        before = self.state.total_score()
        new_keys = 0
        for name, d in parameters.items():
            weight = float(d.get("weight", 0.0))
            score = float(d.get("score", 0.0))

            score = max(-self.cfg.max_abs_parameter_score, min(self.cfg.max_abs_parameter_score, score))
            evidence = d.get("evidence")

            if name in self.state.params:
                self.state.params[name].weight = weight
                self.state.params[name].score = score
                self.state.params[name].evidence = evidence or self.state.params[name].evidence
                self.state.params[name].updated_at = time.time()
            else:
                self.state.params[name] = ParamEval(weight=weight, score=score, evidence=evidence)
                new_keys += 1

        after = self.state.total_score()
        return new_keys, after - before

    def _apply_flags(self, flags: List[str]) -> Tuple[bool, bool]:
        reds, greens = False, False
        for f in flags:
            f = f.strip().lower()
            if f in RED_FLAG_ALIASES and f not in self.state.flags_red:
                self.state.flags_red.append(f)
                reds = True
            if f in GREEN_FLAG_ALIASES and f not in self.state.flags_green:
                self.state.flags_green.append(f)
                greens = True
        return reds, greens

    def _maybe_raise_frustration(self, new_params_count: int, delta_score: float):
        if new_params_count == 0 and abs(delta_score) < 0.25:
            self.state.frustration += 1
        else:
            self.state.frustration = max(0, self.state.frustration - 1)

    def _compile_decision_reasons(self, decision: Optional[Decision], reason: Optional[Reason]) -> List[str]:
        """Create a short human-readable list explaining why the decision was reached."""
        s = self.state
        cfg = self.cfg
        reasons: List[str] = []

        # Helper: top contributors (by absolute contribution)
        items = [(name, p.contribution(), p.evidence or "") for name, p in s.params.items()]
        # sort positives and negatives separately
        pos_sorted = sorted([it for it in items if it[1] > 0], key=lambda x: -x[1])
        neg_sorted = sorted([it for it in items if it[1] < 0], key=lambda x: x[1])  # more negative first

        if reason == Reason.RED_FLAG:
            reasons.append("Red flag(s) triggered: " + ", ".join(s.flags_red))
            for name, contrib, ev in neg_sorted[:3]:
                reasons.append(f"{name}: {contrib:.2f}. {ev}".strip())
            return reasons

        if reason == Reason.GREEN_FLAG:
            reasons.append("Green flag(s) triggered: " + ", ".join(s.flags_green))
            for name, contrib, ev in pos_sorted[:3]:
                reasons.append(f"{name}: +{contrib:.2f}. {ev}".strip())
            return reasons

        if reason == Reason.THRESHOLD and decision is not None:
            if decision == Decision.GOOD_INVESTMENT:
                reasons.append("Score crossed positive threshold.")
                for name, contrib, ev in pos_sorted[:3]:
                    reasons.append(f"{name}: +{contrib:.2f}. {ev}".strip())
                return reasons
            else:
                reasons.append("Score crossed negative threshold.")
                for name, contrib, ev in neg_sorted[:3]:
                    reasons.append(f"{name}: {contrib:.2f}. {ev}".strip())
                return reasons

        if reason == Reason.WEIGHT_EXHAUSTED:
            reasons.append(f"Collected a lot of information (total weight {s.total_weight():.2f}) without a decisive score; Shark opts out.")
            if neg_sorted:
                reasons.append("Top concerns:")
                for name, contrib, ev in neg_sorted[:3]:
                    reasons.append(f"- {name}: {contrib:.2f}. {ev}".strip())
            else:
                reasons.append("No strong negative contributors captured; decision is due to indecision despite high information coverage.")
            return reasons

        if reason == Reason.TURN_LIMIT:
            reasons.append(f"Reached maximum turns ({cfg.max_turns}) without a decisive score.")
            if neg_sorted:
                reasons.append("Top concerns:")
                for name, contrib, ev in neg_sorted[:3]:
                    reasons.append(f"- {name}: {contrib:.2f}. {ev}".strip())
            return reasons

        if reason == Reason.MANUAL:
            reasons.append("Decision made manually by controller/operator.")
            return reasons

        return reasons

    def _decide_if_any(self) -> Tuple[bool, Optional[Decision], Optional[Reason]]:
        cfg = self.cfg
        s = self.state

        # Priority 1: overrides
        if s.flags_red:
            s.decided = True
            s.decision = Decision.BAD_INVESTMENT
            s.reason = Reason.RED_FLAG
            return True, s.decision, s.reason
        if s.flags_green:
            s.decided = True
            s.decision = Decision.GOOD_INVESTMENT
            s.reason = Reason.GREEN_FLAG
            return True, s.decision, s.reason

        # Priority 2: thresholds (only if enough data)
        total_w = s.total_weight()
        total = s.total_score()
        if total_w >= cfg.min_total_weight_for_decision:
            if total >= cfg.positive_threshold:
                s.decided = True
                s.decision = Decision.GOOD_INVESTMENT
                s.reason = Reason.THRESHOLD
                return True, s.decision, s.reason
            if total <= cfg.negative_threshold:
                s.decided = True
                s.decision = Decision.BAD_INVESTMENT
                s.reason = Reason.THRESHOLD
                return True, s.decision, s.reason

        # NEW: Priority 3: weight exhaustion - we've collected a lot of weighted info but still undecided
        if total_w >= cfg.max_total_weight_for_exhaustion:
            s.decided = True
            s.decision = Decision.BAD_INVESTMENT
            s.reason = Reason.WEIGHT_EXHAUSTED
            return True, s.decision, s.reason

        # Priority 4: turn limit
        if s.turn >= cfg.max_turns:
            s.decided = True
            s.decision = Decision.NOT_ENOUGH_DATA
            s.reason = Reason.TURN_LIMIT
            return True, s.decision, s.reason

        # Priority 5: frustration -> red flag
        if s.frustration >= cfg.max_frustration:
            s.flags_red.append("over_negotiation")
            s.decided = True
            s.decision = Decision.BAD_INVESTMENT
            s.reason = Reason.RED_FLAG
            return True, s.decision, s.reason

        return False, None, None

    def step(self, evaluation: Dict) -> Dict:
        """Consume one LLM evaluation payload (parameters + flags)."""
        self.state.turn += 1

        params = evaluation.get("parameters", {}) or {}
        flags = evaluation.get("flags", []) or []

        new_params_count, delta_score = self._apply_params(params)
        self._apply_flags(flags)

        self.state.history_total_scores.append(self.state.total_score())
        self.state.history_new_params_count.append(new_params_count)

        self._maybe_raise_frustration(new_params_count, delta_score)

        decided, decision, reason = self._decide_if_any()

        out = {
            "turn": self.state.turn,
            "decided": decided,
            "decision": decision.value if decision else None,
            "reason": reason.value if reason else Reason.CONTINUE.value,
            "total_score": self.state.total_score(),
            "total_weight": self.state.total_weight(),
            "flags_red": list(self.state.flags_red),
            "flags_green": list(self.state.flags_green),
            "frustration": self.state.frustration,
            "params": {k: {"weight": v.weight, "score": v.score, "evidence": v.evidence}
                       for k, v in self.state.params.items()},
        }

        if decided:
            out["decision_reasons"] = self._compile_decision_reasons(decision, reason)
        else:
            out["decision_reasons"] = []

        return out

    def force_decide(self, decision: Decision, reason: Reason = Reason.MANUAL) -> Dict:
        self.state.decided = True
        self.state.decision = decision
        self.state.reason = reason
        return {
            "turn": self.state.turn,
            "decided": True,
            "decision": decision.value,
            "reason": reason.value,
            "total_score": self.state.total_score(),
            "total_weight": self.state.total_weight(),
            "flags_red": list(self.state.flags_red),
            "flags_green": list(self.state.flags_green),
            "frustration": self.state.frustration,
            "decision_reasons": self._compile_decision_reasons(decision, reason),
        }

# --- Quick demo to show weight-exhaustion behavior ---
if __name__ == "__main__":
    engine = SharkScoringEngine()

    inputs = [
        {"parameters": {"market_size": {"weight": 0.8, "score": +0.5, "evidence": "TAM moderate"}}},
        {"parameters": {"unit_economics": {"weight": 0.8, "score": -0.4, "evidence": "thin margins"}}},
        {"parameters": {"traction": {"weight": 0.9, "score": +0.3, "evidence": "early users"}}},
        {"parameters": {"team_experience": {"weight": 0.8, "score": -0.2, "evidence": "first-time founders"}}},
        {"parameters": {"valuation": {"weight": 0.3, "score": -0.1, "evidence": "high valuation"}}},
        {"parameters": {"customer_acquisition_cost": {"weight": 0.7, "score": -0.3, "evidence": "CAC is high"}}},
        {"parameters": {"net_profit": {"weight": 0.6, "score": +0.2, "evidence": "profitable last quarter"}}},
        {"parameters": {"scalability": {"weight": 0.5, "score": +0.4, "evidence": "scalable tech"}}},
        {"parameters": {"licensing": {"weight": 0.4, "score": +0.1, "evidence": "IP secured"}}},
        {"parameters": {"competition": {"weight": 0.7, "score": -0.5, "evidence": "crowded market"}}},
        {"parameters": {"growth_rate": {"weight": 0.6, "score": +0.3, "evidence": "20% MoM growth"}}},
        {"parameters": {"churn_rate": {"weight": 0.5, "score": -0.2, "evidence": "churn is rising"}}},
        {"parameters": {"brand_strength": {"weight": 0.4, "score": +0.2, "evidence": "strong brand"}}},
        {"parameters": {"distribution": {"weight": 0.6, "score": +0.1, "evidence": "good distribution"}}},
        {"parameters": {"supply_chain": {"weight": 0.5, "score": -0.3, "evidence": "supply chain issues"}}},
        {"parameters": {"international_expansion": {"weight": 0.3, "score": +0.2, "evidence": "expanding overseas"}}},
        {"parameters": {"product_quality": {"weight": 0.7, "score": +0.4, "evidence": "high quality"}}},
        {"parameters": {"user_engagement": {"weight": 0.6, "score": +0.3, "evidence": "active users"}}},
        {"parameters": {"funding_history": {"weight": 0.5, "score": -0.1, "evidence": "previous round failed"}}},
        {"parameters": {"exit_strategy": {"weight": 0.4, "score": +0.2, "evidence": "clear exit plan"}}},
        {"parameters": {"partnerships": {"weight": 0.6, "score": +0.3, "evidence": "strategic partners"}}},
        {"parameters": {"technology_stack": {"weight": 0.5, "score": +0.2, "evidence": "modern stack"}}},
        {"parameters": {"market_trends": {"weight": 0.7, "score": +0.1, "evidence": "positive trends"}}},
        {"parameters": {"regulatory_risk": {"weight": 0.6, "score": -0.4, "evidence": "regulatory uncertainty"}}},
        {"parameters": {"customer_feedback": {"weight": 0.5, "score": +0.3, "evidence": "positive feedback"}}},
    ]

    for i, inp in enumerate(inputs, 1):
        out = engine.step(inp)
        print(f"Turn {out['turn']} -> decided={out['decided']}, decision={out['decision']}, reason={out['reason']}")
        print("  total_weight=", out["total_weight"], " total_score=", out["total_score"])
        if out["decision_reasons"]:
            print("  reasons:")
            for r in out["decision_reasons"]:
                print("   -", r)
        print("---")
        if out["decided"]:
            break
