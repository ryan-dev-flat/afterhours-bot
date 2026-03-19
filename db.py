"""
Database layer for the multi-tenant AfterHours Bot.

Uses psycopg2 with a simple connection-pool pattern.
Expects DATABASE_URL in the environment (Postgres connection string).

The public API mirrors TestDatabase from test_e2e_setup.py so the same
method names work in tests and production.
"""

import json
import logging
import os
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

import psycopg2
import psycopg2.extras
from psycopg2.pool import SimpleConnectionPool

logger = logging.getLogger(__name__)

# ── Connection pool ───────────────────────────────────────────────────────────
_pool: Optional[SimpleConnectionPool] = None


def get_pool() -> SimpleConnectionPool:
    """Return (and lazily create) the connection pool."""
    global _pool
    if _pool is None or _pool.closed:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise EnvironmentError(
                "DATABASE_URL is not set. Add a Postgres plugin on Railway "
                "or set it in your .env for local development."
            )
        _pool = SimpleConnectionPool(minconn=1, maxconn=5, dsn=database_url)
        logger.info("Database connection pool created")
    return _pool


@contextmanager
def get_conn():
    """Yield a connection from the pool; return it when done."""
    pool = get_pool()
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


# ── Accounts ──────────────────────────────────────────────────────────────────

def create_account(
    company_name: str,
    owner_name: str,
    owner_email: Optional[str] = None,
    owner_phone: Optional[str] = None,
    stripe_customer_id: Optional[str] = None,
) -> str:
    """Insert a new account and return its UUID."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO accounts (company_name, owner_name, owner_email,
                                      owner_phone, stripe_customer_id)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (company_name, owner_name, owner_email, owner_phone,
                 stripe_customer_id),
            )
            return str(cur.fetchone()[0])


def get_account(account_id: str) -> Optional[Dict[str, Any]]:
    """Return an account row as a dict, or None."""
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM accounts WHERE id = %s", (account_id,))
            row = cur.fetchone()
            return dict(row) if row else None


def update_account_status(account_id: str, status: str) -> None:
    """Change an account's status."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE accounts SET status = %s WHERE id = %s",
                (status, account_id),
            )


def get_account_id_by_company(company_name: str) -> Optional[str]:
    """Return the most recent account UUID matching company_name, or None."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id FROM accounts
                WHERE company_name = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (company_name,),
            )
            row = cur.fetchone()
            return str(row[0]) if row else None


def update_account_owner_phone(account_id: str, owner_phone: str) -> None:
    """Update the owner_phone on an account record."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE accounts SET owner_phone = %s WHERE id = %s",
                (owner_phone, account_id),
            )


def set_business_profile(account_id: str, config: Dict[str, Any]) -> None:
    """Alias for store_business_profile — used by onboarding flow."""
    store_business_profile(account_id, config)


# ── Business Profiles ────────────────────────────────────────────────────────

def store_business_profile(account_id: str, config: Dict[str, Any]) -> None:
    """Upsert the business profile config (JSONB) for an account."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO business_profiles (account_id, config)
                VALUES (%s, %s)
                ON CONFLICT (account_id)
                DO UPDATE SET config = EXCLUDED.config
                """,
                (account_id, json.dumps(config)),
            )


def get_business_profile(account_id: str) -> Optional[Dict[str, Any]]:
    """Return the business config dict for an account, or None."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT config FROM business_profiles WHERE account_id = %s",
                (account_id,),
            )
            row = cur.fetchone()
            return row[0] if row else None


# ── Channels (Twilio number → account routing) ───────────────────────────────

def store_channel(account_id: str, twilio_number: str,
                  status: str = "provisioning") -> str:
    """Create a channel mapping and return its UUID."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO channels (account_id, twilio_number, status)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (account_id, twilio_number, status),
            )
            return str(cur.fetchone()[0])


def get_account_by_twilio_number(twilio_number: str) -> Optional[Dict[str, Any]]:
    """Look up an account by the Twilio number that received the message.
    This is the core multi-tenant routing query."""
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT a.* FROM accounts a
                JOIN channels c ON c.account_id = a.id
                WHERE c.twilio_number = %s
                  AND c.status = 'active'
                  AND a.status = 'active'
                """,
                (twilio_number,),
            )
            row = cur.fetchone()
            return dict(row) if row else None


def activate_channel(channel_id: str) -> None:
    """Mark a channel as active (after manual Twilio setup)."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE channels SET status = 'active' WHERE id = %s",
                (channel_id,),
            )


# ── Leads ─────────────────────────────────────────────────────────────────────

def store_lead(account_id: str, lead_data: Dict[str, Any],
               customer_phone: Optional[str] = None) -> str:
    """Store a captured lead and return its UUID."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO leads (account_id, customer_phone, lead_data)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (account_id, customer_phone, json.dumps(lead_data)),
            )
            return str(cur.fetchone()[0])


def get_leads(account_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Return recent leads for an account."""
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT * FROM leads
                WHERE account_id = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (account_id, limit),
            )
            return [dict(row) for row in cur.fetchall()]



# ── Admin queries ─────────────────────────────────────────────────────────────

def list_accounts() -> List[Dict[str, Any]]:
    """Return all accounts ordered by created_at desc."""
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM accounts ORDER BY created_at DESC")
            return [dict(row) for row in cur.fetchall()]


def list_channels(account_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return channels, optionally filtered by account_id."""
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if account_id:
                cur.execute(
                    "SELECT * FROM channels WHERE account_id = %s ORDER BY created_at DESC",
                    (account_id,),
                )
            else:
                cur.execute("SELECT * FROM channels ORDER BY created_at DESC")
            return [dict(row) for row in cur.fetchall()]


def get_account_by_stripe_customer(stripe_customer_id: str) -> Optional[Dict[str, Any]]:
    """Look up account by Stripe customer ID."""
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM accounts WHERE stripe_customer_id = %s",
                (stripe_customer_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None
