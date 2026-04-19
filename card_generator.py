"""
W2W Sports share card generator.
Produces 1200x630 PNG cards sized for Open Graph / Twitter previews.
"""

import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import requests

# Brand tokens matching the site
BG = (13, 13, 13)
SURFACE = (22, 22, 22)
BORDER = (42, 42, 42)
TEXT = (240, 236, 228)
TEXT_MUTED = (122, 118, 112)
TEXT_DIM = (74, 71, 66)
CRIMSON = (152, 0, 46)
GOLD = (188, 155, 106)

LEAGUE_COLORS = {
    "NBA":  (201, 162, 39),
    "NFL":  (90, 161, 224),
    "NHL":  (112, 200, 240),
    "MLB":  (224, 112, 112),
    "CFB":  (160, 122, 208),
    "CBB":  (96, 200, 144),
    "EPL":  (78, 197, 165),
    "WNBA": (232, 159, 74),
    "UCL":  (107, 140, 255),
    "MMA":  (214, 69, 69),
}

W, H = 1200, 630
LOGO_CACHE = {}

_HERE = os.path.dirname(os.path.abspath(__file__))
_FONT_DIR = os.path.join(_HERE, "static", "fonts")

_FONT_REGULAR_CANDIDATES = [
    os.path.join(_FONT_DIR, "DejaVuSans.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]
_FONT_BOLD_CANDIDATES = [
    os.path.join(_FONT_DIR, "DejaVuSans-Bold.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]


def _resolve_font_path(candidates):
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


_FONT_REGULAR_PATH = _resolve_font_path(_FONT_REGULAR_CANDIDATES)
_FONT_BOLD_PATH = _resolve_font_path(_FONT_BOLD_CANDIDATES)


def _font(size, bold=False):
    path = _FONT_BOLD_PATH if bold else _FONT_REGULAR_PATH
    if path:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def _text_width(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def _fetch_logo(url, size=180):
    if not url:
        return None
    if url in LOGO_CACHE:
        return LOGO_CACHE[url]
    try:
        resp = requests.get(url, timeout=2)
        if not resp.ok:
            return None
        img = Image.open(BytesIO(resp.content)).convert("RGBA")
        img.thumbnail((size, size), Image.LANCZOS)
        LOGO_CACHE[url] = img
        return img
    except Exception:
        return None


def _draw_rounded_rect(draw, xy, radius, fill=None, outline=None, width=1):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def _truncate(text, max_chars):
    if len(text) <= max_chars:
        return text
    return text[:max_chars - 1] + "…"


def generate_card(game: dict) -> bytes:
    """
    Render a share card for one game. Returns PNG bytes.

    Expected keys in game:
      home_name, away_name, home_logo, away_logo, league, score,
      time, where_to_watch, favored, live_score, is_rivalry
    """
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Subtle top accent stripe in league color
    league = game.get("league", "")
    accent = LEAGUE_COLORS.get(league, GOLD)
    draw.rectangle([0, 0, W, 6], fill=accent)

    # Header — wordmark + league badge
    f_wordmark_w = _font(36, bold=True)
    f_wordmark_2w = _font(36, bold=False)
    draw.text((48, 38), "W", fill=CRIMSON, font=f_wordmark_w)
    w_width = _text_width(draw, "W", f_wordmark_w)
    draw.text((48 + w_width + 2, 38), "2W", fill=TEXT, font=f_wordmark_2w)
    two_w_width = _text_width(draw, "2W", f_wordmark_2w)
    f_subbrand = _font(14)
    draw.text((48 + w_width + two_w_width + 12, 52), "SPORTS", fill=TEXT_MUTED, font=f_subbrand)

    # Top-right: league pill + status
    f_meta = _font(16, bold=True)
    league_text = league or "—"
    league_w = _text_width(draw, league_text, f_meta)
    pill_x2 = W - 48
    pill_y1 = 40
    pill_h = 34
    pill_pad_x = 14
    pill_x1 = pill_x2 - (league_w + pill_pad_x * 2)
    _draw_rounded_rect(draw, (pill_x1, pill_y1, pill_x2, pill_y1 + pill_h),
                       radius=6, outline=accent, width=2)
    draw.text((pill_x1 + pill_pad_x, pill_y1 + 8), league_text, fill=accent, font=f_meta)

    # Live/Final indicator to the left of the league pill
    live = game.get("live_score", "") or ""
    status_label = ""
    status_color = TEXT_MUTED
    if live.startswith("Live score:") and "Not Started" not in live:
        status_label = "● LIVE"
        status_color = CRIMSON
    elif live.startswith("Final score:"):
        status_label = "● FINAL"
        status_color = TEXT_MUTED
    if status_label:
        sw = _text_width(draw, status_label, f_meta)
        draw.text((pill_x1 - sw - 16, pill_y1 + 8), status_label, fill=status_color, font=f_meta)

    # Separator line below header
    draw.line([(48, 100), (W - 48, 100)], fill=BORDER, width=1)

    # Teams row — logos + names
    home_name = game.get("home_name", "Home")
    away_name = game.get("away_name", "Away")
    home_logo_url = game.get("home_logo", "")
    away_logo_url = game.get("away_logo", "")

    home_logo = _fetch_logo(home_logo_url, size=160)
    away_logo = _fetch_logo(away_logo_url, size=160)

    # Teams section: away (left) "at" home (right)
    # Left half: away team; Right half: home team; "vs" divider in middle
    section_y = 150
    section_h = 220

    # Logo placement
    logo_y = section_y + (section_h - 160) // 2
    away_logo_x = 140
    home_logo_x = W - 140 - 160

    if away_logo:
        img.paste(away_logo, (away_logo_x, logo_y), away_logo)
    else:
        # Fallback circle with abbreviation
        _draw_rounded_rect(draw, (away_logo_x, logo_y, away_logo_x + 160, logo_y + 160),
                           radius=80, fill=SURFACE, outline=BORDER, width=2)

    if home_logo:
        img.paste(home_logo, (home_logo_x, logo_y), home_logo)
    else:
        _draw_rounded_rect(draw, (home_logo_x, logo_y, home_logo_x + 160, logo_y + 160),
                           radius=80, fill=SURFACE, outline=BORDER, width=2)

    # Center "VS" or live score
    f_vs = _font(42, bold=True)
    f_live = _font(56, bold=True)
    center_x = W // 2
    center_y = section_y + section_h // 2

    live_score_raw = live.replace("Live score: ", "").replace("Final score: ", "")
    show_live = (live.startswith("Live score:") and "Not Started" not in live) or live.startswith("Final score:")

    if show_live and " - " in live_score_raw:
        # live_score is stored as "home - away" but card positions are away (left) | home (right)
        parts = [p.strip() for p in live_score_raw.split(" - ", 1)]
        if len(parts) == 2:
            score_text = f"{parts[1]} - {parts[0]}"
        else:
            score_text = live_score_raw.strip()
        sw = _text_width(draw, score_text, f_live)
        draw.text((center_x - sw // 2, center_y - 30), score_text, fill=TEXT, font=f_live)
    else:
        vs_text = "vs"
        vw = _text_width(draw, vs_text, f_vs)
        draw.text((center_x - vw // 2, center_y - 22), vs_text, fill=TEXT_DIM, font=f_vs)

    # Team names under logos
    f_team = _font(28, bold=True)
    away_display = _truncate(away_name, 22)
    home_display = _truncate(home_name, 22)

    away_name_w = _text_width(draw, away_display, f_team)
    home_name_w = _text_width(draw, home_display, f_team)

    draw.text((away_logo_x + 80 - away_name_w // 2, section_y + section_h + 8),
              away_display, fill=TEXT, font=f_team)
    draw.text((home_logo_x + 80 - home_name_w // 2, section_y + section_h + 8),
              home_display, fill=TEXT, font=f_team)

    # Rivalry badge (if applicable) — centered between team names
    if game.get("is_rivalry"):
        f_rivalry = _font(16, bold=True)
        badge_text = "RIVALRY MATCH"
        bw = _text_width(draw, badge_text, f_rivalry)
        badge_pad = 14
        badge_y = section_y + section_h + 48
        badge_h = 28
        _draw_rounded_rect(draw,
                           (center_x - bw // 2 - badge_pad, badge_y,
                            center_x + bw // 2 + badge_pad, badge_y + badge_h),
                           radius=4, fill=SURFACE, outline=GOLD, width=1)
        draw.text((center_x - bw // 2, badge_y + 6), badge_text, fill=GOLD, font=f_rivalry)

    # Bottom band — W2W Score on the left, details on the right
    band_y = 450
    draw.line([(48, band_y), (W - 48, band_y)], fill=BORDER, width=1)

    # W2W Score (left side, prominent)
    f_score_label = _font(14, bold=True)
    f_score_num = _font(72, bold=True)
    f_score_unit = _font(18)

    draw.text((48, band_y + 20), "W2W SCORE", fill=TEXT_MUTED, font=f_score_label)
    score_val = game.get("score", 0)
    score_text = f"{score_val}"
    draw.text((48, band_y + 40), score_text, fill=accent, font=f_score_num)
    sw_num = _text_width(draw, score_text, f_score_num)
    draw.text((48 + sw_num + 10, band_y + 88), "pts", fill=TEXT_MUTED, font=f_score_unit)

    # Right side details stack: time, network, moneyline
    f_detail_label = _font(11, bold=True)
    f_detail_value = _font(18, bold=True)
    detail_x = 620
    detail_y = band_y + 22

    time_val = game.get("time", "") or "TBD"
    network_val = game.get("where_to_watch", "") or "—"
    if network_val == "No networks...":
        network_val = "—"
    ml_val = game.get("favored", "") or ""
    if ml_val == "No moneyline" or not ml_val:
        ml_val = "—"

    details = [
        ("KICKOFF", time_val),
        ("WHERE TO WATCH", _truncate(network_val, 36)),
        ("MONEYLINE", _truncate(ml_val, 36)),
    ]
    row_h = 42
    for i, (lbl, val) in enumerate(details):
        y = detail_y + i * row_h
        draw.text((detail_x, y), lbl, fill=TEXT_DIM, font=f_detail_label)
        draw.text((detail_x, y + 14), val, fill=TEXT, font=f_detail_value)

    # Footer domain
    f_foot = _font(14, bold=True)
    domain = "w2w-sports.com"
    dw = _text_width(draw, domain, f_foot)
    draw.text((W - 48 - dw, H - 36), domain, fill=TEXT_MUTED, font=f_foot)

    # Export
    buf = BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
