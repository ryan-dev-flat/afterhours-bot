"""
After-Hours Lead Capture Bot
Demo version - runs in terminal to simulate WhatsApp conversations
"""

import json
import logging
import os
import re
from datetime import datetime
from typing import Callable, Optional
import anthropic

# ── Logging setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── Config loader ──────────────────────────────────────────────────────────────
def load_business(config_path: Optional[str] = None) -> dict:
    path = config_path or os.path.join(os.path.dirname(__file__), "business.json")
    with open(path, "r") as f:
        return json.load(f)

# Keep a module-level default for backwards compatibility with test_bot.py
B = load_business()

# ── System prompt builder ──────────────────────────────────────────────────────
def build_system_prompt(b: dict) -> str:
    return f"""You are the after-hours AI assistant for {b['name']}, a {b['type']} company in {b['location']}.

Your ONLY job is to:
1. Greet the customer warmly (first message only)
2. Find out what service they need
3. Collect: their name, best callback number, and preferred appointment time
4. Confirm details back to them and close warmly
5. Let them know {b['owner_name']} will confirm first thing in the morning

BUSINESS INFO:
- Services offered: {', '.join(b['services'])}
- Business hours: {b['hours']}
- Service area: {b['service_area']}
- Free estimates: {"Yes on all jobs" if b["free_estimate"] else "No"}

EMERGENCY PROTOCOL:
If the customer mentions any of these words: {', '.join(b['emergency_keywords'])}
→ Immediately say: "This sounds like an emergency. Please call our 24/7 emergency line right now: {b['emergency_line']}. We'll be there within the hour."
→ Then still offer to log their info as a backup.

CONVERSATION RULES:
- Keep every response SHORT — 2-3 sentences max. This is WhatsApp, not email.
- Be warm and human, not robotic.
- Never quote prices or make commitments only {b['owner_name']} can make.
- If asked something outside your knowledge, say "{b['owner_name']} will go over that with you in the morning."
- Once you have name + service + preferred time → confirm everything clearly and close the conversation warmly.
- Do not keep the conversation going after confirming — end it.

LEAD CAPTURE TRACKING:
Internally track when you have collected all three:
[ ] Service needed
[ ] Customer name
[ ] Preferred callback time or appointment window

When all three are collected, include this exact tag at the END of your response (hidden from customer view — on its own line after your message):
LEAD_CAPTURED: {{"name": "<name>", "service": "<service>", "time": "<preferred time>", "phone": "<phone if given>"}}
"""

# ── Bot class ──────────────────────────────────────────────────────────────────
MAX_HISTORY_TURNS = 10   # Keep last N user+assistant pairs to cap token usage

class AfterHoursBot:
    def __init__(
        self,
        config_path: Optional[str] = None,
        notify_fn: Optional[Callable[[dict, dict], None]] = None,
    ):
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY environment variable is not set. "
                "Export it before running the bot."
            )
        self.client = anthropic.Anthropic(api_key=api_key)
        self.business = load_business(config_path)
        self.system_prompt = build_system_prompt(self.business)
        self.history: list[dict] = []
        self.lead: Optional[dict] = None
        self._notify_fn = notify_fn or self._default_notify

    def send(self, user_message: str) -> str:
        self.history.append({"role": "user", "content": user_message})
        self._trim_history()

        try:
            response = self.client.messages.create(
                model="claude-haiku-4-5",   # Fast + cheap for production bots
                max_tokens=450,
                system=self.system_prompt,
                messages=self.history,
            )
        except anthropic.APIError as e:
            logger.error("Anthropic API error: %s", e)
            # Pop the user message we just added so history stays consistent
            self.history.pop()
            return (
                "Sorry, I'm having a technical hiccup right now. "
                f"Please call {self.business.get('emergency_line', 'us')} directly "
                "or try again in a moment."
            )

        full_reply = response.content[0].text

        # ── Parse lead capture tag if present ─────────────────────────────────
        lead_match = re.search(r"LEAD_CAPTURED:\s*(\{[^}]*\})", full_reply, re.DOTALL)
        if lead_match and not self.lead:
            try:
                self.lead = json.loads(lead_match.group(1))
                self._notify_fn(self.lead, self.business)
            except json.JSONDecodeError as e:
                logger.warning(
                    "Failed to parse LEAD_CAPTURED JSON — %s | raw: %s",
                    e, lead_match.group(1),
                )

        # Strip internal tag from customer-facing reply
        clean_reply = re.sub(r"\nLEAD_CAPTURED:.*", "", full_reply, flags=re.DOTALL).strip()

        self.history.append({"role": "assistant", "content": full_reply})
        return clean_reply

    def _trim_history(self):
        """Keep only the most recent MAX_HISTORY_TURNS user+assistant pairs."""
        max_messages = MAX_HISTORY_TURNS * 2
        if len(self.history) > max_messages:
            self.history = self.history[-max_messages:]

    def _default_notify(self, lead: dict, business: dict):
        """In production: send WhatsApp/SMS to owner. Here we just print."""
        print("\n" + "━" * 60)
        print("📬  OWNER NOTIFICATION (would send to owner's WhatsApp)")
        print(f"    Business: {business['name']}")
        print(f"    New lead captured at {datetime.now().strftime('%I:%M %p')}")
        for k, v in lead.items():
            print(f"    {k.capitalize()}: {v}")
        print("━" * 60 + "\n")


# ── Demo runner ────────────────────────────────────────────────────────────────
def run_demo():
    print("\n" + "═" * 60)
    print("  AFTER-HOURS LEAD CAPTURE BOT — DEMO")
    print(f"  Business: {B['name']}")
    print(f"  Type: {B['type'].title()}")
    print("═" * 60)
    print("  Simulating a customer texting after hours via WhatsApp.")
    print("  Type messages as a customer. Type 'quit' to exit.\n")

    bot = AfterHoursBot()

    # Trigger the opening greeting
    greeting = bot.send("hi")
    print(f"🤖  Bot: {greeting}\n")

    while True:
        try:
            user_input = input("👤  You: ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("\nDemo ended.")
            break

        reply = bot.send(user_input)
        print(f"\n🤖  Bot: {reply}\n")

        if bot.lead:
            print("✅  Lead successfully captured. Bot will now wrap up the conversation.\n")


if __name__ == "__main__":
    run_demo()
