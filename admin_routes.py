"""
Admin dashboard for AfterHours Bot.
Protected by ADMIN_SECRET env var -- append ?key=<secret> to access.
"""
import logging
import os
from functools import wraps
from flask import Blueprint, request, abort
import db

logger = logging.getLogger(__name__)
admin_bp = Blueprint("admin", __name__)


def _require_admin(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        secret = os.environ.get("ADMIN_SECRET", "")
        if not secret:
            abort(403, "ADMIN_SECRET not configured")
        if request.args.get("key") != secret:
            abort(403, "Invalid admin key")
        return fn(*args, **kwargs)
    return wrapper


def _key():
    return request.args.get("key", "")


_CSS = ('<style>'
    '*{box-sizing:border-box}'
    'body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;max-width:960px;margin:0 auto;padding:24px;background:#f8f9fa;color:#1a1a1a}'
    'h1{font-size:1.6rem;margin-bottom:4px}h2{font-size:1.2rem;margin-top:32px}'
    '.subtitle{color:#666;margin-bottom:24px}'
    'table{width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.08)}'
    'th,td{text-align:left;padding:10px 14px;border-bottom:1px solid #eee;font-size:.9rem}'
    'th{background:#f1f3f5;font-weight:600;font-size:.8rem;text-transform:uppercase;letter-spacing:.5px}'
    'tr:last-child td{border-bottom:none}'
    'a{color:#635bff;text-decoration:none}a:hover{text-decoration:underline}'
    '.badge{display:inline-block;padding:2px 10px;border-radius:12px;font-size:.78rem;font-weight:600}'
    '.badge-active{background:#d3f9d8;color:#1b7a2b}.badge-onboarding{background:#fff3bf;color:#8a6d00}'
    '.badge-pending{background:#e9ecef;color:#495057}.badge-suspended{background:#ffe0e0;color:#c92a2a}'
    '.badge-cancelled,.badge-disabled{background:#e9ecef;color:#868e96}'
    '.badge-provisioning{background:#d0ebff;color:#1864ab}'
    '.card{background:#fff;border-radius:8px;padding:20px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,.08)}'
    '.btn{display:inline-block;padding:6px 16px;border-radius:6px;border:none;font-size:.85rem;cursor:pointer;font-weight:600}'
    '.btn-primary{background:#635bff;color:#fff}.btn-sm{padding:4px 12px;font-size:.8rem}'
    'form.inline{display:inline}'
    'input[type=text],select{padding:6px 10px;border:1px solid #ccc;border-radius:6px;font-size:.9rem}'
    '.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}'
    '.stat{font-size:2rem;font-weight:700}.stat-label{font-size:.8rem;color:#666;text-transform:uppercase}'
    '.back{margin-bottom:16px;display:inline-block;font-size:.85rem}'
    '</style>')


@admin_bp.route("/admin", methods=["GET"])
@_require_admin
def admin_home():
    accounts = db.list_accounts()
    k = _key()
    rows = ""
    for a in accounts:
        s = a["status"]
        badge = '<span class="badge badge-' + s + '">' + s + '</span>'
        dt = a["created_at"].strftime("%b %d, %Y") if a.get("created_at") else ""
        rows += ('<tr><td><a href="/admin/account/' + str(a["id"]) + '?key=' + k + '">'
                 + a["company_name"] + '</a></td><td>' + a["owner_name"] + '</td>'
                 + '<td>' + (a.get("owner_email", "") or "") + '</td><td>' + badge
                 + '</td><td>' + dt + '</td></tr>')
    total = len(accounts)
    active = sum(1 for a in accounts if a["status"] == "active")
    empty_row = '<tr><td colspan="5" style="text-align:center;color:#999;padding:40px">No accounts yet</td></tr>'
    body = rows if rows else empty_row
    return ('<!DOCTYPE html><html><head><title>Admin</title>' + _CSS + '</head><body>'
            + '<h1>AfterHours Admin</h1><p class="subtitle">Manage accounts, channels, and leads</p>'
            + '<div class="grid" style="margin-bottom:24px">'
            + '<div class="card"><div class="stat">' + str(total) + '</div><div class="stat-label">Total Accounts</div></div>'
            + '<div class="card"><div class="stat">' + str(active) + '</div><div class="stat-label">Active</div></div></div>'
            + '<table><tr><th>Company</th><th>Owner</th><th>Email</th><th>Status</th><th>Created</th></tr>'
            + body + '</table></body></html>'), 200



@admin_bp.route("/admin/account/<account_id>", methods=["GET"])
@_require_admin
def admin_account(account_id):
    k = _key()
    account = db.get_account(account_id)
    if not account:
        abort(404, "Account not found")
    profile = db.get_business_profile(account_id) or {}
    channels = db.list_channels(account_id)
    leads = db.get_leads(account_id, limit=25)
    status = account["status"]
    badge = '<span class="badge badge-' + status + '">' + status + '</span>'
    statuses = ["pending", "onboarding", "active", "suspended", "cancelled"]
    status_opts = "".join('<option value="' + s + '"' + (' selected' if s == status else '') + '>' + s + '</option>' for s in statuses)
    # Channels rows
    ch_rows = ""
    for c in channels:
        cs = c["status"]
        cb = '<span class="badge badge-' + cs + '">' + cs + '</span>'
        disabled = " disabled" if cs == "active" else ""
        ch_rows += ('<tr><td>' + c["twilio_number"] + '</td><td>' + cb + '</td><td>'
                    + '<form class="inline" method="POST" action="/admin/account/' + account_id + '/channel?key=' + k + '">'
                    + '<input type="hidden" name="channel_id" value="' + str(c["id"]) + '">'
                    + '<input type="hidden" name="action" value="activate">'
                    + '<button type="submit" class="btn btn-sm btn-primary"' + disabled + '>Activate</button></form></td></tr>')
    # Leads rows
    lead_rows = ""
    for l in leads:
        ld = l.get("lead_data", {})
        dt = l["created_at"].strftime("%b %d %H:%M") if l.get("created_at") else ""
        lead_rows += ('<tr><td>' + ld.get("name", "-") + '</td><td>' + ld.get("service", "-")
                      + '</td><td>' + ld.get("time", "-") + '</td><td>' + (l.get("customer_phone", "") or "-")
                      + '</td><td>' + dt + '</td></tr>')
    # Profile card
    if profile:
        svcs = ", ".join(profile.get("services", [])[:5])
        prof_html = ('<div class="card"><h2 style="margin-top:0">Business Profile</h2>'
                     + '<p><strong>Type:</strong> ' + profile.get("type", "-") + '</p>'
                     + '<p><strong>Location:</strong> ' + profile.get("location", "-") + '</p>'
                     + '<p><strong>Hours:</strong> ' + profile.get("hours", "-") + '</p>'
                     + '<p><strong>Services:</strong> ' + (svcs or "-") + '</p>'
                     + '<p><strong>Emergency Line:</strong> ' + profile.get("emergency_line", "-") + '</p></div>')
    else:
        prof_html = '<div class="card"><p style="color:#999">No business profile submitted yet.</p></div>'
    ch_empty = '<tr><td colspan="3" style="text-align:center;color:#999;padding:20px">No channels yet</td></tr>'
    ld_empty = '<tr><td colspan="5" style="text-align:center;color:#999;padding:20px">No leads yet</td></tr>'
    return ('<!DOCTYPE html><html><head><title>' + account["company_name"] + ' - Admin</title>' + _CSS + '</head><body>'
            + '<a class="back" href="/admin?key=' + k + '">Back to accounts</a>'
            + '<h1>' + account["company_name"] + '</h1>'
            + '<p class="subtitle">' + account["owner_name"] + ' - ' + (account.get("owner_email", "") or "no email")
            + ' - ' + (account.get("owner_phone", "") or "no phone") + '</p>'
            + '<div class="card"><strong>Status:</strong> ' + badge
            + '<form class="inline" method="POST" action="/admin/account/' + account_id + '/status?key=' + k + '" style="margin-left:16px">'
            + '<select name="status">' + status_opts + '</select>'
            + '<button type="submit" class="btn btn-sm btn-primary">Update</button></form>'
            + '<p style="margin-top:8px;font-size:.8rem;color:#999">Stripe: ' + (account.get("stripe_customer_id", "") or "-") + '</p></div>'
            + prof_html
            + '<h2>Channels</h2>'
            + '<table><tr><th>Twilio Number</th><th>Status</th><th>Action</th></tr>' + (ch_rows or ch_empty) + '</table>'
            + '<div class="card" style="margin-top:12px"><form method="POST" action="/admin/account/' + account_id + '/channel?key=' + k + '">'
            + '<input type="hidden" name="action" value="add">'
            + '<input type="text" name="twilio_number" placeholder="whatsapp:+1..." style="width:240px">'
            + '<button type="submit" class="btn btn-primary">Add Channel</button></form></div>'
            + '<h2>Leads (' + str(len(leads)) + ')</h2>'
            + '<table><tr><th>Name</th><th>Service</th><th>Time</th><th>Phone</th><th>Date</th></tr>' + (lead_rows or ld_empty) + '</table>'
            + '</body></html>'), 200


@admin_bp.route("/admin/account/<account_id>/status", methods=["POST"])
@_require_admin
def admin_update_status(account_id):
    new_status = request.form.get("status", "").strip()
    k = _key()
    try:
        db.update_account_status(account_id, new_status)
        logger.info("Admin: account %s status -> %s", account_id, new_status)
    except Exception as e:
        logger.error("Admin status update failed: %s", e)
    return '<script>window.location="/admin/account/' + account_id + '?key=' + k + '"</script>'


@admin_bp.route("/admin/account/<account_id>/channel", methods=["POST"])
@_require_admin
def admin_channel(account_id):
    action = request.form.get("action", "")
    k = _key()
    if action == "add":
        twilio_number = request.form.get("twilio_number", "").strip()
        if twilio_number:
            try:
                ch_id = db.store_channel(account_id, twilio_number)
                logger.info("Admin: channel %s added for account %s", ch_id, account_id)
            except Exception as e:
                logger.error("Admin add channel failed: %s", e)
    elif action == "activate":
        channel_id = request.form.get("channel_id", "").strip()
        if channel_id:
            try:
                db.activate_channel(channel_id)
                logger.info("Admin: channel %s activated", channel_id)
            except Exception as e:
                logger.error("Admin activate channel failed: %s", e)
    return '<script>window.location="/admin/account/' + account_id + '?key=' + k + '"</script>'
