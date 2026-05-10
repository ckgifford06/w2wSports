import re

BO7 = {1: 2, 2: 3, 3: 5, 4: 6, 5: 7, 6: 8, 7: 10}
BO5 = {1: 3, 2: 4, 3: 6, 4: 8, 5: 10}
BO3 = {1: 5, 2: 8, 3: 10}
SINGLE = {1: 10}

ELIMINATION_BONUS = 2


def parse_game_number(series_obj, notes_list):
    if series_obj:
        gn = series_obj.get("gameNumber")
        if gn:
            try:
                return int(gn)
            except (ValueError, TypeError):
                pass
    for note in notes_list or []:
        text = note.get("headline", "") or ""
        m = re.search(r"Game\s+(\d+)", text, re.IGNORECASE)
        if m:
            return int(m.group(1))
    return None


def parse_leader_wins(summary):
    if not summary:
        return None
    m = re.search(r"(?:leads?|lead).*?(\d+)\s*[-–]\s*(\d+)", summary, re.IGNORECASE)
    if m:
        try:
            return int(m.group(1))
        except (ValueError, TypeError):
            return None
    m = re.search(r"tied\s+(\d+)\s*[-–]\s*\d+", summary, re.IGNORECASE)
    if m:
        try:
            return int(m.group(1))
        except (ValueError, TypeError):
            return None
    return None


def is_elimination(game_number, series_length, leader_wins):
    if not game_number or not series_length:
        return False
    if game_number == series_length:
        return False
    needed_to_win = (series_length // 2) + 1
    if leader_wins == needed_to_win - 1:
        return True
    return False


def playoff_bonus(game_number, series_length=7, leader_wins=None, default=8):
    if not game_number:
        return default

    if series_length == 7:
        scale = BO7
    elif series_length == 5:
        scale = BO5
    elif series_length == 3:
        scale = BO3
    elif series_length == 1:
        scale = SINGLE
    else:
        scale = BO7

    base = scale.get(game_number, default)
    if is_elimination(game_number, series_length, leader_wins):
        base += ELIMINATION_BONUS
    return base
