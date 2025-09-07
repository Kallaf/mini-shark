from shark_race_engine import SharkRaceEngine, Config, Decision

engine = SharkRaceEngine(Config(positive_threshold=10, negative_threshold=10))

# Simulate turns
turns = [
    {"positive": 3, "negative": 0, "reason": "good market size"},
    {"positive": 0, "negative": 4, "reason": "high burn rate"},
    {"positive": 7, "negative": 0, "reason": "outstanding founder"}
]

for t in turns:
    out = engine.step(t)
    print("Turn:", out["state"]["turns"])
    print("Scores:", out["state"]["positive"], out["state"]["negative"])
    print("Reason:", t["reason"])
    if out["decided"]:
        print("FINAL DECISION:", out["decision"], "->", out["reason"])
        break
