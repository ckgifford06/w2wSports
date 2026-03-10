# W2W Sports

**Live site: [w2w-sports.com](https://w2w-sports.com)**

W2W stands for What-2-Watch. Instead of scrolling through a full day of sports schedules trying to figure out what to actually watch, this site does that math for you and ranks the top 10 games of the day by how good they are likely to be.

We built this in October 2025 because we kept having the same problem as sports fans. Too many games, not enough time, and no good way to know which ones were actually worth sitting down for.

---

<img width="1512" height="856" alt="Screenshot 2026-03-09 at 9 51 38 AM" src="https://github.com/user-attachments/assets/cfb24f79-a31d-45a1-a24b-9fb21d5b0d0f" />

<img width="1512" height="853" alt="Screenshot 2026-03-09 at 9 51 53 AM" src="https://github.com/user-attachments/assets/5d080f8e-aea2-4555-8004-9d306ba0679e" />


---
## What It Does

Every day the site pulls the full schedule for every supported league from ESPN's public API, runs each game through our scoring algorithm, and displays the top 10 results ranked from best to worst. Each game shows the start time, broadcast network, moneyline, spread, and live score once the game starts.

Users can filter by league, which switches from the global top 10 to all games in that league sorted by score. Click NBA and you see every basketball game that day ranked, even ones that did not crack the overall top 10.

Subscribers receive a daily email digest at 8am ET with the top 10 matchups for that day.

Supported leagues: NBA, NFL, NHL, MLB, CFB (college football), CBB (college basketball), and EPL (English Premier League).

---

## Pages

- **/** — Homepage. Top 10 matchups today, filterable by league, with live score polling every 30 seconds and a Live Now banner when a top game is in progress. Includes email signup.
- **/calendar** — 7-Day Rivalry Calendar. Browse any day in the next week. Games load lazily per day — clicking a tab fetches that day's full schedule and ranks it instantly.
- **/formula** — Explains the W2W scoring algorithm in detail.
- **/about** — About the project and the team.
- **/unsubscribe** — Removes a user from the daily digest. Linked from every email footer.

---

## How It Is Built

This is a full-stack web application. The backend is Python on Flask, the frontend is HTML, CSS, and vanilla JavaScript with Jinja2 templating.

**Backend (Python + Flask)**

Flask receives each request, fetches and scores the games, and returns a finished HTML page. Routes in `app.py`:

- `GET /` — Homepage
- `GET /calendar` — 7-day calendar page
- `GET /about` — About page
- `GET /formula` — Formula page
- `GET /unsubscribe?email=` — Removes an email from Supabase and shows confirmation
- `POST /api/subscribe` — Accepts a JSON body with an email field and saves it to Supabase
- `GET /api/live?tz=` — Returns live score data for today's games as JSON. Polled every 30 seconds by the frontend.
- `GET /api/games?date=YYYYMMDD&tz=` — Returns all scored games for any given date as JSON. Used by the calendar page for lazy loading.
- `GET /api/send-digest?token=` — Vercel Cron endpoint. Fetches today's games, builds the email, and sends to all subscribers. Protected by a secret token.

All game-fetching logic lives in a single shared `fetch_games_for_date(date_str, local_tz)` function. The homepage, calendar endpoint, and digest all call it, no duplicated ESPN logic.

The rating logic lives in separate modules, one per sport: `NBArating.py`, `NFLrating.py`, `NHLrating.py`, `MLBrating.py`, `CFBrating.py`, `CBBrating.py`. Each has a `calculate_score()` function and a `calculate_score_breakdown()` function. The breakdown returns a dict of all five components, which the frontend uses to render the animated score breakdown bars.

**Email Digest**

The daily digest is handled across two files:

`subscribe.py` manages all Supabase and Resend interactions — inserting new subscribers, fetching the full subscriber list, and sending emails. Each subscriber receives an individual email so no recipient can see other email addresses.

`daily_digest.py` contains the email template and the `run_digest()` function. It fetches today's top 10 games, builds a full HTML email styled to match the site, and calls `subscribe.py` to send it. It can also be run directly from the command line for testing.

Vercel Cron fires the `/api/send-digest` endpoint at 8am ET (13:00 UTC) every day via `vercel.json`.

**External Services**

- **Supabase** — Postgres database in the cloud. Stores subscriber email addresses. Accessed via Supabase's REST API directly from Python using `requests`.
- **Resend** — Email delivery API. Sends the daily digest. Free tier supports up to 3,000 emails per month.

**Templating (Jinja2)**

All pages extend `base.html` via template inheritance. The base template contains the nav, fonts, global CSS variables, and Open Graph / meta tags. Individual pages override `{% block title %}`, `{% block og_title %}`, `{% block og_description %}`, and `{% block og_url %}` for per-page SEO.

**Frontend (HTML, CSS, JavaScript)**

The league filter is entirely client-side. All games are rendered into the page on load with `data-league` and `data-overall-rank` attributes. Clicking a filter pill toggles visibility without a server round-trip. The header title updates dynamically to reflect the current filter and game count.

Live scores use `setInterval` polling every 30 seconds against `/api/live`. Matches are found by `data-matchup` attribute rather than index so updates are stable even if game order changes.

The score breakdown chart animates on expand using CSS transitions. Bars start at `width: 0%` and transition to their real percentage when the row opens, resetting when it closes.

The 7-day calendar builds date tabs dynamically in JavaScript. Clicking a tab calls `/api/games` for that date. The other six days are prefetched in the background just to populate the game count badge — no full data load until the tab is clicked.

**Styling**

Dark theme throughout: `#0d0d0d` background, `#98002E` crimson, `#BC9B6A` gold. Fonts: Bebas Neue for display, DM Sans for body, DM Mono for data/labels. Fully responsive with breakpoints at 768px and 480px.

**Hosting**

The site runs on Vercel.

---

## The Scoring Algorithm

Every game gets a W2W Score from five components:

**Rivalry (0–12 pts):** Hard-coded per matchup based on historical rivalry intensity. Duke vs. UNC is a 12. Two teams with no history are a 0.

**Marketability (10–20 pts):** Reflects team popularity and national following. Set manually per team. Lakers vs. Celtics scores much higher than two small-market teams.

**Competitiveness (0–6.67 pts):** Dynamic. The closer the two teams' win-loss records, the higher this score. Evenly matched teams tend to produce better games.

**Quality of Play (0–8.5 pts):** Dynamic. Based on combined win percentage. Two good teams score higher than two bad teams.

**Importance (0–14 pts regular season, higher in postseason):** Accounts for season context. Late-season games with playoff implications score higher. Conference tournaments and playoffs get a significant boost. Flags in each rating module (`march_madness = True`, `playoffs = True`, etc.) control postseason mode.

```
W2W Score = Rivalry + Marketability + Competitiveness + Quality + Importance
```

The formula is tuned per sport but the structure is identical across all six leagues. Clicking any game on the site shows the full breakdown of how its score was calculated.

---

## Configuration

- **Rivalries:** Edit the rivalries list in any rating file
- **Marketability:** Team values live in the `team_marketability` dict in each rating file
- **Postseason mode:** Set `march_madness = True`, `playoffs = True`, etc. in the relevant rating files when postseason starts
- **Timezone:** Defaults to US/Eastern, detected automatically from the browser via `Intl.DateTimeFormat`, can be overridden with `?tz=` query param
- **Digest time:** Change the cron schedule in `vercel.json` (currently `0 13 * * *` = 8am ET)
- **Digest size:** Change the `[:10]` slice in `daily_digest.py` to send more or fewer games

---

## Records Section

- We have a whole webpage dedicated to the top ranked games of all time. As I write this, UNC vs Duke are playing and will most likely hold that coveted spot for a while.
---

## What We Are Still Working On

- Fixing: Live score shows "Not Started" during halftime and period breaks
- Adding: More leagues (email us to give us suggestions), and when events such as the World Cup happens, have a rating system for that as well.

---

## Credits

Game data from ESPN's public scoreboard APIs. Betting odds from DraftKings Sportsbook. Email delivery by Resend. Subscriber storage by Supabase.

---

## Contact

Charles Gifford — giffor@bc.edu  
Vic Ganson — gansonv@bc.edu
