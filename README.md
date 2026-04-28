# Israel TV for Home Assistant

[![HACS Custom][hacs-badge]][hacs-url]
[![HA Version][ha-badge]][ha-url]
[![License: MIT][license-badge]][license-url]

Live Israeli TV channels inside Home Assistant's **Media Browser** — stream and cast to any compatible device.

---

## One-click Install

[![Add to Home Assistant][install-badge]][install-url]

> Requires [HACS](https://hacs.xyz) to be installed first.

---

## Features

- **46 live Israeli TV channels** (HLS / M3U8)
- Organized by category: Broadcast, Sport, ONE, VIVA, Kids, Lifestyle, Music, Movies
- **YES Sport 1–4** — live streams via built-in HLS proxy (no Referer issues)
- Full integration with the **Media Browser** (no extra cards needed)
- **Cast** to Chromecast, Apple TV, Roku, Smart TV, or any `media_player` entity
- No credentials, no API keys
- HACS-installable

---

## Requirements

| Requirement | Version |
|---|---|
| Home Assistant | 2024.1 or newer |
| HACS | 1.x or newer |

---

## Installation

### Method A — One-click via HACS (recommended)

Click the button above, or:

[![Add to Home Assistant][install-badge]][install-url]

### Method B — HACS Custom Repository

1. Open **HACS** in your Home Assistant sidebar.
2. Click the **three-dot menu** (⋮) in the top-right corner → **Custom repositories**.
3. Paste the repository URL:
   ```
   https://github.com/il90il90/hass-israel-tv
   ```
4. Set **Category** to `Integration` → click **Add**.
5. Search for **Israel TV** in HACS → click **Download**.
6. **Restart Home Assistant**.

### Method C — Manual

1. Download or clone this repository.
2. Copy the `custom_components/israel_tv/` folder into your HA config directory:
   ```
   /config/custom_components/israel_tv/
   ```
3. **Restart Home Assistant**.

---

## Setup

After installation and restart:

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **Israel TV**.
3. Click **Submit** — no credentials required.

The integration is now active. Open **Media** in the sidebar to browse channels.

---

## How to Cast

1. Open **Media** in the HA sidebar.
2. Navigate to **Israel TV** → choose a category → choose a channel.
3. Click the **Cast icon** and select your target device (Chromecast, Apple TV, etc.).

---

## Channel List

|---|---------|--------|--------|
**46 channels · 8 folders**

### 📺 שידורי ישראל
כאן 11 · כאן 11 HEVC · כאן 11 כתוביות · קשת 12 · קשת 12 HEVC · קשת 12 כתוביות · רשת 13 · רשת 13 HEVC · רשת 13 כתוביות · ערוץ 14 · ערוץ 14 HEVC · ערוץ 14 כתוביות · ערוץ 9

### ⚽ ספורט
ספורט 5 · ספורט 5 פלוס · ספורט 5 פלוס HEVC · ספורט 5 גולד · ספורט 5 לייב · ספורט 5 לייב HEVC · ספורט 5 מקס · ספורט 5 4K · ONE 1 · ONE 2 · ONE דוקו · ONE אדג' · ספורט 1 · ספורט 2 · ספורט 3 · ספורט 4

### 🎬 VIVA
VIVA · VIVA פלוס

### 🎭 ריאליטי ותוכן
ארץ נהדרת · וואמוס

### 🎵 מוזיקה ובידור
מיוזיק 24 · מיוזיק IL · ערוץ הקריוקי

### 🧒 ילדים
יויו · לוגי · ילדותי · ג'וניור · FOMO

### 🌿 לייפסטייל
פודי · ביוטיז · דייסטאר · A פלוס

### 🎥 סרטים
קלאסיקות 30A

---

## Troubleshooting

**YES Sport channels not loading**

- YES Sport streams are fetched dynamically from nextbet7.tv via a built-in proxy. Make sure your Home Assistant server has internet access.
- Tokens refresh automatically every 4 minutes — if a stream stops, wait a moment and try again.

**Channel not loading / buffering**

- Check that your Home Assistant server has internet access.
- Some channels may be temporarily unavailable at the CDN.

**Cast button is greyed out**

- Make sure a `media_player` entity (Chromecast, Apple TV, etc.) is set up and online in HA.
- Google Home / Chromecast integration must be configured first.

**Integration not appearing in HACS**

- Confirm the custom repository URL was added with category set to **Integration** (not Plugin).
- Clear the HACS cache: HACS → three-dot menu → Reload data.

**"already_configured" error**

- Only one instance of this integration can run at a time. Go to Settings → Integrations to check if it is already installed.

---

## License

MIT — see [LICENSE](LICENSE).

---

[hacs-badge]: https://img.shields.io/badge/HACS-Custom-orange.svg
[hacs-url]: https://hacs.xyz
[ha-badge]: https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg
[ha-url]: https://www.home-assistant.io
[license-badge]: https://img.shields.io/badge/License-MIT-yellow.svg
[license-url]: LICENSE
[install-badge]: https://my.home-assistant.io/badges/hacs_repository.svg
[install-url]: https://my.home-assistant.io/redirect/hacs_repository/?owner=il90il90&repository=hass-israel-tv&category=integration
