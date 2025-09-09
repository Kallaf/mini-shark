import json
from typing import List, Dict

# -----------------------------
# 1. Scoring Extractor (stub)
# -----------------------------
def extract_score(conversation: str) -> Dict:
    """
    Call your LLM here with the scoring prompt.
    For now, return a dummy JSON to illustrate the flow.
    """
    # Example LLM output:
    response = """
    {
      "weight": 20,
      "score": 0.7,
      "pros": ["Strong founder background", "Large market"],
      "cons": ["High burn rate"]
    }
    """
    return json.loads(response)


# -----------------------------
# 2. Accumulation Engine
# -----------------------------
class ScoringEngine:
    def __init__(self, max_weight: int = 100, max_turns: int = 15):
        self.max_weight = max_weight
        self.max_turns = max_turns
        self.turns = 0
        self.total_weight = 0
        self.weighted_score_sum = 0.0
        self.all_pros: List[str] = []
        self.all_cons: List[str] = []

    def update(self, scoring: Dict):
        weight = scoring["weight"]
        score = scoring["score"]

        self.total_weight += weight
        self.weighted_score_sum += weight * score
        self.all_pros.extend(scoring.get("pros", []))
        self.all_cons.extend(scoring.get("cons", []))
        self.turns += 1

    def is_done(self) -> bool:
        print(f"Turns: {self.turns}, Total Weight: {self.total_weight}")  # Debug line
        return self.total_weight >= self.max_weight or self.turns >= self.max_turns

    def final_grade(self) -> float:
        if self.total_weight == 0:
            return 0.0
        print(f"Total Weight: {self.total_weight}, Weighted Score Sum: {self.weighted_score_sum}")  # Debug line
        return self.weighted_score_sum / self.total_weight * 100  # scale 0–100


# -----------------------------
# 3. Shark Personality Mapping
# -----------------------------
def shark1_decision(grade: float) -> str:
    if grade < 30:
        return "Out"
    elif grade < 50:
        return "Bad offer (don't negotiate much)"
    elif grade < 80:
        return "Fair but slightly low offer (light negotiation)"
    else:
        return "Good offer + upsell yourself"