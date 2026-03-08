import os
import json
import requests

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")

def save_game_scores(games: list, date_str: str) -> bool:
    """
    Upsert a list of scored games into the game_scores table.
    date_str should be in YYYY-MM-DD format.
    """
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
    """
    Fetch the highest-scored games ever stored, optionally filtered by league.
    Returns a list of dicts ordered by score descending.
    """
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
        # breakdown comes back as a dict from JSONB — normalise just in case
        for row in rows:
            if isinstance(row.get("breakdown"), str):
                try:
                    row["breakdown"] = json.loads(row["breakdown"])
                except Exception:
                    row["breakdown"] = {}
        return rows
    return []

def trim_game_scores(keep: int = 100) -> bool:
    """Delete all rows outside the top N scores."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return False

    # Fetch the cutoff score (the score at position `keep`)
    url = f"{SUPABASE_URL}/rest/v1/game_scores?select=score&order=score.desc&limit=1&offset={keep}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200 or not resp.json():
        return True  # fewer than `keep` rows exist, nothing to trim

    cutoff_score = resp.json()[0]["score"]

    # Delete everything strictly below the cutoff
    del_url = f"{SUPABASE_URL}/rest/v1/game_scores?score=lt.{cutoff_score}"
    del_headers = {**headers, "Content-Type": "application/json"}
    requests.delete(del_url, headers=del_headers)
    return True
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
    """Send the daily digest email via Resend, one per recipient for privacy."""
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
