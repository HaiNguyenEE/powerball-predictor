#!/usr/bin/env python3
"""
update_data.py — Refresh Powerball history data and rebuild the HTML app.

Usage:
    python3 update_data.py              # Fetch latest + rebuild
    python3 update_data.py --no-fetch   # Just rebuild from existing JSON
    python3 update_data.py --check      # Show diff, don't write

Data source: NY Open Data (official, daily refresh) — https://data.ny.gov/Government-Finance/Lottery-Powerball-Winning-Numbers-Beginning-2010/d6yy-54nr

The 5/69 + 1/26 ruleset has been in effect since 2015-10-07. Earlier draws
use different ball pools and are filtered out automatically.
"""

import json
import csv
import re
import os
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
DATA = ROOT / "data"
APP = ROOT / "app"
DATA.mkdir(exist_ok=True)
APP.mkdir(exist_ok=True)

NY_URL = "https://data.ny.gov/resource/d6yy-54nr.csv?$limit=10000&$order=draw_date%20DESC"
CUTOFF = datetime(2015, 10, 7)
RAW_CSV = DATA / "powerball_raw.csv"
HISTORY_JSON = DATA / "powerball_history.json"
ANALYTICS_JSON = DATA / "analytics.json"
TEMPLATE = APP / "template.html"
OUTPUT = APP / "index.html"


def fetch():
    print(f"→ Fetching from NY Open Data…")
    req = urllib.request.Request(NY_URL, headers={"User-Agent": "powerball-predictor/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read().decode("utf-8")
    RAW_CSV.write_text(data)
    print(f"  wrote {RAW_CSV}  ({len(data):,} bytes)")


def parse():
    rows = []
    with RAW_CSV.open("r") as f:
        reader = csv.DictReader(f)
        for r in reader:
            date = datetime.fromisoformat(r["draw_date"].replace("Z", ""))
            if date < CUTOFF:
                continue
            nums = [int(x) for x in r["winning_numbers"].split()]
            if len(nums) != 6:
                continue
            whites = sorted(nums[:5])
            pb = nums[5]
            if not (all(1 <= w <= 69 for w in whites) and 1 <= pb <= 26):
                continue
            rows.append({
                "date": date.strftime("%Y-%m-%d"),
                "whites": whites,
                "powerball": pb,
                "multiplier": int(r["multiplier"]) if r["multiplier"] else None,
            })
    rows.sort(key=lambda x: x["date"])
    return rows


def analytics(draws):
    """Compute chi-squared, frequency, gap stats."""
    from collections import Counter
    N = len(draws)
    w_freq, p_freq = Counter(), Counter()
    for d in draws:
        for w in d["whites"]:
            w_freq[w] += 1
        p_freq[d["powerball"]] += 1
    exp_w = N * 5 / 69
    exp_p = N / 26
    chi_w = sum((w_freq[i] - exp_w) ** 2 / exp_w for i in range(1, 70))
    chi_p = sum((p_freq[i] - exp_p) ** 2 / exp_p for i in range(1, 27))
    # Gaps
    last_w = {i: None for i in range(1, 70)}
    last_p = {i: None for i in range(1, 27)}
    for idx, d in enumerate(draws):
        for w in d["whites"]:
            last_w[w] = idx
        last_p[d["powerball"]] = idx
    return {
        "meta": {"N": N, "first": draws[0]["date"], "last": draws[-1]["date"]},
        "white_freq": {str(i): w_freq[i] for i in range(1, 70)},
        "pb_freq": {str(i): p_freq[i] for i in range(1, 27)},
        "chi2_white": chi_w,
        "chi2_pb": chi_p,
        "exp_w": exp_w,
        "exp_p": exp_p,
        "uniform_white_ok": chi_w < 88.25,   # critical α=0.05, df=68
        "uniform_pb_ok": chi_p < 37.65,      # critical α=0.05, df=25
    }


def build_html(draws, generated_at=None):
    if not TEMPLATE.exists():
        print(f"✗ template.html missing at {TEMPLATE}")
        sys.exit(1)
    data = {
        "meta": {
            "generatedAt": generated_at or datetime.now().isoformat(),
            "first": draws[0]["date"],
            "last": draws[-1]["date"],
            "n": len(draws),
        },
        "draws": draws,
    }
    data_json = json.dumps(data, separators=(",", ":"))
    tmpl = TEMPLATE.read_text()
    out = tmpl.replace("__DATA_PLACEHOLDER__", data_json)
    OUTPUT.write_text(out)
    print(f"  wrote {OUTPUT}  ({len(out):,} bytes)  ({len(draws)} draws embedded)")


def main():
    args = set(sys.argv[1:])
    do_fetch = "--no-fetch" not in args
    check_only = "--check" in args

    # Load existing
    old_draws = []
    if HISTORY_JSON.exists():
        old_draws = json.loads(HISTORY_JSON.read_text())
        print(f"→ Existing: {len(old_draws)} draws  ({old_draws[0]['date']} → {old_draws[-1]['date']})")

    if do_fetch:
        fetch()
        new_draws = parse()
    else:
        if not old_draws:
            print("✗ --no-fetch but no existing JSON to read from")
            sys.exit(1)
        new_draws = old_draws

    # Diff
    old_dates = {d["date"] for d in old_draws}
    added = [d for d in new_draws if d["date"] not in old_dates]
    print(f"→ Parsed: {len(new_draws)} draws  (+{len(added)} new since last run)")
    for d in added[-5:]:
        print(f"   + {d['date']}  whites {d['whites']}  PB {d['powerball']}  ×{d['multiplier']}")

    if check_only:
        print("→ --check: no files written")
        return

    # Save JSON + analytics
    HISTORY_JSON.write_text(json.dumps(new_draws, indent=2))
    print(f"  wrote {HISTORY_JSON}")
    stats = analytics(new_draws)
    ANALYTICS_JSON.write_text(json.dumps(stats, indent=2))
    print(f"  wrote {ANALYTICS_JSON}  (χ² white={stats['chi2_white']:.2f}  PB={stats['chi2_pb']:.2f})")

    # Rebuild HTML.
    # generatedAt means "when this data was produced", not "when this script last
    # ran". Stamping datetime.now() on every run made app/index.html differ by that
    # one string even when no draw was added, so the workflow's "no new draws"
    # check never fired and all 5 scheduled attempts committed, pushed and
    # triggered a Pages build. When nothing was added, reuse the timestamp already
    # embedded in the previous build so the file comes out byte-identical.
    prev_ts = None
    if not added and OUTPUT.exists():
        m = re.search(r'"generatedAt":"([^"]+)"', OUTPUT.read_text())
        if m:
            prev_ts = m.group(1)
    build_html(new_draws, prev_ts)

    # Print model snapshot reminder
    if added:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        snap_file = DATA / "model_snapshots.log"
        with snap_file.open("a") as f:
            f.write(f"{ts}  +{len(added)} new draws  N={len(new_draws)}  χ²={stats['chi2_white']:.2f}\n")
        print(f"  appended {snap_file}")
        print(f"\n✓ Done. {len(added)} new draws added. App auto-saves model version on next load.")
    else:
        print(f"\n✓ Done. No new draws. App is up to date.")


if __name__ == "__main__":
    main()
