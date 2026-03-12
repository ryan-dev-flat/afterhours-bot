# SaaS Strategy Summary

## Product Direction
AfterHours Bot should evolve into a focused SaaS for small service businesses: an AI after-hours assistant that replies quickly, captures lead details, and helps ensure follow-up the next business day.

### Positioning
Sell the outcome, not the technology:
- stop missing after-hours leads
- collect job details automatically
- capture callback preferences
- alert the owner/team
- improve next-morning follow-up

Avoid positioning it as a generic chatbot or a broad operations platform at the MVP stage.

## Pricing and Packaging Recommendation
### Best starting model
Start with:
- **one core plan**
- **setup fee + monthly subscription**

### Suggested MVP pricing
- setup fee: **$149–$299**
- monthly subscription: **$99–$199/month**

Recommended starting point:
- **$199 setup + $149/month**

Why this works:
- covers manual onboarding and provisioning work
- preserves perceived value
- creates recurring SaaS revenue
- is simple to explain and sell

## Trial / Freemium Decision
### Recommended decision
- **Do not launch freemium**
- **Do not offer a free tier with limited lead messages**
- **Do not start with a public free trial**
- **Charge upfront instead**

### Better alternative to free access
Use:
- a live demo
- a founder-led walkthrough
- a demo video
- optionally a **14-day money-back guarantee**

### Why
This product still has setup friction, support cost, and real usage cost. A free plan or public trial would likely attract low-intent users and create avoidable support burden.

## Recommended MVP Scope
### Include now
Focus on the narrow, high-value workflow:
- WhatsApp after-hours lead capture
- AI lead qualification
- capture of name, service need, callback number, and preferred callback time
- owner/team alerts
- basic next-morning follow-up support or reminders

### Exclude for now
Do not overbuild these in the first SaaS version:
- deep Slack workflows
- broad email automation suites
- full calendar synchronization
- CRM replacement features
- advanced analytics dashboards
- complex omnichannel inbox workflows

## SaaS Delivery Model
### Recommended architecture
Use a **single shared multi-tenant app** first.

Why:
- fastest to build
- lowest ops burden
- cheapest to maintain
- much more scalable than one deployment per client

### Keep manual behind the scenes initially
It is fine to keep these partially manual at first:
- Twilio / WhatsApp sender setup
- onboarding review
- prompt tuning
- final activation
- support exception handling

The goal is to automate internal workflow first, not every external dependency on day one.

## Near-Term Roadmap
### Phase 1 — Start charging with minimal automation
Build:
- pricing CTA
- lead capture form
- founder alert emails
- Stripe Checkout + webhooks
- post-payment onboarding form
- account/subscription records

Keep manual:
- provisioning
- sender setup
- activation

### Phase 2 — Semi-automated onboarding
Build:
- customer login
- onboarding dashboard
- business profile editor
- billing portal link
- DB-backed tenant config
- provisioning status tracking

### Phase 3 — More complete SaaS automation
Build:
- provisioning jobs/workflows
- richer admin tools
- message and lead history views
- lifecycle automation
- better support and analytics tooling

## Recommended Next Steps
1. Add **Stripe** and founder alert emails
2. Move client configuration from JSON files into **Postgres**
3. Build a post-payment onboarding flow plus simple customer/admin dashboards

## Reference Docs
Longer supporting documents:
- `saas-strategy-transcript.md`
- `founder-strategy-memo.md`

