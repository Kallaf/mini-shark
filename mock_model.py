import json
import re

class MockLLM:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MockLLM, cls).__new__(cls)
            cls._instance.state = 1
        return cls._instance

    def generate_content(self, prompt: str):
        if re.search(r"Summarize the Shark Tank pitch session", prompt, re.IGNORECASE):
            return self._mock_report_response()

        response = {
            "currentState": self.state,
            "message": self._mock_message(self.state),
            "sharkReaction": self._mock_reaction(self.state),
            "checklistUpdate": self._mock_checklist(self.state),
            "decision": self._mock_decision(self.state)
        }

        self.state = min(self.state + 1, 4)

        return type("MockResponse", (), {"text": json.dumps(response)})

    def _mock_message(self, state):
        messages = {
            1: "Interesting pitch. What's your revenue?",
            2: "What are your margins and customer acquisition cost?",
            3: "I'll offer 500,000 EGP for 20% equity.",
            4: "Let's negotiate. Would you consider 15%?"
        }
        return messages.get(state, "Thanks for pitching.")

    def _mock_reaction(self, state):
        return ["neutral", "skeptical", "impressed", "intrigued"][state - 1]

    def _mock_checklist(self, state):
        return {
            "valuation": state >= 1,
            "equity": state >= 1,
            "revenue": state >= 2,
            "grossMargin": state >= 2,
            "customerAcquisitionCost": state >= 2,
            "netProfit": state >= 3,
            "scalability": state >= 3,
            "licensing": state >= 4
        }

    def _mock_decision(self, state):
        return "offer" if state >= 4 else "null"

    def _mock_report_response(self):
        report = """
Entrepreneur: Nada  
Business Idea: AI-powered travel assistant for Egypt  
Key Metrics:  
- Valuation: 1M EGP  
- Revenue: 200K EGP  
- Gross Margin: 60%  
- CAC: 50 EGP  
- Net Profit: 40K EGP  

Shark Reaction: Skeptical but intrigued  
Final Decision: Offer made — 500K EGP for 20% equity  
Advice: Focus on licensing and recurring revenue
"""
        return type("MockResponse", (), {"text": report})

    def reset(self):
        self.state = 1
