# Stripe & Twilio Testing Guide

How to test payment and messaging integrations before your first real customer.

## Stripe Test Mode

### Set up test API keys
1. Go to https://dashboard.stripe.com/test/apikeys
2. Copy your **Publishable Key** and **Secret Key**
3. Add to your `.env`:
   ```
   STRIPE_PUBLIC_KEY=pk_test_...
   STRIPE_SECRET_KEY=sk_test_...
   STRIPE_WEBHOOK_SECRET=whsec_test_...
   ```

### Test credit card numbers
Use these in Stripe test mode (they won't charge):

| Card Type | Number | Exp | CVC |
|-----------|--------|-----|-----|
| Visa | 4242 4242 4242 4242 | 12/25 | 123 |
| Visa (decline) | 4000 0000 0000 0002 | 12/25 | 123 |
| Amex | 3782 822463 10005 | 12/25 | 1234 |

### Test checkout flow
1. Start your Flask app locally
2. Go to `/checkout` (or your checkout page)
3. Enter test card: `4242 4242 4242 4242`
4. Verify:
   - Checkout succeeds
   - Webhook is received
   - Account is created in database
   - Subscription is marked active

### Test failed payment
1. Use card: `4000 0000 0000 0002`
2. Verify:
   - Payment is declined
   - Error message is shown
   - No account is created
   - Founder is NOT notified

### Test webhook locally
Use Stripe CLI to forward webhooks to your local app:

```bash
# Install Stripe CLI
# https://stripe.com/docs/stripe-cli

# Forward webhooks to localhost
stripe listen --forward-to localhost:5000/webhook/stripe

# In another terminal, trigger a test event
stripe trigger payment_intent.succeeded
```

## Twilio Test Mode

### Set up Twilio sandbox
1. Go to https://console.twilio.com/develop/sms/try-it-out
2. Get your **Twilio WhatsApp Sandbox Number**
3. Add to your `.env`:
   ```
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=your_auth_token_here
   TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
   ```

### Join the sandbox
1. Send `join <code>` to the sandbox number
2. You'll receive a confirmation
3. Now you can send/receive messages

### Test message flow
1. Send a message to the sandbox number
2. Verify:
   - Your webhook receives the message
   - Bot responds correctly
   - Response is sent back via Twilio
   - Message appears in your phone

### Test owner notifications
1. Set `OWNER_WHATSAPP_NUMBER` to your test number
2. Capture a lead in a conversation
3. Verify:
   - You receive a notification
   - Notification includes lead details
   - Notification goes to correct number

### Test with multiple numbers
1. Add multiple test numbers to the sandbox
2. Send messages from each
3. Verify:
   - Each gets their own bot instance
   - Conversation history is isolated
   - Leads are attributed correctly

## Local Testing Without External Services

### Mock Stripe
```python
from unittest.mock import patch

@patch('stripe.Checkout.Session.create')
def test_checkout(mock_create):
    mock_create.return_value = {
        'id': 'cs_test_123',
        'url': 'https://checkout.stripe.com/...'
    }
    # Test your checkout flow
```

### Mock Twilio
```python
from unittest.mock import patch

@patch('twilio.rest.Client.messages.create')
def test_notification(mock_create):
    mock_create.return_value = {'sid': 'SM123'}
    # Test your notification flow
```

## Testing Checklist

### Stripe
- [ ] Test checkout with valid card
- [ ] Test checkout with declined card
- [ ] Webhook is received and processed
- [ ] Account is created after payment
- [ ] Subscription is marked active
- [ ] Founder is notified of new customer
- [ ] Customer receives confirmation email

### Twilio
- [ ] Can send message to sandbox number
- [ ] Bot responds correctly
- [ ] Response is received on phone
- [ ] Owner notification is sent
- [ ] Notification includes all lead details
- [ ] Multiple test numbers work independently

### Integration
- [ ] Customer signs up → pays → gets onboarded
- [ ] Bot is live after onboarding
- [ ] Leads are captured and attributed
- [ ] Owner is notified of leads
- [ ] Multiple customers don't interfere

## Troubleshooting

### Stripe webhook not received
- Check that Stripe CLI is running
- Verify webhook URL is correct
- Check Flask logs for errors
- Verify webhook secret is correct

### Twilio message not received
- Verify you've joined the sandbox
- Check Twilio logs in console
- Verify webhook URL is correct
- Check Flask logs for errors

### Bot doesn't respond
- Verify Anthropic API key is set
- Check Flask logs for errors
- Run `test_bot.py` to verify bot logic
- Check that business config is loaded

### Owner notification not sent
- Verify `OWNER_WHATSAPP_NUMBER` is set
- Verify Twilio credentials are correct
- Check Flask logs for errors
- Verify lead was actually captured

