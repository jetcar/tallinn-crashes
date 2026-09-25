# Tallinn crashes

Hourly GitHub Action collecting where car crashes happen in Tallinn. Results: [REPORT.md](REPORT.md).

| Source | Data | Frequency | Files |
|---|---|---|---|
| [Transpordiamet open data](https://avaandmed.eesti.ee/datasets/inimkannatanutega-liiklusonnetuste-andmed) (CC BY 3.0) | Police-registered crashes **with injuries**, 2011–now, street + coordinates (L-EST97) | Source updates ~monthly; checked daily | `data/official/` |
| Waze for Cities feed | Driver-reported `ACCIDENT` alerts (all crashes, unverified) | Hourly | `data/waze/` |

## Why not scrape the Waze live map?

`waze.com/live-map/api/georss` requires a reCAPTCHA Enterprise token on every request, so it can't be
polled from CI without circumventing bot protection (and Waze's terms). The Waze for Cities partner
feed returns the same alert data legitimately.

## Enabling the Waze feed

1. Join [Waze for Cities](https://www.waze.com/wazeforcities) (free for public agencies/partners) or ask
   Tallinna Transpordiamet for access to their feed.
2. Copy the partner feed JSON URL (the one returning `{"alerts": [...]}`).
3. Add it as repository secret `WAZE_FEED_URL`:
   `gh secret set WAZE_FEED_URL`

Until the secret is set, the Waze step is skipped.

## Run locally

```bash
python scripts/official.py
WAZE_FEED_URL=... python scripts/waze_feed.py
python scripts/report.py
```
