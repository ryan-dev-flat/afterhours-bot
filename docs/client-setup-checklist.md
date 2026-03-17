# Client Setup Checklist

Use this checklist when setting up a new client's bot. Print it out or use it as a reference.

## Pre-Setup (Before Customer Signs Up)

- [ ] Automated tests pass: `python test_e2e_flow.py`
- [ ] Local database is set up
- [ ] Stripe test keys are configured
- [ ] Twilio sandbox is set up
- [ ] You can send/receive test messages

## Customer Signup

- [ ] Customer completes signup form
- [ ] You receive email alert
- [ ] Customer completes payment
- [ ] You receive payment confirmation
- [ ] Account is created in database

## Onboarding Form

- [ ] Customer completes onboarding form with:
  - [ ] Business name
  - [ ] Owner name
  - [ ] Services offered
  - [ ] Business hours
  - [ ] Service area
  - [ ] Emergency line
  - [ ] Emergency keywords
  - [ ] Owner notification phone number

## Database Setup

- [ ] Create account record in database
- [ ] Store business profile/config
- [ ] Assign Twilio sender number
- [ ] Create channel record
- [ ] Verify data is stored correctly

## Bot Testing

### Test 1: Bot Responds with Client Info
- [ ] Send: "hi"
- [ ] Verify bot mentions client's business name
- [ ] Verify bot mentions client's services
- [ ] Verify bot mentions client's hours

### Test 2: Lead Capture
- [ ] Send: "i need [service]"
- [ ] Send: "tomorrow at [time]"
- [ ] Send: "my name is [name], [phone]"
- [ ] Verify lead is captured
- [ ] Verify lead is attributed to correct client
- [ ] Verify lead data is in database

### Test 3: Owner Notification
- [ ] Verify you receive notification
- [ ] Verify notification goes to correct phone
- [ ] Verify notification includes:
  - [ ] Business name
  - [ ] Customer name
  - [ ] Service needed
  - [ ] Preferred callback time
  - [ ] Phone number (if provided)

### Test 4: Emergency Handling
- [ ] Send: "[emergency keyword]"
- [ ] Verify bot responds with emergency line
- [ ] Verify it's client's emergency line, not generic
- [ ] Verify bot still offers to log info

### Test 5: Multiple Messages
- [ ] Send 5+ messages in conversation
- [ ] Verify bot maintains context
- [ ] Verify conversation history is isolated
- [ ] Verify bot doesn't repeat itself

## Activation

- [ ] All tests pass
- [ ] Mark account as "active" in database
- [ ] Send customer activation email with:
  - [ ] Their WhatsApp number
  - [ ] Instructions to share with customers
  - [ ] Example conversation
  - [ ] Support contact info
  - [ ] Link to dashboard (if available)

## Post-Activation

- [ ] Monitor first 24 hours for issues
- [ ] Check that leads are being captured
- [ ] Verify owner notifications are working
- [ ] Follow up with customer if any issues

## Troubleshooting

### Bot doesn't mention client's business
- [ ] Check config is stored in database
- [ ] Check routing is using correct account_id
- [ ] Check bot is loading correct config
- [ ] Run `test_bot.py` to verify bot logic

### Messages route to wrong client
- [ ] Check account_id/routing key is correct
- [ ] Check database lookup is working
- [ ] Check Twilio number mapping

### Leads don't get captured
- [ ] Check bot is responding correctly
- [ ] Check lead capture logic in bot
- [ ] Check database storage is working
- [ ] Run `test_bot.py` to verify bot

### Notifications go to wrong number
- [ ] Check `owner_notify_number` in database
- [ ] Check Twilio credentials are correct
- [ ] Check notification function is using correct field
- [ ] Check Twilio logs for errors

### Multiple clients interfere
- [ ] Check each client has separate bot instance
- [ ] Check conversation history is isolated
- [ ] Check leads are attributed correctly
- [ ] Check database queries are filtered by account_id

## Sign-Off

- [ ] All tests pass
- [ ] Customer is notified
- [ ] Bot is live
- [ ] You're monitoring for issues

---

## Quick Reference

### Test Commands
```bash
# Run automated tests
python test_e2e_flow.py

# Run bot logic tests
python test_bot.py

# Start webhook server
python webhook.py
```

### Test Data
- Test Stripe card: `4242 4242 4242 4242`
- Test Twilio number: Get from sandbox
- Test message: "hi"

### Key Files
- Bot logic: `bot.py`
- Webhook: `webhook.py`
- Tests: `test_e2e_flow.py`, `test_bot.py`
- Config: `business.json`

### Environment Variables
```
ANTHROPIC_API_KEY=sk-ant-...
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_NUMBER=whatsapp:+1...
OWNER_WHATSAPP_NUMBER=whatsapp:+1...
```

