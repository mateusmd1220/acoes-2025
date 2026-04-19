# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**acoes-2025** — A single-page Streamlit dashboard showing 2025 YTD performance for three Brazilian stocks (PETR4, ITUB4, VALE3) sourced from Yahoo Finance via `yfinance`.

## Running the app

```bash
cd acoes-2025
pip install -r requirements.txt
streamlit run app.py
```

## GitHub sync

The project is versioned in `acoes-2025/.git` and pushed to GitHub (`mateusmd1220/acoes-2025`).

A Claude Code **Stop hook** in `.claude/settings.json` automatically runs after every session ends:
```bash
cd acoes-2025 && git add -A && git diff --cached --quiet || git commit -m "auto: sync changes" && git push
```
This means every change Claude Code makes is committed and pushed when the conversation ends. No manual `git push` needed.

To create the GitHub repo for the first time (one-time setup):
```bash
# Requires a GitHub Personal Access Token with 'repo' scope
GITHUB_TOKEN=<token> curl -s -X POST https://api.github.com/user/repos \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"acoes-2025","private":false}' && \
cd acoes-2025 && git remote add origin https://github.com/mateusmd1220/acoes-2025.git && git push -u origin master
```

## Architecture

The entire app lives in `acoes-2025/app.py` — there is no backend, database, or multi-file structure.

Key design decisions:
- `load_full_year()` fetches the full 2025 calendar year once and caches it for 1 hour (`@st.cache_data(ttl=3600)`). All date filtering happens client-side on the cached DataFrames, not by re-fetching.
- `TICKERS` maps display names → Yahoo Finance symbols (`.SA` suffix for B3 stocks). Adding a new stock means adding an entry here and in `COLORS`.
- The four chart tabs (Preço Histórico, Performance Comparativa, Volume, Volatilidade) all operate on the same filtered `close` / `volume` slices derived from the cached data.
- Volatility is computed as a 21-day rolling annualised std (`* 252**0.5 * 100`).
