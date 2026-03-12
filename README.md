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

## Strategy Docs

- Summary: [`docs/saas-strategy-summary.md`](docs/saas-strategy-summary.md)
