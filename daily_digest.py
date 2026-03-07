"""
daily_digest.py

Fetches today's top 10 games, builds a clean HTML email, and sends it
to all subscribers via Resend. Called by Vercel Cron at 8am ET daily.

Vercel cron endpoint: GET /api/send-digest
"""

import pytz
from datetime import datetime
from app import fetch_games_for_date
from subscribe import get_all_subscribers, send_digest


# ——— EMAIL TEMPLATE ———

def build_email(games: list, date_str: str) -> tuple[str, str]:
    """Returns (subject, html_body) for the daily digest."""

    date_label = datetime.strptime(date_str, "%Y%m%d").strftime("%A, %B %-d")

    league_colors = {
        "NBA": "#c9a227", "NFL": "#5aa1e0", "NHL": "#70c8f0",
        "MLB": "#e07070", "CFB": "#a07ad0", "CBB": "#60c890",
    }

    rows_html = ""
    for i, game in enumerate(games[:10], start=1):
        color = league_colors.get(game["league"], "#BC9B6A")
        rivalry_badge = (
            '<span style="color:#BC9B6A;font-size:11px;font-weight:600;'
            'letter-spacing:0.5px;">🔥 RIVALRY &nbsp;</span>'
            if game.get("is_rivalry") else ""
        )
        rows_html += f"""
        <tr>
          <td style="padding:16px 0;border-bottom:1px solid #2a2a2a;vertical-align:top;">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td width="36" style="vertical-align:top;padding-right:16px;">
                  <span style="font-family:'Arial Black',sans-serif;font-size:26px;
                    color:{'#BC9B6A' if i <= 3 else '#3a3a3a'};line-height:1;">{i}</span>
                </td>
                <td style="vertical-align:top;">
                  <div style="margin-bottom:4px;">
                    <span style="background:#161616;color:{color};border:1px solid {color}33;
                      font-size:10px;font-weight:700;letter-spacing:1.5px;padding:2px 7px;
                      border-radius:3px;font-family:monospace;">{game['league']}</span>
                    &nbsp;{rivalry_badge}
                  </div>
                  <div style="font-size:17px;font-weight:700;color:#f0ece4;margin:4px 0;">
                    {game['matchup']}
                  </div>
                  <div style="font-size:12px;color:#7a7670;margin-bottom:6px;">
                    {game['time']} ET &nbsp;·&nbsp; {game['where_to_watch']}
                  </div>
                  <div style="font-size:12px;color:#7a7670;">
                    <span style="color:#4a4742;">Moneyline:</span> {game['favored']}
                    &nbsp;&nbsp;
                    <span style="color:#4a4742;">Spread:</span> {game['favored_spread']}
                  </div>
                  {f'<div style="font-size:12px;color:#7a7670;margin-top:6px;font-style:italic;">{game["description"]}</div>' if game.get("description") else ""}
                </td>
                <td width="70" style="vertical-align:top;text-align:right;">
                  <div style="font-family:\'Arial Black\',sans-serif;font-size:30px;
                    color:#f0ece4;line-height:1;">{game['score']}</div>
                  <div style="font-size:9px;color:#4a4742;letter-spacing:1px;
                    text-transform:uppercase;font-family:monospace;">W2W PTS</div>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        """

    subject = f"W2W Sports — Top 10 for {date_label}"

    html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{subject}</title>
</head>
<body style="margin:0;padding:0;background:#0d0d0d;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">

  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0d0d0d;">
    <tr>
      <td align="center" style="padding:40px 16px;">
        <table width="600" cellpadding="0" cellspacing="0"
          style="max-width:600px;width:100%;background:#0d0d0d;">

          <!-- HEADER -->
          <tr>
            <td style="padding:0 0 32px 0;border-bottom:1px solid #2a2a2a;">
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td>
                    <div style="font-family:'Arial Black',sans-serif;font-size:36px;
                      color:#f0ece4;letter-spacing:3px;line-height:1;">
                      <span style="color:#98002E;">W</span>2W
                      <span style="font-size:14px;color:#7a7670;
                        letter-spacing:2px;font-weight:400;"> SPORTS</span>
                    </div>
                    <div style="font-size:13px;color:#7a7670;margin-top:6px;">
                      {date_label}
                    </div>
                  </td>
                  <td align="right">
                    <div style="font-size:11px;color:#4a4742;font-family:monospace;
                      letter-spacing:1px;text-transform:uppercase;">
                      Top 10 Matchups
                    </div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- GAMES -->
          <tr>
            <td>
              <table width="100%" cellpadding="0" cellspacing="0">
                {rows_html}
              </table>
            </td>
          </tr>

          <!-- FOOTER -->
          <tr>
            <td style="padding:32px 0 0 0;border-top:1px solid #2a2a2a;">
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td>
                    <a href="https://w2w-sports.com"
                      style="color:#BC9B6A;font-size:13px;text-decoration:none;
                      font-weight:600;">w2w-sports.com</a>
                    <div style="font-size:11px;color:#4a4742;margin-top:4px;">
                      Know what to watch. Every night.
                    </div>
                  </td>
                  <td align="right">
                    <a href="https://w2w-sports.com/unsubscribe?email={{{{email}}}}"
                      style="font-size:11px;color:#4a4742;text-decoration:underline;">
                      Unsubscribe
                    </a>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>

</body>
</html>
    """

    return subject, html


def run_digest():
    """Main entry point — fetch games, build email, send to all subscribers."""
    et = pytz.timezone("US/Eastern")
    today = datetime.now(et).strftime("%Y%m%d")
    date_label = datetime.now(et).strftime("%Y%m%d")

    print(f"Fetching games for {today}...")
    games = fetch_games_for_date(today, et)

    if not games:
        print("No games today, skipping digest.")
        return

    print(f"Found {len(games)} games. Building email...")
    subject, html = build_email(games, today)

    print("Fetching subscribers...")
    subscribers = get_all_subscribers()
    print(f"Sending to {len(subscribers)} subscribers...")

    success = send_digest(subject, html, subscribers)
    print("Sent!" if success else "Send failed.")


if __name__ == "__main__":
    run_digest()
