# After-Hours Lead Capture Bot

An AI-powered WhatsApp bot that captures leads 24/7 when your business is closed.

## What It Does

- Greets customers instantly after hours
- Qualifies their service need
- Captures name, contact, and preferred appointment time
- Notifies the business owner immediately
- Handles emergencies with priority routing

## Setup

1. Install dependencies:

```
pip install -r requirements.txt
```

2. Set your Anthropic API key:

```
$env:ANTHROPIC_API_KEY="your-key-here"
```

3. Edit `business.json` with the client's real business info.

4. Run the demo:

```
python bot.py
```

5. Run tests:

```
python test_bot.py
```

## Deploying for a Client

- Host on a $5/month Hetzner or DigitalOcean VPS
- Connect to client's WhatsApp Business via Twilio or Meta Cloud API
- Replace the `_notify_owner()` method with a real WhatsApp/SMS send
- Update `business.json` with their info — done in under an hour

## Cost Per Client

- VPS: ~$5-10/month
- Claude API (haiku): ~$5-15/month at typical volume
- Your charge: $400-600/month
- Margin: ~$375-580/month per client

## Testing & Onboarding

Before onboarding your first paying customer, follow the testing guides:

- **Quick Start:** [`TESTING_WORKFLOW.md`](TESTING_WORKFLOW.md) — 6-phase testing workflow (60 minutes total)
- **Automated Tests:** `python test_e2e_flow.py` — Tests config storage, routing, lead capture, notifications
- **Testing Guide:** [`docs/e2e-testing-guide.md`](docs/e2e-testing-guide.md) — Detailed testing reference
- **Integration Testing:** [`docs/stripe-twilio-testing.md`](docs/stripe-twilio-testing.md) — Stripe & Twilio test setup
- **Testing Summary:** [`docs/testing-summary.md`](docs/testing-summary.md) — Overview of all testing resources

## Strategy Docs

- Summary: [`docs/saas-strategy-summary.md`](docs/saas-strategy-summary.md)
