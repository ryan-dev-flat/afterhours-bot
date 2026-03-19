"""
Twilio WhatsApp Webhook Server
Bridges incoming WhatsApp messages (via Twilio) to AfterHoursBot.

Multi-tenant mode (DATABASE_URL set):
  Routes messages by the Twilio number they were sent TO.
  Each tenant's config is loaded from the database.

Single-tenant fallback (no DATABASE_URL):
  Uses environment variables and business.json like before.

Environment variables required:
  ANTHROPIC_API_KEY       - Your Anthropic API key
  TWILIO_ACCOUNT_SID      - From console.twilio.com
  TWILIO_AUTH_TOKEN        - From console.twilio.com

Single-tenant only:
  TWILIO_WHATSAPP_NUMBER  - e.g. whatsapp:+14155238886
  OWNER_WHATSAPP_NUMBER   - Owner's WhatsApp number
  BUSINESS_CONFIG_PATH    - Path to a custom business.json (defaults to ./business.json)

Optional:
  DATABASE_URL            - Postgres connection string (enables multi-tenant mode)
  PORT                    - HTTP port to listen on (default: 5000)

Stripe (optional — enables /start, /checkout, /stripe-webhook, /onboard):
  STRIPE_SECRET_KEY       - From Stripe dashboard
  STRIPE_WEBHOOK_SECRET   - From Stripe webhook endpoint settings
  STRIPE_PRICE_ID         - Price ID for the $149/month plan
  APP_BASE_URL            - Public URL of this app
  FOUNDER_WHATSAPP_NUMBER - Your WhatsApp number for new-client alerts
"""

import logging
import os
from datetime import datetime
from flask import Flask, request, abort
from twilio.twiml.messaging_response import MessagingResponse
from twilio.request_validator import RequestValidator
from twilio.rest import Client as TwilioClient
from bot import AfterHoursBot

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── App setup ─────────────────────────────────────────────────────────────────
app = Flask(__name__)

# ── Stripe Blueprint (registers /start, /checkout, /stripe-webhook, /onboard) ─
if os.environ.get("STRIPE_SECRET_KEY"):
    from stripe_routes import stripe_bp
    app.register_blueprint(stripe_bp)
    logger.info("Stripe routes registered")

# ── Admin Blueprint (registers /admin/*) ──────────────────────────────────────
if os.environ.get("ADMIN_SECRET"):
    from admin_routes import admin_bp
    app.register_blueprint(admin_bp)
    logger.info("Admin routes registered")

# ── Multi-tenant mode detection ───────────────────────────────────────────────
_multi_tenant = bool(os.environ.get("DATABASE_URL"))
if _multi_tenant:
    import db as tenant_db
    logger.info("Multi-tenant mode enabled (DATABASE_URL is set)")
else:
    logger.info("Single-tenant mode (no DATABASE_URL)")

# ── Twilio client (used for owner notifications) ───────────────────────────────
_twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID")
_twilio_token = os.environ.get("TWILIO_AUTH_TOKEN")
_twilio_number = os.environ.get("TWILIO_WHATSAPP_NUMBER", "")   # single-tenant only
_owner_number = os.environ.get("OWNER_WHATSAPP_NUMBER", "")     # single-tenant only

twilio_client: TwilioClient | None = None
if _twilio_sid and _twilio_token:
    twilio_client = TwilioClient(_twilio_sid, _twilio_token)
else:
    logger.warning("TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN not set — owner notifications disabled")

# ── Per-conversation bot instances ─────────────────────────────────────────────
# Multi-tenant key: (account_id, from_number)
# Single-tenant key: from_number
_sessions: dict[str, AfterHoursBot] = {}


def _get_or_create_session_single(from_number: str) -> AfterHoursBot:
    """Single-tenant: one business.json, one owner."""
    if from_number not in _sessions:
        config_path = os.environ.get("BUSINESS_CONFIG_PATH")
        _sessions[from_number] = AfterHoursBot(
            config_path=config_path,
            notify_fn=_make_notify_fn(
                owner_phone=_owner_number,
                from_number=_twilio_number,
            ),
        )
        logger.info("New single-tenant session for %s", from_number)
    return _sessions[from_number]


def _get_or_create_session_multi(
    from_number: str, account_id: str, config: dict, account: dict
) -> AfterHoursBot:
    """Multi-tenant: config from DB, owner phone from account record."""
    session_key = f"{account_id}:{from_number}"
    if session_key not in _sessions:
        owner_phone = account.get("owner_phone", "")
        if owner_phone and not owner_phone.startswith("whatsapp:"):
            owner_phone = f"whatsapp:{owner_phone}"

        # In multi-tenant mode, the Twilio number that received the message
        # is the one we send notifications FROM for this tenant.
        channel_number = account.get("_channel_number", _twilio_number)

        _sessions[session_key] = AfterHoursBot(
            config=config,
            notify_fn=_make_notify_fn(
                owner_phone=owner_phone,
                from_number=channel_number,
                account_id=account_id,
                customer_phone=from_number,
            ),
        )
        logger.info("New multi-tenant session for %s (account %s)", from_number, account_id)
    return _sessions[session_key]


# ── Owner notification via WhatsApp ───────────────────────────────────────────
def _make_notify_fn(
    owner_phone: str,
    from_number: str,
    account_id: str | None = None,
    customer_phone: str | None = None,
):
    """Return a closure that notifies the correct owner and stores the lead."""

    def _notify(lead: dict, business: dict) -> None:
        timestamp = datetime.now().strftime("%I:%M %p")
        lines = [
            f"📬 *New lead — {business['name']}* ({timestamp})",
            f"• Name: {lead.get('name', 'unknown')}",
            f"• Service: {lead.get('service', 'unknown')}",
            f"• Time: {lead.get('time', 'unknown')}",
        ]
        if lead.get("phone"):
            lines.append(f"• Phone: {lead['phone']}")
        message_body = "\n".join(lines)

        logger.info("Lead captured: %s", lead)

        # ── Store lead in DB (multi-tenant only) ──────────────────────────
        if account_id and _multi_tenant:
            try:
                tenant_db.store_lead(account_id, lead, customer_phone)
                logger.info("Lead stored in DB for account %s", account_id)
            except Exception as e:
                logger.error("Failed to store lead in DB: %s", e)

        # ── Send WhatsApp notification to owner ───────────────────────────
        if twilio_client and owner_phone and from_number:
            try:
                twilio_client.messages.create(
                    from_=from_number,
                    to=owner_phone,
                    body=message_body,
                )
                logger.info("Owner notification sent to %s", owner_phone)
            except Exception as e:
                logger.error("Failed to send owner notification: %s", e)
        else:
            # Fallback: just log it
            print(message_body)

    return _notify

# ── Twilio signature validation ────────────────────────────────────────────────
def _validate_twilio_request() -> bool:
    """Return True if request came from Twilio (skip in dev if token missing)."""
    if not _twilio_token:
        return True   # Dev mode — skip validation
    validator = RequestValidator(_twilio_token)
    signature = request.headers.get("X-Twilio-Signature", "")

    # Railway (and most PaaS) terminate TLS at the load balancer, so
    # request.url is http:// even though Twilio signed an https:// URL.
    # Reconstruct the public HTTPS URL from forwarded headers.
    forwarded_proto = request.headers.get("X-Forwarded-Proto", "")
    if forwarded_proto == "https":
        url = request.url.replace("http://", "https://", 1)
    else:
        url = request.url

    params = request.form.to_dict()
    return validator.validate(url, params, signature)

# ── Webhook endpoint ───────────────────────────────────────────────────────────
@app.route("/webhook", methods=["POST"])
def webhook():
    if not _validate_twilio_request():
        logger.warning("Invalid Twilio signature — rejecting request")
        abort(403)

    from_number = request.form.get("From", "")
    to_number = request.form.get("To", "")
    body = request.form.get("Body", "").strip()

    logger.info("Incoming from %s to %s: %r", from_number, to_number, body)

    if not body:
        twiml = MessagingResponse()
        return str(twiml), 200, {"Content-Type": "text/xml"}

    # ── Route to the correct tenant ───────────────────────────────────────
    if _multi_tenant and to_number:
        account = tenant_db.get_account_by_twilio_number(to_number)
        if not account:
            logger.warning("No active account for Twilio number %s", to_number)
            twiml = MessagingResponse()
            twiml.message(
                "Sorry, this number is not currently active. "
                "Please contact support."
            )
            return str(twiml), 200, {"Content-Type": "text/xml"}

        account_id = str(account["id"])
        config = tenant_db.get_business_profile(account_id)
        if not config:
            logger.error("Account %s has no business profile", account_id)
            twiml = MessagingResponse()
            twiml.message(
                "Sorry, this service is being set up. Please try again later."
            )
            return str(twiml), 200, {"Content-Type": "text/xml"}

        # Attach the channel number so the notify closure can use it
        account["_channel_number"] = to_number
        bot = _get_or_create_session_multi(from_number, account_id, config, account)
    else:
        # Single-tenant fallback
        bot = _get_or_create_session_single(from_number)

    reply = bot.send(body)

    logger.info("Reply to %s: %r", from_number, reply)

    twiml = MessagingResponse()
    twiml.message(reply)
    return str(twiml), 200, {"Content-Type": "text/xml"}

# ── Health check ──────────────────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return {
        "status": "ok",
        "mode": "multi-tenant" if _multi_tenant else "single-tenant",
        "sessions": len(_sessions),
    }, 200

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info("Starting webhook server on port %d", port)
    app.run(host="0.0.0.0", port=port, debug=False)

