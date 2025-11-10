import requests
url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
data = requests.get(url).json()
