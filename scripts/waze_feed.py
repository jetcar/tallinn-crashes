"""Collect Waze ACCIDENT alerts in Tallinn from a Waze for Cities (Connected Citizens) partner feed.

Requires env WAZE_FEED_URL - the JSON feed URL from the Waze for Cities partner portal.
Alerts persist while active, so each run upserts by uuid and tracks first/last seen.
"""
import csv
import json
import os
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "waze"
ACCIDENTS = OUT_DIR / "accidents.csv"
# Tallinn bounding box, used when an alert has no city
BBOX = (59.35, 59.51, 24.55, 25.00)  # lat_min, lat_max, lon_min, lon_max
COLUMNS = [
    "uuid", "published", "first_seen", "last_seen", "subtype", "street", "city",
    "lat", "lon", "reliability", "confidence", "thumbs_up",
]


def in_tallinn(alert):
    city = alert.get("city") or ""
    if city:
        return "Tallinn" in city
    loc = alert.get("location") or {}
    lat, lon = loc.get("y"), loc.get("x")
    return lat is not None and BBOX[0] <= lat <= BBOX[1] and BBOX[2] <= lon <= BBOX[3]


def iso(ms):
    return datetime.fromtimestamp(ms / 1000, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    url = os.environ.get("WAZE_FEED_URL")
    if not url:
        raise SystemExit("WAZE_FEED_URL not set")
    with urllib.request.urlopen(url, timeout=60) as r:
        feed = json.load(r)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    known = {}
    if ACCIDENTS.exists():
        with open(ACCIDENTS, encoding="utf-8") as f:
            known = {row["uuid"]: row for row in csv.DictReader(f)}

    new = 0
    for a in feed.get("alerts", []):
        if a.get("type") != "ACCIDENT" or not in_tallinn(a):
            continue
        loc = a.get("location") or {}
        row = known.get(a["uuid"])
        if row is None:
            new += 1
            row = known[a["uuid"]] = {"uuid": a["uuid"], "first_seen": now}
        row.update({
            "published": iso(a["pubMillis"]) if a.get("pubMillis") else "",
            "last_seen": now,
            "subtype": a.get("subtype", ""),
            "street": a.get("street", ""),
            "city": a.get("city", ""),
            "lat": loc.get("y", ""),
            "lon": loc.get("x", ""),
            "reliability": a.get("reliability", ""),
            "confidence": a.get("confidence", ""),
            "thumbs_up": a.get("nThumbsUp", ""),
        })

    rows = sorted(known.values(), key=lambda r: r["published"] or r["first_seen"])
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(ACCIDENTS, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    by_street = Counter(r["street"] or "(unknown)" for r in rows)
    with open(OUT_DIR / "by_street.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["street", "accidents"])
        w.writerows(by_street.most_common())

    print(f"{new} new, {len(rows)} total Tallinn accident reports")


if __name__ == "__main__":
    main()
