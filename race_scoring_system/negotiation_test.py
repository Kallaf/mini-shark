from shark_negotiation_engine import SharkNegotiationEngine, NegotiationConfig, NegotiationDecision

engine = SharkNegotiationEngine(NegotiationConfig(concession_threshold=5, annoyance_threshold=5))

turns = [
    {"concession": 1, "annoyance": 0, "reason": "founder lowered valuation slightly"},
    {"concession": 0, "annoyance": 2, "reason": "founder resists giving more equity"},
    {"concession": 2, "annoyance": 0, "reason": "founder agreed to board seat"},
    {"concession": 2, "annoyance": 0, "reason": "founder offered more equity"}
]

for t in turns:
    out = engine.step(t)
    print("Turn:", out["state"]["turns"])
    print("Scores:", out["state"]["concessions"], out["state"]["annoyance"])
    print("Reason:", t["reason"])
    if out["decided"]:
        print("FINAL DECISION:", out["decision"], "->", out["reason"])
        break
