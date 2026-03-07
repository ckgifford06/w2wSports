import os
import json
import requests


SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")


def save_game_scores(games: list, date_str: str) -> bool:
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Supabase not configured — skipping score save")
        return False

    url = f"{SUPABASE_URL}/rest/v1/game_scores"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }

    records = [
        {
            "date": date_str,
            "matchup": g["matchup"],
            "league": g["league"],
            "score": g["score"],
            "breakdown": g.get("breakdown", {}),
            "is_rivalry": g.get("is_rivalry", False),
            "where_to_watch": g.get("where_to_watch", ""),
        }
        for g in games
    ]

    resp = requests.post(url, json=records, headers=headers)
    success = resp.status_code in (200, 201)
    if not success:
        print(f"save_game_scores failed: {resp.status_code} {resp.text}")
    return success


def get_top_games(limit: int = 100, league: str = None) -> list:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []

    params = f"select=*&order=score.desc&limit={limit}"
    if league:
        params += f"&league=eq.{league}"

    url = f"{SUPABASE_URL}/rest/v1/game_scores?{params}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }

    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        rows = resp.json()
        for row in rows:
            if isinstance(row.get("breakdown"), str):
                try:
                    row["breakdown"] = json.loads(row["breakdown"])
                except Exception:
                    row["breakdown"] = {}
        return rows
    return []

def add_subscriber(email: str) -> dict:
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

    success_count = 0
    for email in recipients:
        payload = {
            "from": "W2W Sports <digest@w2w-sports.com>",
            "to": [email],
            "subject": subject,
            "html": html_body.replace("{{email}}", email),
        }
        resp = requests.post(url, json=payload, headers=headers)
        if resp.status_code == 200:
            success_count += 1

    print(f"Sent to {success_count}/{len(recipients)} subscribers")
    return success_count > 0
