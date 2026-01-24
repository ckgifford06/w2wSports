# W2W Sports - What to Watch Sports (W2W-sports.com)

A web application that ranks and displays the top 10 most exciting sports matchups each day across multiple leagues. The ranking system analyzes games based on rivalry intensity, team marketability, competitiveness, quality of play, and game importance.


## What It Does
The site pulls daily game schedules from ESPN's APIs and calculates a score for each matchup. Games are ranked by their entertainment value, helping users find the best games to watch on any given day. The top 10 games are displayed with betting odds, broadcast information, and AI-generated descriptions.

**Supported Leagues**

- NBA (National Basketball Association)
- NFL (National Football League)
- NHL (National Hockey League)
- MLB (Major League Baseball)
- CFB (NCAA College Football)
- CBB (NCAA College Basketball)

## How it's made
**Tech Stack**
Backend:

Python 3.x
Flask - web framework for handling routes and rendering templates
Requests - making HTTP calls to ESPN APIs

Frontend:

HTML/CSS with Jinja2 templating
Vanilla JavaScript for interactivity
Google Analytics for traffic tracking

APIs:

ESPN Scoreboard APIs - game data, scores, odds, and broadcast info
Anthropic Claude API - generating contextual game descriptions

Hosting:

Render - deployment platform
SQLite - database for email subscriptions and blurb caching

Other:

PyTZ - timezone handling for displaying games in user's local time
SMTP - email verification system (in progress)

How the Scoring Works

Each game gets a score based on five components:

Rivalry (0-12 points): Historical matchups between teams. Duke vs UNC gets 12 points, while non-rivalry games get 0.
Marketability (10-20 points): Team popularity and media market size. Lakers, Celtics, and Duke are high value.
Competitiveness (0-6.67 points): How evenly matched the teams are based on their win-loss records. Closer records mean higher scores.
Quality of Play (0-8.5 points): Combined win percentage of both teams. Two good teams playing each other scores higher.
Game Importance (0-14 points regular season, up to 24 for tournaments): Late season games, ranked matchups, playoff implications, and tournament games all increase this score.
The formula varies slightly by sport but follows the same general structure. Each league has its own rating module (NBArating.py, CBBrating.py, etc.) with sport-specific rivalries and adjustments.

AI Blurb Generation
Game descriptions are generated using Claude AI for the top 10 ranked games only. This keeps API costs low (around $0.10/month) while still providing quality descriptions for the games that matter.
The system caches blurbs in a JSON file so each game only needs one API call per day, regardless of how many visitors the site gets. If the cache is empty or the API fails, a rule-based fallback generates descriptions using team rankings, records, and conference information.

Project Structure
/
├── app.py                 # Main Flask application
├── NBArating.py          # NBA game scoring logic
├── NFLrating.py          # NFL game scoring logic
├── NHLrating.py          # NHL game scoring logic
├── MLBrating.py          # MLB game scoring logic
├── CFBrating.py          # College football scoring logic
├── CBBrating.py          # College basketball scoring logic
├── templates/
│   ├── index.html        # Main page template
│   ├── about.html        # About page
│   └── formula.html      # Scoring methodology explanation
├── emails.db             # SQLite database
├── blurb_cache.json      # Cached AI descriptions
├── requirements.txt      # Python dependencies
└── README.md            # This file


Configuration

Timezone: The site defaults to US/Eastern but can be changed via the tz query parameter.
League Filter: Users can filter by specific leagues using the dropdown menu or by passing ?league=NBA in the URL.
Rivalry Scores: Edit the rivalries list in each rating file to add or modify rivalries.
Marketability Scores: Team popularity scores are defined in the team_marketability dictionary in each rating file.
Tournament Modes: Set march_madness = True or conference_tournament = True in CBBrating.py to boost importance scores during tournament season.
Cost Considerations
With the current caching setup, the Anthropic API costs are minimal:

10 games per day = $0.003/day
Monthly cost: ~$0.10

The site generates AI blurbs only for the top 10 games and caches them. Subsequent visitors see cached blurbs at no additional cost.
Future Features

Email subscription system with daily game recommendations
User preference saving for favorite teams and leagues
Historical game data and trending analysis
Mobile app version
Live score updates via WebSocket

Credits
Game data provided by ESPN's public APIs. Betting odds via DraftKings Sportsbook. AI descriptions powered by Anthropic Claude.

License
This is a personal project. Feel free to fork and modify for your own use.

Contact Info:
Charles Gifford (giffor@bc.edu)
Vic Ganson (gansonv@bc.edu)
