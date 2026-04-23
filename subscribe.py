import os
import json
import uuid
import requests

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")


def add_pending_subscriber(email: str) -> dict:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return {"error": "Supabase not configured"}

    token = str(uuid.uuid4())
    url = f"{SUPABASE_URL}/rest/v1/pending_subscribers"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }
    resp = requests.post(url, json={"email": email, "token": token}, headers=headers)
    if resp.status_code in (200, 201):
        return {"success": True, "token": token}
    return {"error": f"Database error ({resp.status_code})"}


def send_confirmation_email(email: str, token: str) -> bool:
    if not RESEND_API_KEY:
        return False

    confirm_url = f"https://www.w2w-sports.com/confirm?token={token}"

    html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#0d0d0d;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0d0d0d;">
    <tr>
      <td align="center" style="padding:40px 16px;">
        <table width="520" cellpadding="0" cellspacing="0" style="max-width:520px;width:100%;background:#0d0d0d;">
          <tr>
            <td style="padding:0 0 32px 0;border-bottom:1px solid #2a2a2a;">
              <div style="font-family:'Arial Black',sans-serif;font-size:32px;color:#f0ece4;letter-spacing:3px;line-height:1;">
                <span style="color:#98002E;">W</span>2W
                <span style="font-size:13px;color:#7a7670;letter-spacing:2px;font-weight:400;"> SPORTS</span>
              </div>
            </td>
          </tr>
          <tr>
            <td style="padding:32px 0;">
              <div style="font-size:22px;font-weight:700;color:#f0ece4;margin-bottom:12px;">Confirm your subscription</div>
              <div style="font-size:15px;color:#7a7670;line-height:1.7;margin-bottom:28px;">
                You're one click away from getting the top 10 sports matchups delivered to your inbox every morning at 9:30 am ET.
              </div>
              <a href="{confirm_url}" style="display:inline-block;background:#98002E;color:#ffffff;font-size:14px;font-weight:600;letter-spacing:0.5px;padding:14px 32px;border-radius:4px;text-decoration:none;">
                Confirm Subscription
              </a>
              <div style="margin-top:20px;font-size:12px;color:#4a4742;">
                Or copy this link:<br><span style="color:#7a7670;">{confirm_url}</span>
              </div>
            </td>
          </tr>
          <tr>
            <td style="padding:24px 0 0 0;border-top:1px solid #2a2a2a;">
              <div style="font-size:11px;color:#4a4742;">If you didn't sign up for W2W Sports, you can safely ignore this email.</div>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
    """

    resp = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
        json={
            "from": "W2W Sports <digest@w2w-sports.com>",
            "to": [email],
            "subject": "Confirm your W2W Sports subscription",
            "html": html,
        },
    )
    return resp.status_code == 200


def confirm_subscriber(token: str) -> dict:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return {"error": "Supabase not configured"}

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }

    lookup_url = f"{SUPABASE_URL}/rest/v1/pending_subscribers?token=eq.{token}&select=email"
    resp = requests.get(lookup_url, headers=headers)
    if resp.status_code != 200 or not resp.json():
        return {"error": "Invalid or expired confirmation link"}

    email = resp.json()[0]["email"]

    sub_headers = {**headers, "Prefer": "return=minimal"}
    resp2 = requests.post(f"{SUPABASE_URL}/rest/v1/subscribers", json={"email": email}, headers=sub_headers)
    if resp2.status_code not in (200, 201, 409):
        return {"error": f"Could not confirm subscription ({resp2.status_code})"}

    requests.delete(f"{SUPABASE_URL}/rest/v1/pending_subscribers?token=eq.{token}", headers=headers)

    return {"success": True, "email": email}



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
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []

    url = f"{SUPABASE_URL}/rest/v1/subscribers?select=email"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
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

    import time

    headers = {"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"}

    # Resend batch endpoint accepts up to 100 emails per call.
    # Chunk recipients and send batches to avoid per-email sequential overhead.
    BATCH_SIZE = 100
    success_count = 0
    total = len(recipients)

    for i in range(0, total, BATCH_SIZE):
        chunk = recipients[i:i + BATCH_SIZE]
        batch_payload = [
            {
                "from": "W2W Sports <digest@w2w-sports.com>",
                "to": [email],
                "subject": subject,
                "html": html_body.replace("{{email}}", email),
            }
            for email in chunk
        ]
        try:
            resp = requests.post(
                "https://api.resend.com/emails/batch",
                json=batch_payload,
                headers=headers,
                timeout=15,
            )
            # Resend returns 200 for batch and 202 for single sends
            if resp.status_code in (200, 202):
                try:
                    data = resp.json()
                    sent = len(data.get("data", []))
                    success_count += sent if sent else len(chunk)
                except Exception:
                    success_count += len(chunk)
            else:
                print(f"batch {i}: status {resp.status_code} body={resp.text[:300]}")
        except Exception as e:
            print(f"batch {i} error: {e}")

        # Small delay between batches to stay comfortably under Resend's 5 req/sec limit
        if i + BATCH_SIZE < total:
            time.sleep(0.25)

    print(f"Sent {success_count}/{total} subscribers")
    return success_count > 0



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
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
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


def trim_game_scores(keep: int = 100) -> bool:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return False

    url = f"{SUPABASE_URL}/rest/v1/game_scores?select=score&order=score.desc&limit=1&offset={keep}"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200 or not resp.json():
        return True

    cutoff_score = resp.json()[0]["score"]
    del_headers = {**headers, "Content-Type": "application/json"}
    requests.delete(f"{SUPABASE_URL}/rest/v1/game_scores?score=lt.{cutoff_score}", headers=del_headers)
    return True
