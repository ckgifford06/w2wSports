from . import nba, nfl, nhl, mlb, cfb, cbb, epl, wnba, ucl, mma

_MODULES = {
    "NBA": nba, "NFL": nfl, "NHL": nhl, "MLB": mlb, "CFB": cfb,
    "CBB": cbb, "EPL": epl, "WNBA": wnba, "UCL": ucl, "MMA": mma,
}

def get_rating_module(league):
    return _MODULES.get(league)
