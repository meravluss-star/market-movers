# Market Movers — Daily Top 10 Most Active US Stocks

A friendly, mobile-first page in English that shows the 10 most actively traded US stocks of the last trading day. For each one it shows whether it went up or down, the news that may explain the move, and a short description of the company. Data comes from **Alpha Vantage** and updates automatically after every trading day, within the Alpha Vantage free plan.

**Live page:** https://meravluss-star.github.io/market-movers/

**Status:** Working demo hosted on GitHub Pages. The full spec is in [spec.md](spec.md).

## Features

- **Top 10 most active stocks**: ranked by share volume. ETFs, warrants and shares under $0.50 are left out.
- **Clear up/down marking**: green ▲ with + for gains, red ▼ with − for losses (never color alone), with % change, $ change and price.
- **Bold names**: ticker and company name in bold on every card.
- **Why it moved**: up to 3 news headlines per stock from Alpha Vantage, with source, date and news sentiment (Bullish … Bearish); each opens the article.
- **About the company**: a 1–2 sentence description, exchange, sector, industry and market cap.
- **Summary tiles**: number of gainers and losers, top gainer and top loser.
- **Filter and sort**: All / Gainers / Losers; sort by volume, biggest gain, biggest loss, price or ticker.
- **Mobile friendly**: one column on phones and tablets, two columns on desktop, white background, touch targets of at least 56 px.
- **Automatic daily update**: a GitHub Actions job runs Monday–Friday at 22:30 UTC (after the US close), fetches the data and commits it, which updates the live page.
- **Stays on the free plan**: at most 20 Alpha Vantage requests per run (free limit: 25 per day). It skips the run with 1 request if the trading day is already saved, and caches company profiles (30 days) and the ETF list (7 days).

## Setup: Alpha Vantage key

The daily job needs a free Alpha Vantage API key, stored as a GitHub repository secret (never in the code):

1. Get a free key at https://www.alphavantage.co/support/#api-key
2. Open **Settings → Secrets and variables → Actions → New repository secret** in this repository. Set the name to `ALPHA_VANTAGE_KEY` and the value to your key. You can also run `gh secret set ALPHA_VANTAGE_KEY --repo meravluss-star/market-movers` and paste the key when asked.
3. Optional: run it once now in **Actions → Update stock movers → Run workflow**.

## Limitations

- End-of-day data only, no live prices or charts. The page shows the starting data (Nov 13, 2026, marked with a yellow notice) until the first automatic run.
- The free key allows 25 requests a day **in total**. If the same key is also used elsewhere on the same day, some news or profiles may be skipped that day.
- "Why it moved" lists headlines, not a written analysis. For information only, not investment advice.
- The full list is in the spec's **§0 Out of Scope**.

## Project files

| File | What it is |
|---|---|
| [index.html](index.html) | The dashboard (one page: HTML, CSS and JavaScript) |
| [data/latest.json](data/latest.json) | The data the page shows (written by the daily job) |
| [data/cache.json](data/cache.json) | Stock/ETF list and company profiles kept between runs |
| [scripts/update_stocks.py](scripts/update_stocks.py) | Daily update script (Python standard library only) |
| [tests/](tests/) | Tests with saved sample responses (no API key needed) |
| [.github/workflows/update-stocks.yml](.github/workflows/update-stocks.yml) | Daily schedule, tests, fetch and commit |
| [spec.md](spec.md) | Full specification |
| [practice.md](practice.md) | Working rules |
| README.md | This file: project description and features |
