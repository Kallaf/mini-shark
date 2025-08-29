import json
import re
import random

class MockLLM:
    _instance = None
    _conversation_states = [
        "q&a",
        "negotiation",
        "end"
    ]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MockLLM, cls).__new__(cls)
            cls._instance.conversation_state = 0
        return cls._instance

    def generate_content(self, prompt: str):
        if re.search(r"Summarize the Shark Tank pitch session", prompt, re.IGNORECASE):
            return self._mock_report_response()

        response = {
            "currentState": self._conversation_states[self.conversation_state],
            "message": self._mock_message(self.conversation_state),
            "checklistUpdate": self._mock_checklist(self.conversation_state),
            "decision": self._mock_decision(self.conversation_state)
        }

        self.conversation_state = min(self.conversation_state + 1, len(self._conversation_states))

        return type("MockResponse", (), {"text": json.dumps(response)})

    def _mock_message(self, state):
        messages = [
            "Interesting pitch. What are your margins and customer acquisition cost?",
            "I'll offer 500,000 EGP for 20% equity.",
            "Thanks for pitching."
        ]
        return messages[state]


    def _mock_checklist(self, state):
        return {
            "valuation": state >= 0,
            "equity": state >= 0,
            "revenue": state >= 1,
            "grossMargin": state >= 1,
            "customerAcquisitionCost": state >= 1,
            "netProfit": state >= 2,
            "scalability": state >= 2,
            "licensing": state >= 2
        }

    def _mock_decision(self, state):
        decisions = ["offer", "pass"]
        if state >= 1:
            return random.choice(decisions)
        return "null"

    def _mock_report_response(self):
        report = """
Entrepreneur: Ahmed  
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
        self.conversation_state = 1
