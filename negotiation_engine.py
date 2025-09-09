class NegotiationEngine:
    def __init__(self, limit_per_decision):
        """
        limit_per_decision: dict mapping decision names to their negotiation limits
        """
        self.limit_per_decision = limit_per_decision
        self.negotiations_count = {decision: 0 for decision in limit_per_decision}

    def negotiate(self, decision):
        """
        Increments negotiation count for a decision.
        Returns:
            'ok' if under limit,
            'warning' if about to reach limit (one less than limit),
            'out' if limit reached or exceeded.
        """
        if decision not in self.limit_per_decision:
            raise ValueError(f"Unknown decision: {decision}")

        self.negotiations_count[decision] += 1
        count = self.negotiations_count[decision]
        limit = self.limit_per_decision[decision]
        
        print(f"Negotiation count for {decision}: {count}/{limit}")

        if count >= limit:
            return 'out'
        elif count == limit - 1:
            return 'warning'
        else:
            return 'ok'

    def get_state(self, decision):
        """
        Returns current state for a decision without incrementing.
        """
        count = self.negotiations_count.get(decision, 0)
        limit = self.limit_per_decision.get(decision)
        if limit is None:
            raise ValueError(f"Unknown decision: {decision}")

        if count >= limit:
            return 'out'
        elif count == limit - 1:
            return 'warning'
        else:
            return 'ok'