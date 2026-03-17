"""
Stripe Checkout and webhook routes.

Environment variables required:
  STRIPE_SECRET_KEY       - From Stripe dashboard (sk_live_... or sk_test_...)
  STRIPE_WEBHOOK_SECRET   - From Stripe webhook endpoint settings (whsec_...)
  STRIPE_PRICE_ID         - Price ID for the $149/month plan (price_...)
  APP_BASE_URL            - Public URL of this app (e.g. https://afterhours-bot-production-f37a.up.railway.app)

Optional (for founder notifications):
  FOUNDER_WHATSAPP_NUMBER - Your personal WhatsApp number (whatsapp:+1...)
"""

import logging
import os

import stripe
from flask import Blueprint, jsonify, redirect, request

logger = logging.getLogger(__name__)

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
_webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
_price_id = os.environ.get("STRIPE_PRICE_ID")
_base_url = os.environ.get("APP_BASE_URL", "http://localhost:5000")

stripe_bp = Blueprint("stripe", __name__)


# ── GET /start — simple sign-up form ─────────────────────────────────────────
@stripe_bp.route("/start", methods=["GET"])
def start():
    return """
    <!DOCTYPE html>
    <html>
    <head>
      <title>Get Started — AfterHours Bot</title>
      <style>
        body { font-family: sans-serif; max-width: 480px; margin: 80px auto; padding: 0 20px; }
        h1 { font-size: 1.6rem; margin-bottom: 8px; }
        p  { color: #555; margin-bottom: 28px; }
        label { display: block; font-size: .9rem; font-weight: 600; margin-bottom: 4px; }
        input { width: 100%; padding: 10px; font-size: 1rem; border: 1px solid #ccc;
                border-radius: 6px; margin-bottom: 16px; box-sizing: border-box; }
        button { width: 100%; padding: 14px; background: #635bff; color: #fff;
                 font-size: 1.1rem; font-weight: 700; border: none; border-radius: 8px; cursor: pointer; }
        button:hover { background: #4f46e5; }
      </style>
    </head>
    <body>
      <h1>Set up your After-Hours Bot</h1>
      <p>$199 setup &nbsp;+&nbsp; $149/month. Cancel anytime.</p>
      <form action="/checkout" method="POST">
        <label>Your name</label>
        <input name="owner_name" placeholder="Jane Smith" required>
        <label>Business name</label>
        <input name="company_name" placeholder="Smith Plumbing LLC" required>
        <label>Email address</label>
        <input name="email" type="email" placeholder="jane@smithplumbing.com" required>
        <button type="submit">Continue to payment →</button>
      </form>
    </body>
    </html>
    """, 200


# ── POST /checkout — create Stripe Checkout Session ──────────────────────────
@stripe_bp.route("/checkout", methods=["POST"])
def checkout():
    if not stripe.api_key or not _price_id:
        return jsonify({"error": "Stripe is not configured"}), 500

    owner_name   = request.form.get("owner_name", "").strip()
    company_name = request.form.get("company_name", "").strip()
    email        = request.form.get("email", "").strip()

    if not all([owner_name, company_name, email]):
        return jsonify({"error": "All fields are required"}), 400

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="subscription",
        customer_email=email,
        line_items=[{"price": _price_id, "quantity": 1}],
        metadata={
            "owner_name":   owner_name,
            "company_name": company_name,
        },
        success_url=f"{_base_url}/onboard?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{_base_url}/start",
    )
    return redirect(session.url, code=303)


# ── POST /stripe-webhook — handle Stripe events ───────────────────────────────
@stripe_bp.route("/stripe-webhook", methods=["POST"])
def stripe_webhook():
    payload   = request.get_data()
    sig_header = request.headers.get("Stripe-Signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, _webhook_secret)
    except stripe.error.SignatureVerificationError:
        logger.warning("Invalid Stripe signature")
        return jsonify({"error": "Invalid signature"}), 400

    if event["type"] == "checkout.session.completed":
        _handle_new_subscription(event["data"]["object"])

    return jsonify({"received": True}), 200


def _handle_new_subscription(session: dict) -> None:
    """Create DB account and notify founder when payment succeeds."""
    meta         = session.get("metadata", {})
    owner_name   = meta.get("owner_name", "Unknown")
    company_name = meta.get("company_name", "Unknown Business")
    email        = session.get("customer_email", "")
    stripe_cid   = session.get("customer", "")

    logger.info("New subscription: %s (%s)", company_name, email)

    # Auto-create account in DB
    try:
        import db
        account_id = db.create_account(
            company_name=company_name,
            owner_name=owner_name,
            owner_email=email,
            stripe_customer_id=stripe_cid,
        )
        db.update_account_status(account_id, "onboarding")
        logger.info("Account created: %s → %s", company_name, account_id)
    except Exception as e:
        logger.error("Failed to create account in DB: %s", e)
        return

    # Notify founder via WhatsApp
    _notify_founder(company_name, owner_name, email, account_id)


def _notify_founder(company_name, owner_name, email, account_id):
    """Send yourself a WhatsApp when a new client pays."""
    founder_number = os.environ.get("FOUNDER_WHATSAPP_NUMBER")
    twilio_number  = os.environ.get("TWILIO_WHATSAPP_NUMBER")
    twilio_sid     = os.environ.get("TWILIO_ACCOUNT_SID")
    twilio_token   = os.environ.get("TWILIO_AUTH_TOKEN")

    msg = (
        f"💰 *New AfterHours Bot client!*\n"
        f"• Business: {company_name}\n"
        f"• Owner: {owner_name}\n"
        f"• Email: {email}\n"
        f"• Account ID: {account_id}\n\n"
        f"⚡ Action needed: assign a Twilio number and activate their channel."
    )

    if all([twilio_sid, twilio_token, founder_number, twilio_number]):
        from twilio.rest import Client as TwilioClient
        try:
            TwilioClient(twilio_sid, twilio_token).messages.create(
                from_=twilio_number,
                to=founder_number,
                body=msg,
            )
            logger.info("Founder notified via WhatsApp")
        except Exception as e:
            logger.error("Failed to notify founder: %s", e)
    else:
        # Fallback: log it so it at least shows in Railway logs
        logger.info("FOUNDER ALERT (WhatsApp not configured):\n%s", msg)


# ── GET /onboard — post-payment business details form ─────────────────────────
@stripe_bp.route("/onboard", methods=["GET"])
def onboard_form():
    session_id = request.args.get("session_id", "")
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <title>Set Up Your Bot — AfterHours</title>
      <style>
        body {{ font-family: sans-serif; max-width: 560px; margin: 60px auto; padding: 0 20px; }}
        h1 {{ font-size: 1.5rem; margin-bottom: 6px; }}
        p  {{ color: #555; margin-bottom: 24px; }}
        label {{ display: block; font-size: .85rem; font-weight: 600; margin-bottom: 4px; margin-top: 14px; }}
        input, textarea, select {{ width: 100%; padding: 10px; font-size: 1rem;
                border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; }}
        textarea {{ height: 80px; resize: vertical; }}
        button {{ margin-top: 24px; width: 100%; padding: 14px; background: #16a34a; color: #fff;
                  font-size: 1.1rem; font-weight: 700; border: none; border-radius: 8px; cursor: pointer; }}
        button:hover {{ background: #15803d; }}
        .note {{ font-size: .8rem; color: #888; margin-top: 6px; }}
      </style>
    </head>
    <body>
      <h1>🎉 Payment confirmed! Let's set up your bot.</h1>
      <p>Fill in the details below. We'll use these to configure your AI receptionist.</p>
      <form action="/onboard" method="POST">
        <input type="hidden" name="session_id" value="{session_id}">

        <label>Business name</label>
        <input name="business_name" placeholder="Summit Home Services" required>

        <label>Business type / services offered</label>
        <input name="business_type" placeholder="Plumbing and HVAC" required>

        <label>City / service area</label>
        <input name="location" placeholder="Denver, CO" required>

        <label>Your name (owner)</label>
        <input name="owner_name" placeholder="Mike" required>

        <label>Your WhatsApp number (for lead alerts)</label>
        <input name="owner_phone" type="tel" placeholder="+17205550000" required>

        <label>Business hours</label>
        <input name="hours" placeholder="Mon-Fri 8am-5pm, Sat 9am-2pm" required>

        <label>Services you offer (one per line)</label>
        <textarea name="services" placeholder="Plumbing repairs&#10;Drain cleaning&#10;Water heater installation"></textarea>

        <label>Emergency line (optional)</label>
        <input name="emergency_line" placeholder="(720) 555-0123">

        <label>Emergency keywords (comma-separated, optional)</label>
        <input name="emergency_keywords" placeholder="flood, gas leak, burst pipe, no heat">

        <p class="note">We'll review your details and text you within 24 hours once your WhatsApp number is active.</p>
        <button type="submit">Submit →</button>
      </form>
    </body>
    </html>
    """, 200


# ── POST /onboard — save business profile to DB ───────────────────────────────
@stripe_bp.route("/onboard", methods=["POST"])
def onboard_submit():
    business_name = request.form.get("business_name", "").strip()
    owner_phone  = request.form.get("owner_phone", "").strip()

    # Build config dict matching business.json structure
    services_raw = request.form.get("services", "")
    services = [s.strip() for s in services_raw.splitlines() if s.strip()]

    keywords_raw = request.form.get("emergency_keywords", "")
    emergency_keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]

    config = {
        "name":               business_name,
        "type":               request.form.get("business_type", "").strip(),
        "location":           request.form.get("location", "").strip(),
        "owner_name":         request.form.get("owner_name", "").strip(),
        "owner_notify_number": owner_phone,
        "services":           services,
        "hours":              request.form.get("hours", "").strip(),
        "closed_days":        [],
        "service_area":       request.form.get("location", "").strip(),
        "emergency_line":     request.form.get("emergency_line", "").strip(),
        "booking_lead_time":  "Same day or next day for most requests",
        "free_estimate":      True,
        "emergency_keywords": emergency_keywords,
    }

    # Look up account by Stripe session — match on company name (best we have without DB session storage)
    try:
        import db
        # Find the newest onboarding account with this business name
        account_id = db.get_account_id_by_company(business_name)
        if account_id:
            db.set_business_profile(account_id, config)
            # Update owner phone on account record too
            db.update_account_owner_phone(account_id, owner_phone)
            logger.info("Onboarding profile saved for account %s", account_id)
    except Exception as e:
        logger.error("Failed to save onboarding profile: %s", e)

    return """
    <!DOCTYPE html>
    <html>
    <head>
      <title>All done! — AfterHours Bot</title>
      <style>
        body { font-family: sans-serif; max-width: 480px; margin: 100px auto; text-align: center; padding: 0 20px; }
        h1 { font-size: 2rem; }
        p  { color: #555; font-size: 1.1rem; line-height: 1.6; }
      </style>
    </head>
    <body>
      <h1>✅ You're all set!</h1>
      <p>We received your business details and will have your AI receptionist live within 24 hours.</p>
      <p>We'll send you a WhatsApp message once your number is active.</p>
      <p style="margin-top:40px; color:#999; font-size:.9rem;">Questions? Reply to any of our messages.</p>
    </body>
    </html>
    """, 200

