# Powerball Predictor — Ensemble Lab

[![Auto-update](https://github.com/HaiNguyenEE/powerball-predictor/actions/workflows/update-data.yml/badge.svg)](https://github.com/HaiNguyenEE/powerball-predictor/actions/workflows/update-data.yml)
[![GitHub Pages](https://img.shields.io/badge/Live%20app-hainguyenee.github.io%2Fpowerball--predictor-blue)](https://hainguyenee.github.io/powerball-predictor/)

A self-contained statistical research app for US Powerball (5/69 + 1/26, ruleset since 2015-10-07).
Built as a single HTML file with embedded historical data. Open it in any browser — on laptop, phone,
or transfer to another machine and it still works offline.

**Live URL:** https://hainguyenee.github.io/powerball-predictor/

**Auto-updates** after every drawing (Mon/Wed/Sat ~10:59 PM ET) via GitHub Actions —
fetches new results from NY Open Data, rebuilds the app, and redeploys. You never have to do anything.

## ⚠️ Read this first

Powerball is a uniform i.i.d. random variable. A chi-squared goodness-of-fit test on **1.348 draws**
(2015-10-07 → present) **fails to reject H₀ uniform** at α=0.05 for both white balls
(χ²=83.98 < critical 88.25, df=68) and Powerball (χ²=23.79 < 37.65, df=25). By the
**Data Processing Inequality** (Shannon), no function of past draws can have non-zero mutual
information with the next draw. Translation: **no model can predict the next result better than
1 in 292,201,338 per ticket**.

This app exists for:

- **Statistical research and education** — see real frequency distributions, chi-squared tests,
  autocorrelation, runs tests, etc.
- **Ensemble model engineering** — implement and compare frequency, EWMA, gap, Bayesian Dirichlet,
  Markov pairwise, and smart-pick models.
- **Expected-value calculations** — given a jackpot size, compute the true EV of a ticket including
  all prize tiers.
- **Smart pick** — generates combinations that avoid popular patterns (birthdays, consecutive
  sequences, lucky numbers). This is the *only* feature with a real EV improvement — not the
  probability of winning, but the expected payout *given* a win, since you're less likely to share
  the jackpot.

If you treat this as a "system to beat Powerball", you will lose money. Don't.

## Files

```
PowerPoint/
├── README.md                 ← this file
├── update_data.py            ← refresh data + rebuild app
├── serve.py                  ← local HTTP server (LAN access)
├── share.py                  ← public URL via Cloudflare Tunnel (any network)
├── serve.command             ← double-click launcher for serve.py
├── app/
│   ├── index.html            ← the main app (PWA-enabled)
│   ├── manifest.json         ← PWA manifest
│   ├── sw.js                 ← service worker (offline support)
│   ├── icon-*.png            ← app icons (180/192/512/maskable)
│   ├── apple-touch-icon.png  ← iOS home-screen icon
│   ├── favicon.png           ← browser tab icon
│   └── template.html         ← source template
└── data/
    ├── powerball_history.json
    ├── powerball_raw.csv
    ├── analytics.json
    └── model_snapshots.log
```

## How to use

### 1. Open the app

Just double-click `app/index.html` — it opens in your default browser. Works on:

- macOS / Windows / Linux desktop browsers
- iOS Safari, Android Chrome (phone-responsive layout)
- Offline. No server, no install, no internet required after the first build.

### 2. Tabs

| Tab | What it does |
|---|---|
| **Dashboard** | Summary stats, last draw, countdown to next draw, quick smart pick, schedule. |
| **Predictions** | Generate 1–1000 top combinations under any of 8 models. Export to CSV, copy to clipboard. |
| **My Pick** | Click numbers to build your own combination. Combine with ensemble's top suggestions. Compute ensemble score + true EV. |
| **Analytics** | Heatmaps of white & PB frequency, sum distribution, overdue numbers, statistical test panel. |
| **History** | Search the full 1.348-draw history by date or by number. |
| **Models** | Adjust ensemble weights (sliders), save model snapshots, auto-tune via backtesting, refresh data. |
| **Math** | Full mathematical specification of every model. |

### 3. Update with new draws

The app auto-detects when its embedded data is stale. To pull new draws after a Mon/Wed/Sat drawing:

**Option A — in the app:** Models → Data refresh → "Check for new results".
Fetches from NY Open Data directly in the browser. Persists in `localStorage`.

**Option B — via Python script:**

```bash
cd "/Volumes/Extreme SSD 1/Clauds/PowerPoint"
python3 update_data.py
```

This refreshes `data/powerball_history.json` and rebuilds `app/index.html` with the new data
baked in. Use this if you want the data to survive `localStorage` clears.

### 4. Share with anyone, on any device, any network

Three options, pick by use case:

**Option A — Public URL (RECOMMENDED for phones / sending to friends)**

```bash
cd "/Volumes/Extreme SSD 1/Clauds/PowerPoint"
python3 share.py
```

This starts a Cloudflare Quick Tunnel (free, no signup) and prints a public URL like
`https://wandering-anchor-1234.trycloudflare.com/app/index.html`. Share that link with
anyone — they open it in any browser, on any network, anywhere in the world. The script
also prints a QR code if `qrcode` is installed (`pip3 install qrcode`).

Auto-installs `cloudflared` on first run via Homebrew or direct binary download. URL
changes every time you run the script — for a permanent URL, deploy to GitHub Pages,
Netlify, Vercel, or Cloudflare Pages (any static host works).

Press Ctrl+C to stop sharing.

**Option B — Same WiFi (laptop ↔ phone in your home/office)**

```bash
python3 serve.py
```

Prints a URL like `http://192.168.1.42:8080/app/index.html`. Open it on phone Safari
(same WiFi). Faster than tunnel, but requires the devices to be on the same network.

**Option C — File transfer (works for laptops; iOS phone has restrictions)**

Copy `app/` folder to another machine. On laptops: open `app/index.html`. On phones:
file:// URLs have JavaScript / localStorage restrictions — use Option A or B instead.

### 5. Install as a PWA (look-and-feel of a native app)

After opening the app on any device:

- **iPhone Safari:** tap Share (□↑) → **Add to Home Screen** → app icon appears on home
  screen, opens fullscreen with no Safari chrome.
- **Android Chrome:** menu (⋮) → **Install app** or **Add to Home screen**.
- **Mac Safari (Sonoma+):** File → **Add to Dock**.
- **Chrome desktop:** address bar → install icon (⊕) → **Install**.

Once installed:
- Custom app icon (red-gold lottery ball with "PB")
- Splash screen on launch
- Service worker caches everything — works **offline** after first load
- Looks and behaves like a native app

### 5. Model auto-update

When the app loads, it checks if today is a draw day and if it has the latest draw. If new data
is fetched, the app automatically:

1. Recomputes all frequency / gap / EWMA / Bayesian stats.
2. Creates a new model version (incrementing `STATE.modelVersion`).
3. Saves a snapshot to localStorage.
4. Shows a toast notification.

You can roll back to any previous version on the **Models** tab.

## Mathematical details

See the **Math** tab inside the app for the full specification of every formula. Quick reference:

| Model | Score formula |
|---|---|
| Frequency | `score_F(i) = freq(i) / Σ freq(j)` |
| EWMA hot | `score_H(i) = Σ_t λ^(N-t) · 𝟙[i ∈ draw_t]`, default λ=0.985 |
| Gap / Due | `score_D(i) = gap(i) / mean_gap_expected`, where mean_gap = 13.8 (whites), 26 (PB) |
| Bayesian | `score_B(i) = (1 + freq(i)) / Σ (1 + freq(j))` — Dirichlet posterior mean |
| Markov pairwise | `score_M(i \| last) = (1/5) Σ_{j ∈ last} co(i,j) / freq(j)` |
| Ensemble | `score(i) = Σ_k w_k · score_k(i)`, weights from sliders |

Combination ranking:

```
combo_score(a₁,…,a₅,b) = Σ log score(aₖ) + log score_pb(b)
top-N: take top-30 whites × top-10 PBs by score, sort by combo_score, truncate
```

EV calculation (for any ticket, jackpot J):

```
P(jackpot) = 1 / 292,201,338
EV = -$2 + J · P(jackpot) + Σ_{tier} payout(tier) · P(tier)
```

## Data source

[NY Open Data — Lottery Powerball Winning Numbers Beginning 2010](https://data.ny.gov/Government-Finance/Lottery-Powerball-Winning-Numbers-Beginning-2010/d6yy-54nr).
This is the official authoritative source; the New York State Gaming Commission publishes results
within minutes of each drawing.

## Privacy & data

Everything runs locally in your browser. No data is sent anywhere. The only outbound request the
app makes is to NY Open Data when you click "Check for new results" (this is the official lottery
data API, not a tracker).

Model versions, ensemble weights, and any newly-fetched draws are stored in browser
`localStorage`. Clearing site data wipes them; run `python3 update_data.py` to rebuild from source.

## Inspect the source

The whole app is one file: `app/index.html`. Open it in any text editor. ~3.500 lines of clean
HTML + CSS + vanilla JS. No external dependencies, no minification, no obfuscation. The math is
exactly what's described in the **Math** tab — read the source to verify.

## Final reminder

> The expected return on a $2 Powerball ticket is approximately **−$1.40** under typical jackpot sizes.
> No ensemble of statistical models changes this. Play for entertainment only.
