"""Write REPORT.md with top streets from both sources."""
import csv
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOP = 20


def read(path):
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def table(rows, count_col, total):
    out = [f"| # | Street | {count_col.capitalize()} | Share |", "|---|---|---|---|"]
    for i, r in enumerate(rows[:TOP], 1):
        n = int(r[count_col])
        out.append(f"| {i} | {r['street']} | {n} | {n / total:.1%} |")
    return "\n".join(out)


def main():
    lines = [
        "# Tallinn crash report",
        "",
        f"_Generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC_",
        "",
    ]

    crashes = read(ROOT / "data/official/tallinn_crashes.csv")
    if crashes:
        streets = read(ROOT / "data/official/by_street.csv")
        years = read(ROOT / "data/official/by_year.csv")
        lines += [
            "## Injury crashes (Transpordiamet open data)",
            "",
            f"{len(crashes)} crashes with injuries, {crashes[0]['time'][:10]} – {crashes[-1]['time'][:10]}.",
            "",
            "| Year | Crashes |",
            "|---|---|",
            *[f"| {y['year']} | {y['crashes']} |" for y in years],
            "",
            f"### Top {TOP} streets (all years)",
            "",
            table(streets, "crashes", len(crashes)),
            "",
        ]

    waze = read(ROOT / "data/waze/accidents.csv")
    lines += ["## Waze accident reports (hourly)", ""]
    if waze:
        streets = read(ROOT / "data/waze/by_street.csv")
        lines += [
            f"{len(waze)} unique accident reports since {min(r['first_seen'] for r in waze)[:10]}.",
            "",
            table(streets, "accidents", len(waze)),
            "",
        ]
    else:
        lines += ["No data yet – set the `WAZE_FEED_URL` repository secret (see README).", ""]

    (ROOT / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
