"""
End-to-end testing utilities for multi-tenant bot setup.
Tests the full client onboarding flow without external dependencies.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

# Try to import bot, but allow tests to run without it for demo purposes
try:
    from bot import AfterHoursBot
except ImportError:
    # Mock bot for testing without dependencies
    class AfterHoursBot:
        def __init__(self, config_path=None):
            self.business = {}
            self.history = []
            self.lead = None

        def send(self, message: str) -> str:
            self.history.append({"role": "user", "content": message})
            # Simple mock response
            response = f"Thanks for reaching out to {self.business.get('name', 'our business')}. How can I help?"
            self.history.append({"role": "assistant", "content": response})
            return response


# ── Test Data Fixtures ─────────────────────────────────────────────────────────
class TestClientFixture:
    """Represents a test client with business config."""

    def __init__(self, name: str, owner_name: str, owner_phone: str):
        self.account_id = str(uuid.uuid4())[:8]
        self.business_config = {
            "name": name,
            "type": "test service business",
            "location": "Test City, TS",
            "owner_name": owner_name,
            "owner_notify_number": owner_phone,
            "services": ["service1", "service2", "service3"],
            "hours": "Monday-Friday 8am-5pm",
            "closed_days": ["Sunday"],
            "service_area": "Test metro area",
            "emergency_line": "(555) 123-4567",
            "booking_lead_time": "Same day or next day",
            "free_estimate": True,
            "emergency_keywords": ["flood", "gas leak", "emergency"],
        }

    def to_dict(self) -> Dict[str, Any]:
        """Return business config as dict."""
        return self.business_config


# ── Simulated Database ─────────────────────────────────────────────────────────
class TestDatabase:
    """In-memory database for testing."""

    def __init__(self):
        self.accounts = {}
        self.business_profiles = {}
        self.channels = {}
        self.leads = {}

    def create_account(self, account_id: str, company_name: str, owner_name: str):
        """Create a test account."""
        self.accounts[account_id] = {
            "id": account_id,
            "company_name": company_name,
            "owner_name": owner_name,
            "status": "active",
            "created_at": datetime.now().isoformat(),
        }

    def store_business_profile(self, account_id: str, config: Dict[str, Any]):
        """Store business config for a client."""
        self.business_profiles[account_id] = config

    def store_channel(self, account_id: str, twilio_number: str):
        """Store Twilio channel for a client."""
        self.channels[account_id] = {
            "account_id": account_id,
            "twilio_number": twilio_number,
            "status": "active",
        }

    def get_business_profile(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve business config for a client."""
        return self.business_profiles.get(account_id)

    def store_lead(self, account_id: str, lead: Dict[str, Any]):
        """Store a captured lead."""
        if account_id not in self.leads:
            self.leads[account_id] = []
        self.leads[account_id].append(lead)

    def get_leads(self, account_id: str) -> list:
        """Get all leads for a client."""
        return self.leads.get(account_id, [])


# ── Multi-Tenant Bot Router ────────────────────────────────────────────────────
class MultiTenantBotRouter:
    """Routes messages to the correct client's bot."""

    def __init__(self, db: TestDatabase):
        self.db = db
        self.bot_instances = {}

    def get_or_create_bot(self, account_id: str) -> Optional[AfterHoursBot]:
        """Get or create a bot instance for a client."""
        if account_id not in self.bot_instances:
            config = self.db.get_business_profile(account_id)
            if not config:
                return None
            # Create a temporary config file for the bot
            self.bot_instances[account_id] = {
                "config": config,
                "bot": None,  # Will be created on first message
            }
        return self.bot_instances[account_id]

    def send_message(self, account_id: str, message: str) -> Optional[str]:
        """Send a message to a client's bot."""
        bot_data = self.get_or_create_bot(account_id)
        if not bot_data:
            return None

        # Create bot instance if needed
        if bot_data["bot"] is None:
            # For testing, we'll create a bot with the config
            # In production, this would load from a file or env var
            bot_data["bot"] = AfterHoursBot()
            # Override the business config
            bot_data["bot"].business = bot_data["config"]
            bot_data["bot"].system_prompt = self._build_system_prompt(bot_data["config"])

        bot = bot_data["bot"]
        reply = bot.send(message)

        # Store lead if captured
        if bot.lead:
            self.db.store_lead(account_id, bot.lead)

        return reply

    @staticmethod
    def _build_system_prompt(config: Dict[str, Any]) -> str:
        """Build system prompt from config."""
        from bot import build_system_prompt
        return build_system_prompt(config)


# ── Test Notifications ─────────────────────────────────────────────────────────
class TestNotificationCapture:
    """Captures notifications for testing."""

    def __init__(self):
        self.notifications = []

    def capture_notification(self, account_id: str, lead: Dict[str, Any], business: Dict[str, Any]):
        """Capture a notification."""
        self.notifications.append({
            "account_id": account_id,
            "lead": lead,
            "business": business,
            "timestamp": datetime.now().isoformat(),
        })

    def get_notifications_for_account(self, account_id: str) -> list:
        """Get all notifications for an account."""
        return [n for n in self.notifications if n["account_id"] == account_id]

