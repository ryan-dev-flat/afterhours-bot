# Client After-Hours Bot Setup Workflow

Use this checklist to go from first client call to production in a repeatable way.

## 1) Discovery Call (30 minutes)

Collect the minimum data needed before touching code:

- Business name, timezone, and service area
- Business hours and after-hours definition
- Top 3–5 service categories customers ask about
- Emergency criteria (what counts as urgent)
- Preferred owner notification channel (SMS, WhatsApp, email)
- Intake fields required for follow-up (name, phone, issue, preferred time)

**Deliverable:** a completed intake form in your project tracker.

---

## 2) Provision Core Accounts (15–30 minutes)

Set up or confirm these are available:

- Anthropic API key
- WhatsApp provider account (Twilio or Meta Cloud API)
- Hosting target (Render, Railway, DigitalOcean, or Hetzner)
- Optional: Sentry/logging account for error tracking

**Deliverable:** credentials stored in a password manager and environment variable map.

---

## 3) Clone and Configure Bot Template (20 minutes)

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Configure environment variables:

```bash
export ANTHROPIC_API_KEY="<client-or-platform-key>"
```

3. Update `business.json` with:
   - business name
   - hours and timezone
   - service offerings
   - emergency keywords/rules
   - owner contact destination

4. Replace `_notify_owner()` integration with your real channel (Twilio SMS, Slack webhook, etc.).

**Deliverable:** local bot responds with correct business context.

---

## 4) Build a Conversation QA Script (20 minutes)

Test these scenarios before deployment:

- Normal after-hours inquiry (captures all lead fields)
- Emergency request (triggers urgent routing)
- Missing information (bot asks follow-up question)
- Off-topic message (bot politely redirects)
- Appointment preference captured with clear next step

Run:

```bash
python test_bot.py
```

Add 3–5 client-specific test messages and expected outcomes.

**Deliverable:** QA checklist marked pass/fail with notes.

---

## 5) Deploy and Wire Webhook (20–40 minutes)

1. Deploy app from repo using `Procfile` startup.
2. Set production env vars in host platform.
3. Configure WhatsApp webhook URL to point to deployed endpoint.
4. Send live test messages from a non-owner phone.

Health checks:

- App boots without errors
- Incoming message is processed
- Owner notification is sent
- No sensitive data appears in logs

**Deliverable:** production URL + successful test transcript.

---

## 6) Client Acceptance (15 minutes)

Walk the client through:

- sample conversation flow
- where leads are delivered
- emergency handling behavior
- expected response limitations

Collect sign-off in writing (email is enough).

**Deliverable:** acceptance confirmation.

---

## 7) Weekly Operations Playbook

Use this recurring routine to keep clients happy:

- Review missed leads and false emergency triggers
- Improve prompt/business rules from real transcripts
- Confirm notifications are delivered reliably
- Send a simple weekly metrics report:
  - messages handled
  - qualified leads captured
  - emergency escalations

**Deliverable:** 10-minute weekly report template per client.

---

## Suggested Folder and File Conventions

For multiple clients, create one config file per client:

- `clients/<client_slug>/business.json`
- `clients/<client_slug>/runbook.md`
- `clients/<client_slug>/qa-notes.md`

Keep your core bot logic shared, and isolate client-specific data/config.

## Recommended Go-Live Checklist

- [ ] Credentials secured and documented
- [ ] Business profile configured correctly
- [ ] Emergency rules tested
- [ ] Owner notification tested
- [ ] Webhook connected
- [ ] Production smoke test passed
- [ ] Client sign-off received
