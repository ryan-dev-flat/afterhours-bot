-- AfterHours Bot — Multi-Tenant Database Schema
-- Run against a Postgres 14+ database.
--
-- Usage:
--   psql $DATABASE_URL -f schema.sql
--
-- On Railway: add the Postgres plugin, grab DATABASE_URL from the Variables tab,
-- then run this file once to bootstrap the tables.

-- ── Extensions ───────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "pgcrypto";   -- gen_random_uuid()

-- ── Accounts ─────────────────────────────────────────────────────────────────
-- One row per paying customer (tenant).
CREATE TABLE IF NOT EXISTS accounts (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name      TEXT NOT NULL,
    owner_name        TEXT NOT NULL,
    owner_email       TEXT,
    owner_phone       TEXT,                          -- for WhatsApp owner notifications
    status            TEXT NOT NULL DEFAULT 'pending'
                      CHECK (status IN ('pending','onboarding','active','suspended','cancelled')),
    stripe_customer_id TEXT UNIQUE,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ── Business Profiles ────────────────────────────────────────────────────────
-- The bot personality / config for each tenant.
-- Mirrors the current business.json structure stored as JSONB so new fields
-- never require a migration.
CREATE TABLE IF NOT EXISTS business_profiles (
    account_id  UUID PRIMARY KEY REFERENCES accounts(id) ON DELETE CASCADE,
    config      JSONB NOT NULL DEFAULT '{}',
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ── Channels ─────────────────────────────────────────────────────────────────
-- Maps a Twilio sender number to an account.  The webhook uses this to route
-- incoming messages to the correct tenant.
CREATE TABLE IF NOT EXISTS channels (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id    UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    twilio_number TEXT NOT NULL UNIQUE,               -- e.g. "whatsapp:+14155238886"
    status        TEXT NOT NULL DEFAULT 'provisioning'
                  CHECK (status IN ('provisioning','active','disabled')),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_channels_twilio_number ON channels(twilio_number);

-- ── Leads ────────────────────────────────────────────────────────────────────
-- Every captured lead, attributed to the correct account.
CREATE TABLE IF NOT EXISTS leads (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id     UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    customer_phone TEXT,                              -- the WhatsApp number that texted in
    lead_data      JSONB NOT NULL DEFAULT '{}',       -- {name, service, time, phone}
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_leads_account_id ON leads(account_id);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at DESC);

-- ── Auto-update updated_at ───────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_accounts_updated_at
    BEFORE UPDATE ON accounts
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE OR REPLACE TRIGGER trg_business_profiles_updated_at
    BEFORE UPDATE ON business_profiles
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

