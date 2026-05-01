"""
NVI daily Twitter/X auto-post bot.

Scrapes its own deployed dashboard, picks the top peaking venues, composes
a tweet from a rotating set of templates, and posts via the X API v2.

Designed to run on a GitHub Actions cron (twice daily). Tweets at 17:30
EAT every day plus 21:00 EAT on Fri & Sat. Free tier of X API v2 covers
this volume (~50 tweets/month).

Required environment variables (set as GitHub Actions secrets):
    X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET
"""
from __future__ import annotations

import os
import random
import re
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
import tweepy

NVI_URL = "https://charles254.github.io/nairobi-vibe-index/"
EAT = ZoneInfo("Africa/Nairobi")


def fetch_venues() -> list[dict]:
    """Scrape NVI's deployed page and parse all visible venue cards."""
    html = requests.get(NVI_URL, timeout=30).text
    soup = BeautifulSoup(html, "html.parser")
    venues = []
    for card in soup.select("article.card:not(.listed)"):
        name_el = card.select_one(".card-name")
        name = name_el.get_text(strip=True) if name_el else card.get("data-name", "")
        area = card.get("data-area", "")
        cat = card.get("data-category", "")
        peak_pct = 0
        for badge in card.select(".badge"):
            m = re.search(r"(\d+)%", badge.get_text(" ", strip=True))
            if m:
                peak_pct = int(m.group(1))
                break
        score_el = card.select_one(".card-meta-row .mono")
        if score_el and not peak_pct:
            m = re.search(r"(\d+)%", score_el.get_text(strip=True))
            if m:
                peak_pct = int(m.group(1))
        peaks_now = card.select_one(".peaks-now-badge") is not None
        if name:
            venues.append({
                "name": name,
                "area": area,
                "category": cat,
                "peak_pct": peak_pct,
                "peaks_now": peaks_now,
            })
    return venues


def pick_top(venues: list[dict], n: int = 5) -> list[dict]:
    """Return up to n venues, prioritizing PEAKS NOW then highest %."""
    now = [v for v in venues if v["peaks_now"]]
    rest = sorted(
        (v for v in venues if not v["peaks_now"]),
        key=lambda v: -v["peak_pct"],
    )
    return (now + rest)[:n]


def compose(top: list[dict]) -> str:
    """Pick a template based on time of day; keep under 280 chars."""
    hour = datetime.now(EAT).hour
    is_evening = hour >= 18
    evening_templates = [
        "🌃 Tonight in Nairobi — top peaking venues:\n{lines}\n\nDrink safely. Plan a ride home 🚖\n{url}",
        "📡 NVI live — Nairobi nightlife right now:\n{lines}\n\n{url}",
        "🔥 Where's the vibe at?\n{lines}\n\nDon't drink & drive.\n{url}",
        "Friday energy meter 📈\n{lines}\n\nAll 287 venues: {url}",
    ]
    daytime_templates = [
        "☀️ Nairobi venue activity right now:\n{lines}\n\nFull index: {url}",
        "📊 NVI midday signal — busiest spots:\n{lines}\n\n{url}",
    ]
    templates = evening_templates if is_evening else daytime_templates
    fire = lambda v: "🔥" if v["peaks_now"] else "▲"
    lines = "\n".join(
        f"{fire(v)} {v['name']} ({v['area']}) — {v['peak_pct']}%"
        for v in top
    )
    text = random.choice(templates).format(lines=lines, url=NVI_URL)
    if len(text) > 280:
        text = text[:277] + "…"
    return text


def post(text: str) -> None:
    client = tweepy.Client(
        consumer_key=os.environ["X_API_KEY"],
        consumer_secret=os.environ["X_API_SECRET"],
        access_token=os.environ["X_ACCESS_TOKEN"],
        access_token_secret=os.environ["X_ACCESS_SECRET"],
    )
    client.create_tweet(text=text)


def main() -> int:
    venues = fetch_venues()
    if not venues:
        print("No venues parsed; aborting.", file=sys.stderr)
        return 1
    top = pick_top(venues, n=5)
    if not top:
        print("No top venues; aborting.", file=sys.stderr)
        return 1
    text = compose(top)
    print("Composed tweet:")
    print(text)
    if "--dry-run" in sys.argv:
        return 0
    post(text)
    print("Posted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
