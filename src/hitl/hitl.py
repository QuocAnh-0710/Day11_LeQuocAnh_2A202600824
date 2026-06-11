"""
Lab 11 — Part 4: Human-in-the-Loop Design
  TODO 12: Confidence Router
  TODO 13: Design 3 HITL decision points
"""
from dataclasses import dataclass


# ============================================================
# TODO 12: Implement ConfidenceRouter
#
# Route agent responses based on confidence scores:
#   - HIGH (>= 0.9): Auto-send to user
#   - MEDIUM (0.7 - 0.9): Queue for human review
#   - LOW (< 0.7): Escalate to human immediately
#
# Special case: if the action is HIGH_RISK (e.g., money transfer,
# account deletion), ALWAYS escalate regardless of confidence.
#
# Implement the route() method.
# ============================================================

HIGH_RISK_ACTIONS = [
    "transfer_money",
    "close_account",
    "change_password",
    "delete_data",
    "update_personal_info",
]


@dataclass
class RoutingDecision:
    """Result of the confidence router."""
    action: str          # "auto_send", "queue_review", "escalate"
    confidence: float
    reason: str
    priority: str        # "low", "normal", "high"
    requires_human: bool


class ConfidenceRouter:
    """Route agent responses based on confidence and risk level.

    Thresholds:
        HIGH:   confidence >= 0.9 -> auto-send
        MEDIUM: 0.7 <= confidence < 0.9 -> queue for review
        LOW:    confidence < 0.7 -> escalate to human

    High-risk actions always escalate regardless of confidence.
    """

    HIGH_THRESHOLD = 0.9
    MEDIUM_THRESHOLD = 0.7

    def route(self, response: str, confidence: float,
              action_type: str = "general") -> RoutingDecision:
        """Route a response based on confidence score and action type.

        Args:
            response: The agent's response text
            confidence: Confidence score between 0.0 and 1.0
            action_type: Type of action (e.g., "general", "transfer_money")

        Returns:
            RoutingDecision with routing action and metadata
        """
        if action_type in HIGH_RISK_ACTIONS:
            return RoutingDecision(
                action="escalate",
                confidence=confidence,
                reason=f"High-risk action: {action_type}",
                priority="high",
                requires_human=True,
            )

        if confidence >= self.HIGH_THRESHOLD:
            return RoutingDecision(
                action="auto_send",
                confidence=confidence,
                reason="High confidence",
                priority="low",
                requires_human=False,
            )
        elif confidence >= self.MEDIUM_THRESHOLD:
            return RoutingDecision(
                action="queue_review",
                confidence=confidence,
                reason="Medium confidence — needs review",
                priority="normal",
                requires_human=True,
            )
        else:
            return RoutingDecision(
                action="escalate",
                confidence=confidence,
                reason="Low confidence — escalating",
                priority="high",
                requires_human=True,
            )


# ============================================================
# TODO 13: Design 3 HITL decision points
#
# For each decision point, define:
# - trigger: What condition activates this HITL check?
# - hitl_model: Which model? (human-in-the-loop, human-on-the-loop,
#   human-as-tiebreaker)
# - context_needed: What info does the human reviewer need?
# - example: A concrete scenario
#
# Think about real banking scenarios where human judgment is critical.
# ============================================================

hitl_decision_points = [
    {
        "id": 1,
        "name": "Large Financial Transaction Approval",
        "trigger": (
            "User requests a money transfer or withdrawal above 50,000,000 VND, "
            "or the action_type is 'transfer_money' / 'close_account'. "
            "Triggered regardless of model confidence."
        ),
        "hitl_model": "human-in-the-loop",
        "context_needed": (
            "Full transaction details (amount, source account, destination account), "
            "user identity verification status, account history for the past 30 days, "
            "any recent suspicious activity flags."
        ),
        "example": (
            "Customer asks the agent to transfer 200,000,000 VND to an external account. "
            "The agent queues the request and a human bank officer must approve or reject "
            "the transaction before it is executed."
        ),
    },
    {
        "id": 2,
        "name": "Low-Confidence or Ambiguous Response Review",
        "trigger": (
            "The ConfidenceRouter assigns a score below 0.7, or the LLM-as-Judge returns "
            "UNSAFE / RELEVANCE < 3. The agent's response may be inaccurate or misleading."
        ),
        "hitl_model": "human-on-the-loop",
        "context_needed": (
            "The user's original question, the agent's drafted response, "
            "the judge scores (safety, relevance, accuracy, tone), "
            "and relevant FAQ/policy documents for fact-checking."
        ),
        "example": (
            "Customer asks about a new government loan subsidy scheme. "
            "The agent produces a response with accuracy score 2/5. "
            "A compliance officer reviews the draft before it is sent and corrects "
            "any outdated interest rate figures."
        ),
    },
    {
        "id": 3,
        "name": "Repeated Security Alert Escalation",
        "trigger": (
            "A single user session triggers 3 or more injection/blocked alerts within "
            "10 minutes, indicating a possible automated attack or persistent bad actor."
        ),
        "hitl_model": "human-as-tiebreaker",
        "context_needed": (
            "Full session transcript with timestamps, list of blocked prompts, "
            "user account details and IP address, and block-rate anomaly metrics "
            "from the monitoring dashboard."
        ),
        "example": (
            "An automated script sends 5 prompt injection attempts in 3 minutes targeting "
            "the agent. The monitoring alert fires. A security analyst reviews the session "
            "and decides whether to permanently block the user account or flag it for "
            "further investigation."
        ),
    },
]


# ============================================================
# Quick tests
# ============================================================

def test_confidence_router():
    """Test ConfidenceRouter with sample scenarios."""
    router = ConfidenceRouter()

    test_cases = [
        ("Balance inquiry", 0.95, "general"),
        ("Interest rate question", 0.82, "general"),
        ("Ambiguous request", 0.55, "general"),
        ("Transfer $50,000", 0.98, "transfer_money"),
        ("Close my account", 0.91, "close_account"),
    ]

    print("Testing ConfidenceRouter:")
    print("=" * 80)
    print(f"{'Scenario':<25} {'Conf':<6} {'Action Type':<18} {'Decision':<15} {'Priority':<10} {'Human?'}")
    print("-" * 80)

    for scenario, conf, action_type in test_cases:
        decision = router.route(scenario, conf, action_type)
        print(
            f"{scenario:<25} {conf:<6.2f} {action_type:<18} "
            f"{decision.action:<15} {decision.priority:<10} "
            f"{'Yes' if decision.requires_human else 'No'}"
        )

    print("=" * 80)


def test_hitl_points():
    """Display HITL decision points."""
    print("\nHITL Decision Points:")
    print("=" * 60)
    for point in hitl_decision_points:
        print(f"\n  Decision Point #{point['id']}: {point['name']}")
        print(f"    Trigger:  {point['trigger']}")
        print(f"    Model:    {point['hitl_model']}")
        print(f"    Context:  {point['context_needed']}")
        print(f"    Example:  {point['example']}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_confidence_router()
    test_hitl_points()
