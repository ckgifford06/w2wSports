def get_rating_module(league):
    if league == "NBA":
        from . import nba
        return nba
    elif league == "NFL":
        from . import nfl
        return nfl
    elif league == "NHL":
        from . import nhl
        return nhl
    elif league == "MLB":
        from . import mlb
        return mlb
    elif league == "CFB":
        from . import cfb
        return cfb
    elif league == "CBB":
        from . import cbb
        return cbb
    elif league == "EPL":
        from . import epl
        return epl
    elif league == "WNBA":
        from . import wnba
        return wnba
    elif league == "UCL":
        from . import ucl
        return ucl
    elif league == "MMA":
        from . import mma
        return mma
    return None
