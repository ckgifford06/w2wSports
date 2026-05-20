# W2W Sports

**Live site: [w2w-sports.com](https://w2w-sports.com)**

W2W stands for What-2-Watch. Instead of scrolling through a full day of sports schedules trying to figure out what to actually watch, this site does that math for you and ranks the top 10 games of the day by how good they are likely to be.

Built in October 2025 because we kept having the same problem as sports fans: too many games, not enough time, and no good way to know which ones were actually worth sitting down for.

(Readme was last updated in: May 20)

---

<img width="1512" height="857" alt="Screenshot 2026-05-20 at 6 50 32 PM" src="https://github.com/user-attachments/assets/4cad4c78-18d5-4107-9fc6-64ae19bea0ce" />

<img width="1512" height="858" alt="Screenshot 2026-05-20 at 6 50 54 PM" src="https://github.com/user-attachments/assets/5747dd78-2a74-4cc1-b718-eddbca43ed38" />

<img width="1512" height="855" alt="Screenshot 2026-05-20 at 6 51 06 PM" src="https://github.com/user-attachments/assets/cfe2793e-6eeb-42db-9fc8-671920df349d" />

---

## What It Does

Every day the site pulls the full schedule for every supported league from ESPN's public API, runs each game (or fight) through our scoring algorithm, and displays the top 10 results ranked from best to worst. Each game shows the start time, broadcast network, moneyline, spread, and live score once the game starts.

Users can filter by league, which switches from the global top 10 to all games in that league sorted by score. Click NBA and you see every basketball game that day ranked, even ones that did not crack the overall top 10.

Subscribers receive a daily email digest at 9:30am ET with the top 10 matchups for the day.

Supported leagues: NBA, WNBA, NFL, NHL, MLB, CFB (college football), CBB (college basketball), EPL (English Premier League), UCL (UEFA Champions League), and MMA/UFC.

---

## Pages

- **/** — Homepage. Top 10 matchups today, filterable by league, with live score polling every 30 seconds and a Live Now banner when a top game is in progress. Includes email signup.
- **/calendar** — 7-Day Rivalry Calendar. Browse any day in the next week. Games load lazily per day — clicking a tab fetches that day's full schedule and ranks it instantly.
- **/records** — Top 25 highest-rated games tracked since 03/07/26, filterable by league.
- **/formula** — Explains the W2W scoring algorithm in detail.
- **/about** — About the project and the team.
- **/install** — PWA installation guide.
- **/confirm** — Email subscription confirmation landing page.
- **/unsubscribe** — Removes a user from the daily digest. Linked from every email footer.
- **/privacy** — Privacy policy.
- **/terms** — Terms of service.
- **/game/<event_id>** — Per-game share page with a custom 1200×630 OG image, used when a game link is shared on social media.

---

## How It Is Built

This is a full-stack web application. The backend is Python on Flask, the frontend is HTML, CSS, and vanilla JavaScript with Jinja2 templating.

**Backend (Python + Flask)**

Flask receives each request, fetches and scores the games, and returns a finished HTML page. Routes in `app.py`:

- `GET /` — Homepage
- `GET /calendar` — 7-day calendar page
- `GET /records` — Top 25 all-time games, filterable by league
- `GET /about` — About page
- `GET /formula` — Formula page
- `GET /install` — PWA install guide
- `GET /privacy` — Privacy policy
- `GET /terms` — Terms of service
- `GET /game/<event_id>` — Per-game share page with custom OG meta tags pointing to a generated share card
- `GET /sitemap.xml` — Dynamically generated XML sitemap
- `GET /robots.txt` — Robots file pointing to sitemap
- `GET /sw.js` — Service worker with a date-versioned cache key to prevent stale PWA caches
- `GET /confirm?token=` — Confirms a pending email subscription
- `GET /unsubscribe?email=` — Removes an email from Supabase and shows confirmation
- `POST /api/subscribe` — Accepts a JSON body with an email field, adds a pending subscriber, and sends a confirmation email
- `GET /api/live?tz=` — Returns live score data for today's games as JSON. Polled every 30 seconds by the frontend.
- `GET /api/games?date=YYYYMMDD&tz=` — Returns all scored games for any given date as JSON. Used by the calendar page for lazy loading.
- `GET /api/game-details?event_id=&league_path=` — Fetches injury data for a specific game from ESPN's summary endpoint.
- `GET /api/share-card/<event_id>.png` — Returns a 1200×630 PNG share card for a given game. Cached on disk.
- `GET /api/save-scores?token=` — Vercel Cron endpoint. Saves yesterday's final game scores to Supabase for the records page.
- `GET /api/send-digest?token=` — Vercel Cron endpoint. Fetches today's games, builds the email, and sends to all confirmed subscribers. Protected by a secret token.

All game-fetching logic lives in a single shared `fetch_games_for_date(date_str, local_tz)` function. The homepage, calendar endpoint, and digest all call it — no duplicated ESPN logic.

The rating logic lives in separate modules, one per sport: `NBArating.py`, `WNBArating.py`, `NFLrating.py`, `NHLrating.py`, `MLBrating.py`, `CFBrating.py`, `CBBrating.py`, `EPLrating.py`, `UCLrating.py`, and `MMArating.py`. Each has a `calculate_score()` function and a `calculate_score_breakdown()` function. The breakdown returns a dict of all five components, which the frontend uses to render the animated score breakdown bars.

**Game Descriptions**

Each game card displays a short contextual blurb. For completed games, this is pulled directly from ESPN's headline field. For upcoming games, `generate_fallback_blurb()` in `app.py` generates a sentence based on records, rankings, rivalry score, win percentage, conference, and postseason context. The fallback logic handles undefeated teams, hot/struggling teams, ranked matchups, close records, and rivalry games.

**Share Card Generator**

`share_cards.py` builds 1200×630 PNG share cards on demand using Pillow. When someone shares a `/game/<event_id>` link on Twitter/X, iMessage, Slack, or anywhere else that respects Open Graph meta tags, the link unfurls into a custom card showing both teams, their records, the matchup time, the W2W Score, and the league branding.

Cards are cached to disk on first generation and served as static PNGs on every subsequent request. The cache key includes the event ID and a hash of the matchup state so cards regenerate automatically if records or scores change. The per-game page sets `og:image`, `og:title`, `og:description`, and `twitter:card` to `summary_large_image` so the unfurl renders at full width.

This was built as a growth lever: most game discussion happens in group chats and social posts, and a generic OG image gets ignored. A branded card with the actual matchup is far more clickable.

**Email Subscription (Double Opt-In)**

The subscription system uses a two-step confirmation flow. When a user submits their email, `add_pending_subscriber()` writes their address and a UUID token to a `pending_subscribers` table in Supabase, then `send_confirmation_email()` sends them a confirmation link via Resend. Clicking the link hits `/confirm?token=`, which calls `confirm_subscriber()` — this moves the email to the confirmed `subscribers` table and deletes the pending record. Only confirmed subscribers receive the daily digest.

`subscribe.py` manages all Supabase and Resend interactions: inserting pending and confirmed subscribers, confirming via token, fetching the full subscriber list, sending emails, saving game scores to the records table, and trimming old records.

`daily_digest.py` contains the email template and the `run_digest()` function. It fetches today's top 10 games, builds a full HTML email styled to match the site, and calls `subscribe.py` to send it. It can also be run directly from the command line for testing.

**Records System**

A `game_scores` table in Supabase stores final game data after each day ends. The `/api/save-scores` cron runs at midnight ET, fetches yesterday's completed games, and writes them to Supabase via `save_game_scores()`. `get_top_games()` reads back the top 25 all-time by W2W Score with optional league filtering. `trim_game_scores()` keeps the table from growing unbounded by dropping scores below the top 100.

**Cron Jobs**

Two Vercel Cron jobs run daily via `vercel.json`:

- `0 13 * * *` (9am ET) — `/api/send-digest` fires the daily email
- `0 5 * * *` (midnight ET) — `/api/save-scores` records yesterday's final scores

Both endpoints are protected by `CRON_SECRET` and also accept Vercel's native `x-vercel-cron` header so the cron jobs themselves don't need a token.

**External Services**

- **ESPN Public API** — Game schedules, scores, odds, broadcasts, leaders, and injury data across all team leagues plus MMA/UFC fight cards. No API key required.
- **Supabase** — Postgres in the cloud. Stores confirmed subscribers, pending subscribers, and historical game scores. Accessed via Supabase's REST API from Python using `requests`.
- **Resend** — Email delivery. Sends confirmation emails and the daily digest. Free tier supports up to 3,000 emails per month.
- **Pillow (PIL)** — Server-side image generation for share cards.

**Templating (Jinja2)**

All pages extend `base.html` via template inheritance. The base template contains the nav, fonts, global CSS variables, and Open Graph / meta tags. Individual pages override `{% block title %}`, `{% block og_title %}`, `{% block og_description %}`, `{% block og_url %}`, and `{% block og_image %}` for per-page SEO. The per-game share pages override `og_image` to point at the generated share card.

**Frontend (HTML, CSS, JavaScript)**

The league filter is entirely client-side. All games are rendered into the page on load with `data-league` and `data-overall-rank` attributes. Clicking a filter pill toggles visibility without a server round-trip. The header title updates dynamically to reflect the current filter and game count.

Live scores use `setInterval` polling every 30 seconds against `/api/live`. Matches are found by `data-matchup` attribute rather than index so updates are stable even if game order changes.

The score breakdown chart animates on expand using CSS transitions. Bars start at `width: 0%` and transition to their real percentage when the row opens, resetting when it closes.

Each game card can expand to show game leaders (passing yards, points, goals, etc.) pulled from the ESPN scoreboard response, and an injury report for key players listed as Out or Doubtful, fetched on-demand from `/api/game-details`.

For MMA/UFC, the card layout adapts: instead of team records and broadcasts, fight cards show the two fighters, their professional records, weight class, title bout flag if applicable, and the event card position (main event, co-main, prelims).

The 7-day calendar builds date tabs dynamically in JavaScript. Clicking a tab calls `/api/games` for that date. The other six days are prefetched in the background just to populate the game count badge — no full data load until the tab is clicked.

**Progressive Web App (PWA)**

The site ships as a PWA. `static/sw.js` is a service worker that caches static assets for offline use. The cache key is date-versioned at runtime (`w2w-YYYYMMDD`) via the `/sw.js` route so deployments always bust stale caches. `static/icon-192.png` and `static/icon-512.png` are the PWA icons. The `/install` page provides installation instructions for iOS and Android.

**SEO**

`/sitemap.xml` is generated dynamically at request time with today's date as the `<lastmod>` value for every page. `/robots.txt` points crawlers to the sitemap and allows all paths.

**Styling**

Dark theme throughout: `#0d0d0d` background, `#98002E` crimson, `#BC9B6A` gold. Fonts: Bebas Neue for display, DM Sans for body, DM Mono for data/labels. Fully responsive with breakpoints at 768px and 480px.

**Hosting**

The site runs on Vercel.

---

## The Scoring Algorithm

Every game gets a W2W Score from five components:

**Rivalry (0-12 pts):** Hard-coded per matchup based on historical rivalry intensity. Duke vs. UNC is a 12. Two teams with no history are a 0. For MMA/UFC, this reflects fighter history — previous bouts, public feuds, and stylistic grudges.

**Marketability (10-20 pts):** Reflects team popularity and national following. Set manually per team. Lakers vs. Celtics scores much higher than two small-market teams. For UCL, European giants like Real Madrid and Bayern carry top marketability. For MMA, this is per-fighter and weighted heavily for champions and PPV draws.

**Competitiveness (0-6.67 pts):** Dynamic. The closer the two teams' win-loss records, the higher this score. Evenly matched teams tend to produce better games. For MMA, this uses fighter records and odds spread.

**Quality of Play (0-8.5 pts):** Dynamic. Based on combined win percentage. Two good teams score higher than two bad teams.

**Importance (0-14 pts regular season, higher in postseason):** Accounts for season context. Late-season games with playoff implications score higher. Conference tournaments and playoffs get a significant boost. UCL knockout rounds and finals get the full postseason multiplier. MMA title fights and main events get a fixed importance bonus. Flags in each rating module (`march_madness = True`, `playoffs = True`, `ucl_knockouts = True`, etc.) control postseason mode.

```
W2W Score = Rivalry + Marketability + Competitiveness + Quality + Importance
```

The formula is tuned per sport but the structure is identical across all ten leagues. Clicking any game on the site shows the full breakdown of how its score was calculated.

---

## Configuration

- **Rivalries:** Edit the rivalries list in any rating file
- **Marketability:** Team or fighter values live in the `team_marketability` (or `fighter_marketability`) dict in each rating file
- **Postseason mode:** Set `march_madness = True`, `playoffs = True`, `ucl_knockouts = True`, etc. in the relevant rating files when postseason starts
- **Timezone:** Defaults to US/Eastern, detected automatically from the browser via `Intl.DateTimeFormat`, can be overridden with `?tz=` query param
- **Digest time:** Change the cron schedule in `vercel.json` (currently `0 13 * * *` = 9am ET)
- **Digest size:** Change the `[:10]` slice in `daily_digest.py` to send more or fewer games
- **Records table size:** Change the `keep` argument in the `trim_game_scores()` call inside `/api/save-scores` (currently 100)
- **Share card cache:** Clear `/tmp/share_cards/` (or whichever cache dir is configured) to force regeneration

---

## What We Are Still Working On

- Fixing: Live score shows "Not Started" during halftime and period breaks
- Adding: More leagues (email us with suggestions), and special rating systems for events like the World Cup
- Building: Twitter/X bot that auto-posts the top game of the day with its generated share card

---

## Credits

Game data from ESPN's public scoreboard APIs. Betting odds from DraftKings Sportsbook. Email delivery by Resend. Subscriber storage and game records by Supabase. Share cards generated with Pillow.

---

## Contact

Charles Gifford — giffor@bc.edu (charliegifford.com)
Vic Ganson — gansonv@bc.edu
