"""
Twilio WhatsApp Webhook Server
Bridges incoming WhatsApp messages (via Twilio) to AfterHoursBot.

Environment variables required:
  ANTHROPIC_API_KEY       - Your Anthropic API key
  TWILIO_ACCOUNT_SID      - From console.twilio.com
  TWILIO_AUTH_TOKEN       - From console.twilio.com
  TWILIO_WHATSAPP_NUMBER  - e.g. whatsapp:+14155238886
  OWNER_WHATSAPP_NUMBER   - Owner's WhatsApp number, e.g. whatsapp:+17205779547

Optional:
  BUSINESS_CONFIG_PATH    - Path to a custom business.json (defaults to ./business.json)
  PORT                    - HTTP port to listen on (default: 5000)
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

# ── Twilio client (used for owner notifications) ───────────────────────────────
_twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID")
_twilio_token = os.environ.get("TWILIO_AUTH_TOKEN")
_twilio_number = os.environ.get("TWILIO_WHATSAPP_NUMBER", "")   # whatsapp:+1...
_owner_number = os.environ.get("OWNER_WHATSAPP_NUMBER", "")     # whatsapp:+1...

twilio_client: TwilioClient | None = None
if _twilio_sid and _twilio_token:
    twilio_client = TwilioClient(_twilio_sid, _twilio_token)
else:
    logger.warning("TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN not set — owner notifications disabled")

# ── Per-conversation bot instances ─────────────────────────────────────────────
# Key: customer WhatsApp number (e.g. "whatsapp:+13035551234")
# Each customer gets their own bot instance so conversation history is isolated.
_sessions: dict[str, AfterHoursBot] = {}

def _get_or_create_session(from_number: str) -> AfterHoursBot:
    if from_number not in _sessions:
        config_path = os.environ.get("BUSINESS_CONFIG_PATH")
        _sessions[from_number] = AfterHoursBot(
            config_path=config_path,
            notify_fn=_notify_owner,
        )
        logger.info("New session created for %s", from_number)
    return _sessions[from_number]

# ── Owner notification via WhatsApp ───────────────────────────────────────────
def _notify_owner(lead: dict, business: dict) -> None:
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

    if twilio_client and _owner_number and _twilio_number:
        try:
            twilio_client.messages.create(
                from_=_twilio_number,
                to=_owner_number,
                body=message_body,
            )
            logger.info("Owner notification sent to %s", _owner_number)
        except Exception as e:
            logger.error("Failed to send owner notification: %s", e)
    else:
        # Fallback: just log it
        print(message_body)

# ── Twilio signature validation ────────────────────────────────────────────────
def _validate_twilio_request() -> bool:
    """Return True if request came from Twilio (skip in dev if token missing)."""
    if not _twilio_token:
        return True   # Dev mode — skip validation
    validator = RequestValidator(_twilio_token)
    signature = request.headers.get("X-Twilio-Signature", "")
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
    body = request.form.get("Body", "").strip()

    logger.info("Incoming from %s: %r", from_number, body)

    if not body:
        # Empty message — Twilio sometimes sends media-only messages
        twiml = MessagingResponse()
        return str(twiml), 200, {"Content-Type": "text/xml"}

    bot = _get_or_create_session(from_number)
    reply = bot.send(body)

    logger.info("Reply to %s: %r", from_number, reply)

    twiml = MessagingResponse()
    twiml.message(reply)
    return str(twiml), 200, {"Content-Type": "text/xml"}

# ── Health check ──────────────────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok", "sessions": len(_sessions)}, 200

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info("Starting webhook server on port %d", port)
    app.run(host="0.0.0.0", port=port, debug=False)

