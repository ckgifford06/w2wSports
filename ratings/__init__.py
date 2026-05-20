def get_rating_module(league):
    if league == "NBA":
        from . import NBArating
        return NBArating
    elif league == "NFL":
        from . import NFLrating
        return NFLrating
    elif league == "NHL":
        from . import NHLrating
        return NHLrating
    elif league == "MLB":
        from . import MLBrating
        return MLBrating
    elif league == "CFB":
        from . import CFBrating
        return CFBrating
    elif league == "CBB":
        from . import CBBrating
        return CBBrating
    elif league == "EPL":
        from . import EPLrating
        return EPLrating
    elif league == "WNBA":
        from . import WNBArating
        return WNBArating
    elif league == "UCL":
        from . import UCLrating
        return UCLrating
    elif league == "MMA":
        from . import MMArating
        return MMArating
    return None
