# End-to-End Testing Guide for Client Onboarding

This guide walks you through testing the complete multi-tenant bot setup flow before onboarding your first paying customer.

## Quick Start

### Run the automated test suite
```bash
python test_e2e_flow.py
```

This tests:
- ✅ Client signup and config storage
- ✅ Message routing to correct client
- ✅ Lead capture and attribution
- ✅ Owner notification routing
- ✅ Multi-client isolation

## Testing Levels

### Level 1: Automated Unit Tests (5 minutes)
Run the test suite above. This validates the core logic without external dependencies.

**What it tests:**
- Database operations
- Multi-tenant routing
- Lead capture
- Notification capture

**What it doesn't test:**
- Stripe integration
- Twilio integration
- Real email/SMS

### Level 2: Local Integration Tests (15 minutes)
Test with a real local database and mock Stripe/Twilio.

**Steps:**
1. Set up a local Postgres database
2. Create the schema (accounts, business_profiles, channels, leads)
3. Run the test suite with real DB
4. Verify data persists correctly

### Level 3: Staging Environment (30 minutes)
Deploy to a staging environment with real Stripe test mode and Twilio sandbox.

**Steps:**
1. Deploy to Railway staging
2. Use Stripe test API keys
3. Use Twilio sandbox credentials
4. Test the full signup → payment → onboarding flow
5. Send test WhatsApp messages
6. Verify notifications

### Level 4: Manual Testing with Real Twilio (ongoing)
Send actual WhatsApp messages to your Twilio sandbox number.

**Steps:**
1. Get your Twilio sandbox WhatsApp number
2. Add it to your phone
3. Send test messages
4. Verify bot responses
5. Check owner notifications

## Pre-Launch Testing Checklist

Before taking your first paying customer, verify:

### Database & Config
- [ ] Client config stores correctly in database
- [ ] Config retrieval works for each client
- [ ] Multiple clients don't interfere with each other
- [ ] Config updates persist

### Message Routing
- [ ] Messages route to correct client's bot
- [ ] Bot responds with client's business name
- [ ] Bot uses client's services list
- [ ] Bot uses client's emergency line
- [ ] Bot uses client's hours

### Lead Capture
- [ ] Leads are captured correctly
- [ ] Leads are attributed to correct client
- [ ] Lead data is stored in database
- [ ] Multiple leads per client work
- [ ] Lead fields are complete (name, service, time, phone)

### Notifications
- [ ] Owner gets notified when lead is captured
- [ ] Notification goes to correct phone number
- [ ] Notification includes all lead details
- [ ] Notification format is readable

### Edge Cases
- [ ] Empty messages don't crash
- [ ] Very long messages work
- [ ] Special characters work
- [ ] Multiple conversations per client work
- [ ] Conversation history is isolated per client

### Stripe Integration
- [ ] Test checkout works
- [ ] Webhook processes payment correctly
- [ ] Account is created after payment
- [ ] Subscription status is tracked
- [ ] Failed payment is handled

### Email Notifications
- [ ] Founder gets alert when customer signs up
- [ ] Founder gets alert when customer completes onboarding
- [ ] Customer gets welcome email
- [ ] Customer gets activation email
- [ ] Emails include correct business info

## Testing Scenarios

### Scenario 1: Single Client Full Flow
1. Create a test client account
2. Store their business config
3. Send a test message
4. Verify bot responds with their info
5. Complete a lead capture conversation
6. Verify lead is stored and attributed
7. Verify owner notification is sent

### Scenario 2: Multiple Clients Simultaneously
1. Create 3 test clients
2. Send messages to each
3. Verify each gets their own bot response
4. Verify leads don't cross-contaminate
5. Verify notifications go to correct owners

### Scenario 3: Client Config Update
1. Create a client
2. Send a message (verify response)
3. Update their config
4. Send another message
5. Verify new config is used

### Scenario 4: Emergency Handling
1. Create a client with emergency keywords
2. Send a message with emergency keyword
3. Verify bot responds with emergency line
4. Verify emergency line is client's, not generic

## Common Issues and Fixes

### Issue: Bot doesn't mention client's business name
**Fix:** Verify business config is loaded correctly. Check that `build_system_prompt()` is using the right config.

### Issue: Messages route to wrong client
**Fix:** Verify the routing key/account_id is correct. Check database lookup.

### Issue: Leads don't get captured
**Fix:** Run `test_bot.py` first to verify bot logic works. Then check multi-tenant routing.

### Issue: Notifications go to wrong number
**Fix:** Verify `owner_notify_number` is stored correctly in database. Check notification function uses correct field.

### Issue: Multiple clients interfere
**Fix:** Verify each client gets a separate bot instance. Check session/instance management.

## Next Steps

1. **Run Level 1 tests** (automated suite)
2. **Set up local database** and run Level 2 tests
3. **Deploy to staging** and run Level 3 tests
4. **Manual testing** with Twilio sandbox
5. **Onboard first paying customer**

## Support

If tests fail, check:
1. Are all dependencies installed? (`pip install -r requirements.txt`)
2. Is the Anthropic API key set? (`echo $ANTHROPIC_API_KEY`)
3. Are there any error messages in the test output?
4. Can you run `test_bot.py` successfully?

