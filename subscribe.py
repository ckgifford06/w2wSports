import os
import requests

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")

def add_subscriber(email: str) -> dict:
    """
    Insert an email into the Supabase subscribers table.
    Returns {"success": True} or {"error": "message"}.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        return {"error": "Supabase not configured"}

    url = f"{SUPABASE_URL}/rest/v1/subscribers"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }

    resp = requests.post(url, json={"email": email}, headers=headers)

    # 201 = inserted, 409 = already exists (unique constraint) — both are fine
    if resp.status_code in (201, 409):
        return {"success": True}

    return {"error": f"Database error ({resp.status_code})"}


def get_all_subscribers() -> list:
    """Return list of all subscriber email strings."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []

    url = f"{SUPABASE_URL}/rest/v1/subscribers?select=email"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }

    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return [row["email"] for row in resp.json()]
    return []


def send_digest(subject: str, html_body: str, recipients: list) -> bool:
    """Send the daily digest email via Resend to a list of recipients."""
    if not RESEND_API_KEY:
        print("Resend not configured")
        return False

    if not recipients:
        print("No subscribers to send to")
        return False

    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "from": "W2W Sports <digest@w2w-sports.com>",
        "to": recipients,
        "subject": subject,
        "html": html_body,
    }

    resp = requests.post(url, json=payload, headers=headers)
    return resp.status_code == 200
