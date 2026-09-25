"""Download Transpordiamet injury-crash open data and extract Tallinn crashes.

Source: https://avaandmed.eesti.ee/datasets/inimkannatanutega-liiklusonnetuste-andmed (CC BY 3.0)
"""
import csv
import io
import json
import urllib.request
from collections import Counter
from pathlib import Path

DATASET_API = "https://avaandmed.eesti.ee/api/datasets/slug/inimkannatanutega-liiklusonnetuste-andmed"
FALLBACK_URL = "https://pilv.transpordiamet.ee/s/Iiee4OAYFq4lT1v/download?path=%2F&files=lo_2011_2026.csv"
UA = {"User-Agent": "Mozilla/5.0 (compatible; tallinn-crashes)"}
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "official"

FIELDS = {
    "Juhtumi nr": "case_id",
    "Toimumisaeg": "time",
    "Hukkunuid": "killed",
    "Vigastatuid": "injured",
    "Sõidukeid": "vehicles",
    "Tänav": "street",
    "Maja nr": "house_nr",
    "Ristuv tänav": "cross_street",
    "Asustusüksus": "district",
    "Liiklusõnnetuse liik": "type",
    "Liiklusõnnetuse liik (detailne)": "type_detail",
    "Jalakäija osalusel": "pedestrian",
    "Jalgratturi osalusel": "cyclist",
    "Kergliikurijuhi osalusel": "light_vehicle",
    "X koordinaat": "lest_x",
    "Y koordinaat": "lest_y",
}


def csv_url():
    """Find the current CSV link; the file name changes each year (lo_2011_YYYY.csv)."""
    try:
        with urllib.request.urlopen(urllib.request.Request(DATASET_API, headers=UA), timeout=60) as r:
            d = json.load(r)
        d = d.get("data", d)
        for dist in d.get("distributions", []):
            if dist.get("format") == "CSV" and dist.get("accessUrls"):
                return dist["accessUrls"][0]
    except Exception as e:
        print(f"dataset API lookup failed ({e}), using fallback URL")
    return FALLBACK_URL


def main():
    url = csv_url()
    print(f"downloading {url}")
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=300) as r:
        text = r.read().decode("utf-8-sig")

    rows = [
        {new: (row.get(old) or "").strip() for old, new in FIELDS.items()}
        for row in csv.DictReader(io.StringIO(text), delimiter=";")
        if row.get("Omavalitsus") == "Tallinn"
    ]
    if not rows:
        raise SystemExit("no Tallinn rows found - source format changed?")
    rows.sort(key=lambda r: r["time"])

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_DIR / "tallinn_crashes.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(FIELDS.values()), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    by_street = Counter(r["street"] or "(unknown)" for r in rows)
    with open(OUT_DIR / "by_street.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["street", "crashes"])
        w.writerows(by_street.most_common())

    by_year = Counter(r["time"][:4] for r in rows)
    with open(OUT_DIR / "by_year.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["year", "crashes"])
        w.writerows(sorted(by_year.items()))

    print(f"{len(rows)} Tallinn crashes, latest {rows[-1]['time']}")


if __name__ == "__main__":
    main()
