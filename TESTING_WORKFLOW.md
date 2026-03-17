# Client Onboarding Testing Workflow

A practical step-by-step guide to test the entire client setup flow before your first paying customer.

## Phase 1: Automated Testing (5 minutes)

### Step 1: Run the automated test suite
```bash
python test_e2e_flow.py
```

**Expected output:**
```
█ MULTI-TENANT BOT E2E TEST SUITE
  TEST 1: Client Signup and Config Storage
  ✅ Account created: abc12345
  ✅ Business config stored: ABC Plumbing
  ✅ Owner notification number: +15551234567
  
  TEST 2: Message Routing to Correct Client
  ✅ Client 1 (abc12345): Hi! Thanks for reaching out to ABC Plumbing...
  ✅ Client 2 (xyz67890): Hi! Thanks for reaching out to XYZ Electric...
  
  TEST 3: Lead Capture and Attribution
  ✅ Lead captured: {"name": "sarah", "service": "drain cleaning", ...}
  
  TEST 4: Owner Notification Routing
  ✅ Notification captured for: ABC Plumbing
  ✅ Owner phone: +15551234567
  
  TEST 5: Multi-Client Isolation
  ✅ All 3 clients isolated correctly
  
  RESULTS: 5 passed, 0 failed
```

**If tests fail:**
- Check that `ANTHROPIC_API_KEY` is set
- Run `python test_bot.py` to verify bot logic works
- Check error messages in output

---

## Phase 2: Local Integration Testing (15 minutes)

### Step 2: Set up a local database
```bash
# Install Postgres locally or use Docker
docker run --name postgres -e POSTGRES_PASSWORD=password -p 5432:5432 -d postgres

# Create database
createdb afterhours_test
```

### Step 3: Create database schema
```sql
CREATE TABLE accounts (
  id VARCHAR(50) PRIMARY KEY,
  company_name VARCHAR(255),
  owner_name VARCHAR(255),
  status VARCHAR(50),
  created_at TIMESTAMP
);

CREATE TABLE business_profiles (
  account_id VARCHAR(50) PRIMARY KEY,
  config JSONB,
  FOREIGN KEY (account_id) REFERENCES accounts(id)
);

CREATE TABLE channels (
  account_id VARCHAR(50) PRIMARY KEY,
  twilio_number VARCHAR(50),
  status VARCHAR(50),
  FOREIGN KEY (account_id) REFERENCES accounts(id)
);

CREATE TABLE leads (
  id SERIAL PRIMARY KEY,
  account_id VARCHAR(50),
  lead_data JSONB,
  created_at TIMESTAMP,
  FOREIGN KEY (account_id) REFERENCES accounts(id)
);
```

### Step 4: Update test suite to use real database
Modify `test_e2e_flow.py` to use Postgres instead of in-memory database.

### Step 5: Run tests with real database
```bash
python test_e2e_flow.py
```

**Verify:**
- Data persists in database
- Queries work correctly
- Multiple clients are isolated

---

## Phase 3: Stripe Test Mode (10 minutes)

### Step 6: Set up Stripe test keys
1. Go to https://dashboard.stripe.com/test/apikeys
2. Copy test keys to `.env`
3. Create a test checkout page

### Step 7: Test checkout flow
1. Start your Flask app: `python webhook.py`
2. Go to your checkout page
3. Use test card: `4242 4242 4242 4242`
4. Verify:
   - [ ] Checkout succeeds
   - [ ] Webhook is received
   - [ ] Account is created in database
   - [ ] Founder gets email alert

### Step 8: Test failed payment
1. Use card: `4000 0000 0000 0002`
2. Verify:
   - [ ] Payment is declined
   - [ ] Error message is shown
   - [ ] No account is created

---

## Phase 4: Twilio Sandbox Testing (15 minutes)

### Step 9: Set up Twilio sandbox
1. Go to https://console.twilio.com/develop/sms/try-it-out
2. Get sandbox number
3. Add to `.env`: `TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886`

### Step 10: Join the sandbox
1. Send `join <code>` to the sandbox number
2. Wait for confirmation

### Step 11: Test message flow
1. Send: "hi"
2. Verify bot responds with your business name
3. Send: "i need help with my drain"
4. Verify bot asks for callback time
5. Send: "tomorrow at 9am"
6. Verify bot asks for name
7. Send: "it's john, 555-1234"
8. Verify:
   - [ ] Bot captures lead
   - [ ] You get owner notification
   - [ ] Notification includes all details

### Step 12: Test with multiple clients
1. Create 2 test clients in database
2. Assign each a different Twilio number (or use routing key)
3. Send messages to each
4. Verify:
   - [ ] Each gets their own bot response
   - [ ] Leads are attributed correctly
   - [ ] Notifications go to correct owners

---

## Phase 5: End-to-End Flow (20 minutes)

### Step 13: Simulate complete customer journey
1. **Signup:** Create account via form
2. **Payment:** Complete Stripe checkout
3. **Onboarding:** Fill out business profile form
4. **Provisioning:** Store config in database
5. **Testing:** Send test message
6. **Activation:** Mark account active
7. **Live:** Send real message and verify response

### Step 14: Verify all 6 requirements
- [ ] Config stored correctly in database
- [ ] Messages route to correct client
- [ ] Bot responds with client-specific info
- [ ] Leads are captured and attributed
- [ ] Owner notifications go to right number
- [ ] Multiple clients don't interfere

---

## Phase 6: Manual Testing (ongoing)

### Step 15: Real Twilio sandbox testing
1. Add sandbox number to your phone
2. Send actual WhatsApp messages
3. Verify responses in real-time
4. Check owner notifications on your phone

### Step 16: Test edge cases
- [ ] Very long messages
- [ ] Special characters
- [ ] Multiple conversations
- [ ] Rapid messages
- [ ] Empty messages

---

## Checklist Before First Customer

- [ ] Automated tests pass
- [ ] Local database tests pass
- [ ] Stripe test checkout works
- [ ] Twilio sandbox messages work
- [ ] Multiple clients isolated
- [ ] Owner notifications work
- [ ] Lead capture works
- [ ] Config updates work
- [ ] Edge cases handled

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Tests fail | Check `ANTHROPIC_API_KEY` is set |
| Bot doesn't respond | Run `test_bot.py` to verify bot logic |
| Messages don't route | Check database lookup and routing key |
| Notifications don't send | Verify `OWNER_WHATSAPP_NUMBER` is set |
| Stripe webhook fails | Check webhook secret and URL |
| Twilio messages fail | Verify you've joined sandbox |

---

## Next Steps

1. ✅ Run Phase 1 (automated tests)
2. ✅ Run Phase 2 (local database)
3. ✅ Run Phase 3 (Stripe test mode)
4. ✅ Run Phase 4 (Twilio sandbox)
5. ✅ Run Phase 5 (end-to-end)
6. ✅ Run Phase 6 (manual testing)
7. 🚀 Onboard first paying customer

