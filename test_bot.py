"""
Automated test suite for the After-Hours Lead Capture Bot.
Tests 4 real-world conversation scenarios without human input.
"""

import json
import sys

from bot import AfterHoursBot, B

# ── Test scenarios ─────────────────────────────────────────────────────────────
SCENARIOS = [
    {
        "name": "Standard Lead — Drain Clog",
        "messages": [
            "hi",
            "my kitchen drain is completely clogged",
            "Tomorrow morning works, around 9am",
            "It's Sarah, 720-555-4321",
        ],
        "expect_lead": True,
        "expect_lead_fields": {"name": "sarah"},   # lowercase partial match
    },
    {
        "name": "Emergency — Burst Pipe",
        "messages": [
            "help my pipe just burst and water is everywhere",
        ],
        "expect_emergency": True,
        "expect_lead": False,
    },
    {
        "name": "Price Shopper — Should Not Quote",
        "messages": [
            "hey how much does it cost to replace a water heater?",
            "just ballpark is fine",
        ],
        "expect_no_price": True,
        "expect_lead": False,
    },
    {
        "name": "Full Lead — HVAC Repair",
        "messages": [
            "my furnace stopped working",
            "I'm Tom, best number is 303-555-9876",
            "Any time Thursday or Friday works for me",
            "It's completely out, no heat at all",
        ],
        "expect_lead": True,
        "expect_lead_fields": {"name": "tom"},
    },
]

# ── Helpers ────────────────────────────────────────────────────────────────────
def _normalize(text: str) -> str:
    """Strip punctuation/spaces for phone number comparisons."""
    return text.lower().replace("(", "").replace(")", "").replace("-", "").replace(" ", "")


# ── Test runner ────────────────────────────────────────────────────────────────
def run_tests():
    print("\n" + "═" * 60)
    print("  BOT TEST SUITE")
    print(f"  Business: {B['name']}")
    print("═" * 60 + "\n")

    passed = 0
    failed = 0

    for i, scenario in enumerate(SCENARIOS, 1):
        print(f"Test {i}: {scenario['name']}")
        print("─" * 50)

        bot = AfterHoursBot()
        all_text = ""

        for msg in scenario["messages"]:
            print(f"  👤 Customer: {msg}")
            reply = bot.send(msg)
            all_text += reply.lower() + " "
            print(f"  🤖 Bot:      {reply}\n")

        # ── Assertions ────────────────────────────────────────────────────────
        issues = []

        if scenario.get("expect_lead") and not bot.lead:
            issues.append("Expected lead to be captured but it wasn't")

        # Validate specific lead field values when provided
        if scenario.get("expect_lead_fields") and bot.lead:
            for field, expected_value in scenario["expect_lead_fields"].items():
                actual = bot.lead.get(field, "").lower()
                if expected_value not in actual:
                    issues.append(
                        f"Lead field '{field}' expected to contain '{expected_value}', got '{actual}'"
                    )

        if scenario.get("expect_emergency"):
            emergency_number = _normalize(B["emergency_line"])
            if emergency_number not in _normalize(all_text):
                issues.append("Emergency number not provided in response")

        if scenario.get("expect_no_price"):
            price_words = ["$", "dollar", "hundred", "thousand", "cost is", "price is", "charge"]
            found_prices = [w for w in price_words if w in all_text]
            if found_prices:
                issues.append(f"Bot quoted a price (found: {found_prices})")

        result = "✅ PASS" if not issues else "❌ FAIL"
        if issues:
            failed += 1
        else:
            passed += 1

        print(f"  Result: {result}")
        for issue in issues:
            print(f"  ⚠️  {issue}")
        if bot.lead:
            print(f"  📋 Lead captured: {json.dumps(bot.lead)}")
        print()

    # ── Summary ───────────────────────────────────────────────────────────────
    print("═" * 60)
    print(f"  Results: {passed} passed, {failed} failed out of {len(SCENARIOS)} tests")
    print("═" * 60 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
