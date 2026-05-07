def _extract_results(team_block):
    events = team_block.get("events", [])
    results = []
    for ev in events:
        r = ev.get("gameResult") or ev.get("result")
        if r in ("W", "L", "T"):
            results.append(r)
        elif r == "OTL":
            results.append("L")
    return results


def _compute_streak(results):
    if not results:
        return None
    first = results[0]
    if first not in ("W", "L"):
        return None
    count = 1
    for r in results[1:]:
        if r == first:
            count += 1
        else:
            break
    return f"{first}{count}"


def _format_streak_summary(home_abbr, home_streak, away_abbr, away_streak):
    parts = []
    if home_streak:
        parts.append(f"{home_abbr} {home_streak}")
    if away_streak:
        parts.append(f"{away_abbr} {away_streak}")
    return " · ".join(parts)


def get_streaks(summary_data, home_abbr, away_abbr):
    last_five = summary_data.get("lastFiveGames", [])
    if not last_five:
        return None

    home_streak = None
    away_streak = None

    for block in last_five:
        team = block.get("team", {})
        abbr = team.get("abbreviation", "")
        results = _extract_results(block)
        streak = _compute_streak(results)
        if abbr == home_abbr:
            home_streak = streak
        elif abbr == away_abbr:
            away_streak = streak

    if not home_streak and not away_streak:
        return None

    return {
        "home": home_streak,
        "away": away_streak,
        "summary": _format_streak_summary(home_abbr, home_streak, away_abbr, away_streak),
    }


def get_head_to_head(summary_data):
    series_list = summary_data.get("seasonseries", [])
    if not series_list:
        return None

    first = series_list[0]
    summary = (first.get("summary") or "").strip()
    total = first.get("totalCompetitions", 0)

    if not summary and not total:
        return None

    if total == 0:
        return {"summary": "First meeting of the season", "total": 0}

    if summary:
        return {"summary": summary, "total": total}

    return None
