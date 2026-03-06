# W2W Sports

**Live site: [w2w-sports.com](https://w2w-sports.com)**

W2W stands for Worth 2 Watch. The idea is simple: instead of scrolling through a full day of sports schedules trying to figure out what to actually watch, this site does that math for you and spits out the top 10 games of the day ranked by how good they are likely to be.

We built this in October 2025 because we kept having the same problem as sports fans. Too many games, not enough time, and no good way to know which ones were actually worth sitting down for.

---


<img width="1512" height="858" alt="Screenshot 2026-03-06 at 2 38 55 PM" src="https://github.com/user-attachments/assets/53a477b6-4725-4ffa-95e9-37ac3ac35e80" />


---

## What It Does

Every day the site pulls the full schedule for every supported league from ESPN's public API, runs each game through our scoring algorithm, and displays the top 10 results ranked from best to worst. Each game shows the start time, broadcast network, moneyline, spread, live score once the game starts, and a short blurb about why it is worth watching.

Users can also filter by league, which switches the view from the global top 10 to all games in that league sorted by score. So if you only care about MLB that day, you can click the MLB filter and see every baseball game ranked, even ones that did not crack the overall top 10.

Supported leagues: NBA, NFL, NHL, MLB, CFB (college football), CBB (college basketball).

---

## How It Is Built

This is a full-stack web application. The backend is Python running on the Flask framework, and the frontend is HTML, CSS, and vanilla JavaScript with Jinja2 handling the templating.

**Backend (Python + Flask)**

Flask is a lightweight Python web framework. When someone visits the site, Flask receives the request, runs all the logic to fetch and score the games, and sends back a finished HTML page. Each route in `app.py` corresponds to a page on the site: `/` for the homepage, `/about`, and `/formula`.

The rating logic lives in separate Python modules, one per sport: `NBArating.py`, `NFLrating.py`, `NHLrating.py`, `MLBrating.py`, `CFBrating.py`, and `CBBrating.py`. Each module has a `calculate_score()` function that takes two team abbreviations and returns a W2W Score. Splitting them out by sport keeps things clean since the data from ESPN comes back slightly differently per league and the rivalry/marketability values are all sport-specific.

**Templating (Jinja2)**

Jinja2 is Flask's built-in templating engine. It lets you write HTML with placeholders like `{{ game.matchup }}` or loop through a list with `{% for game in matchups %}`. Flask fills those in with real data before the page gets sent to the browser, so the same template file generates a completely different page every single day.

All three pages (home, about, formula) extend a shared `base.html` template that contains the nav bar, fonts, and footer. This is called template inheritance. If we ever change the nav, we change it in one place and it updates everywhere.

**Frontend (HTML, CSS, JavaScript)**

The HTML defines the structure of the page. The CSS handles all the visual styling, colors, layout, and animations. JavaScript handles the interactive parts.

The league filter is entirely client-side, meaning no server request gets made when you click a pill. All games are rendered into the page as hidden HTML elements when it first loads. Each game div has two data attributes on it: `data-league` and `data-overall-rank`. When you click a filter, a JavaScript function reads those attributes and toggles which rows are visible. Clicking All shows only the rows where overall rank is 1 through 10. Clicking a specific league shows all rows where the league matches. The header title also updates dynamically.

Live scores work through AJAX polling. Every 30 seconds a JavaScript `setInterval` fires, hits the `/api/live` endpoint on the server, gets back fresh score data as JSON, and updates just the score elements on the page without doing a full reload.

**Hosting**

The site runs on Vercel, which handles deployment and serves the Flask app.

---

## The Scoring Algorithm

Every game gets a W2W Score made up of five components.

**Rivalry Value (0-12 points):** Hard-coded per matchup. Duke vs. UNC gets a 12. Two teams that have no history get a 0. We set these manually based on what we think the actual rivalry intensity is.

**Marketability (10-20 points):** Reflects how popular and widely followed each team is. A Lakers vs. Celtics game gets a much higher marketability score than two small-market teams. Also set manually.

**Competitiveness (0-6.67 points):** Calculated dynamically from the ESPN data. The closer the two teams' win-loss records are to each other, the higher this score. The idea is that evenly matched teams tend to produce better games.

**Quality of Play (0-8.5 points):** Also dynamic. Looks at the combined win percentage of both teams. Two good teams playing each other scores higher than two bad teams.

**Importance (0-14 points regular season, higher in postseason):** Accounts for where the game falls in the season. Late-season games with playoff implications rank higher. Conference tournaments and actual playoffs get a significant boost. There are flags in each rating module like `march_madness = True` and `playoffs = True` that you can flip on when postseason starts.

The final score is just all five of those added together. The formula is slightly tuned per sport but the structure is the same across all six leagues.

---

## Configuration

A few things that are easy to adjust:

- **Rivalries:** Edit the rivalries list in any rating file to add or change rivalry scores
- **Marketability:** Team popularity values live in the `team_marketability` dictionary in each rating file
- **Postseason mode:** Set `march_madness = True`, `playoffs = True`, etc. in the relevant rating files when tournament season starts
- **Timezone:** Defaults to US/Eastern, can be changed with a `?tz=` query parameter

---

## What We Are Still Working On

- Fixing: Betting odds disappear when a game goes live
- Fixing: Live score shows "Not Started" during halftime and period breaks
- Adding: Daily email with that morning's top matchups
- Adding: Premier League soccer

---

## Credits

Game data from ESPN's public scoreboard APIs. Betting odds from DraftKings Sportsbook.

---

## Contact
Charles Gifford -- giffor@bc.edu
Vic Ganson -- gansonv@bc.edu
