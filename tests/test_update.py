#!/usr/bin/env python3
"""Tests for update_stocks.py using saved responses (no network, no API key).

Run: python tests/test_update.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(os.path.dirname(HERE), "scripts", "update_stocks.py")
FIXTURES = os.path.join(HERE, "fixtures")
failures = []


def run(data_dir, **env):
    full = dict(os.environ, AV_FIXTURES=FIXTURES, AV_DATA_DIR=data_dir, AV_DELAY="0")
    full.pop("ALPHA_VANTAGE_KEY", None)
    full.update(env)
    p = subprocess.run([sys.executable, SCRIPT], env=full, capture_output=True, text=True)
    print(p.stdout + p.stderr)
    return p.returncode, p.stdout


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        failures.append(msg)


def read(data_dir):
    with open(os.path.join(data_dir, "latest.json"), encoding="utf-8") as f:
        return json.load(f)


# 1. Full run with an empty data folder.
d = tempfile.mkdtemp()
code, out = run(d)
check(code == 0, "full run exits 0")
latest = read(d)
tickers = [s["ticker"] for s in latest["stocks"]]
check(tickers == ["NVDA", "ONFO", "NU", "RAIN", "FCUV", "INTC", "CRWV", "AKAN", "SPCX", "FRMI"],
      f"top 10 by volume, ETFs and sub-$0.50 shares removed: {tickers}")
check(latest["tradingDate"] == "2026-11-13", "trading date read from last_updated")
check(latest["apiCalls"] <= 20, f"stays within 20 requests (used {latest['apiCalls']})")
check(latest["seed"] is False, "seed flag is false after a real run")
nvda = latest["stocks"][0]
check(nvda["name"] == "NVIDIA Corporation" and nvda["sector"] == "TECHNOLOGY", "profile merged from OVERVIEW (the real Alpha Vantage function name)")
check(nvda["description"] == "Test company description, first sentence. Second sentence here.",
      f"description cut to two sentences: {nvda['description']!r}")
check("NEWS_SENTIMENT" not in out and all("news" not in s for s in latest["stocks"]), "no news requests and no news in the data")
check(latest["apiCalls"] == 12, f"first run: 1 movers + 1 listing + 10 profiles = 12 requests (used {latest['apiCalls']})")
check(nvda["change"] == -3.34 and nvda["changePercent"] == -2.0097, "change and percent parsed")
check(latest["stocks"][1]["name"] == "Onfolio Holdings Inc", "name falls back to the listing when no profile")
check(latest["stocks"][5]["name"] == "Intel Corp" and ": OVERVIEW CRWV" in out, "an error for one stock does not stop the run")
with open(os.path.join(d, "cache.json"), encoding="utf-8") as f:
    cache = json.load(f)
check(cache["listing"]["SOXL"][0] == "ETF" and cache["listingUpdated"], "listing cached")

# 2. Second run for the same trading day: only 1 request, data unchanged.
code, out = run(d)
check(code == 0 and "already saved" in out and "request 2/" not in out, "same-day rerun uses only 1 request")

# 3. FORCE rerun: listing and NVDA profile come from cache.
code, out = run(d, FORCE="1")
check(code == 0 and "LISTING_STATUS" not in out and "OVERVIEW NVDA" not in out,
      "cached listing and fresh profiles are not requested again")
check(read(d)["apiCalls"] <= 20, "forced run stays within budget")

# 4. Tight budget: never more requests than AV_MAX_CALLS.
d2 = tempfile.mkdtemp()
code, out = run(d2, AV_MAX_CALLS="5")
check(code == 0, "run with a 5-request budget still saves data")
check(read(d2)["apiCalls"] == 5 and "request 6/" not in out, "never goes over AV_MAX_CALLS")

# 5. Missing key outside test mode fails clearly.
d3 = tempfile.mkdtemp()
env = dict(os.environ, AV_DATA_DIR=d3)
env.pop("AV_FIXTURES", None)
env.pop("ALPHA_VANTAGE_KEY", None)
p = subprocess.run([sys.executable, SCRIPT], env=env, capture_output=True, text=True)
check(p.returncode == 1 and "ALPHA_VANTAGE_KEY" in p.stdout, "missing key gives a clear error")
check(not os.path.exists(os.path.join(d3, "latest.json")), "no data written when the key is missing")


def fixtures_with(overrides):
    """Copy of the fixtures folder with some responses replaced."""
    f = tempfile.mkdtemp()
    for name in os.listdir(FIXTURES):
        shutil.copy(os.path.join(FIXTURES, name), f)
    for name, body in overrides.items():
        with open(os.path.join(f, name), "w", encoding="utf-8") as fh:
            json.dump(body, fh)
    return f


# 6. Function refused as premium-only: asked once, then skipped for the rest of the run.
premium = {"Information": "Thank you for using Alpha Vantage! This is a premium endpoint. You may subscribe to any of the premium plans."}
f6 = fixtures_with({"OVERVIEW_NVDA.json": premium})
d6 = tempfile.mkdtemp()
code, out = run(d6, AV_FIXTURES=f6)
check(code == 0 and out.count(": OVERVIEW ") == 1, "premium-only function is requested only once per run")
check(len(read(d6)["stocks"]) == 10, "data still saved after a premium-only refusal")

# 7. Daily limit reached mid-run: no further requests, data still saved.
daily = {"Information": "We have detected your API key as XXX and our standard API rate limit is 25 requests per day."}
f7 = fixtures_with({"OVERVIEW_NVDA.json": daily})
d7 = tempfile.mkdtemp()
code, out = run(d7, AV_FIXTURES=f7)
check(code == 0 and "request 4/" not in out, "daily-limit message stops all further requests")
check(len(read(d7)["stocks"]) == 10, "data still saved after the daily limit")

# 8. Short-term (per-second) limit for one stock is not treated as the daily limit.
burst = {"Information": "Please consider spreading out your free API requests more sparingly (1 request per second). 25 requests per day."}
f8 = fixtures_with({"OVERVIEW_NVDA.json": burst})
d8 = tempfile.mkdtemp()
code, out = run(d8, AV_FIXTURES=f8)
check(code == 0 and ": OVERVIEW ONFO" in out, "per-second limit does not stop the other requests")

for x in (d, d2, d3, f6, d6, f7, d7, f8, d8):
    shutil.rmtree(x, ignore_errors=True)
print(f"\n{len(failures)} failure(s)")
sys.exit(1 if failures else 0)
