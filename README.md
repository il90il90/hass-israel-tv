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

- **193 live channels** (HLS / M3U8) — 44 Israeli plus 149 international sport
- Organized by category: Broadcast, Sport, VIVA, Reality, Music, Kids, Lifestyle, Movies, Sport Global
- **Sport 1–5** — including premium channels served through the built-in HLS
  proxy, which handles the signed token and CDN Referer for you
- Tokens refresh automatically mid-playback, so long broadcasts do not cut out
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

**193 channels · 9 folders**

### 📺 שידורי ישראל (10)
כאן 11 · כאן 11 כתוביות · קשת 12 · קשת 12 כתוביות · רשת 13 · רשת 13 כתוביות · ערוץ 14 · ערוץ 14 כתוביות · ערוץ 9 · ערוץ 10

### ⚽ ספורט (14)
ספורט 5 · ספורט 5 פלוס · ספורט 5 גולד · ספורט 5 לייב · ספורט 5 מקס · ספורט 5 סטאר · ONE 1 · ONE 2 · ONE דוקו · ONE אדג' · ספורט 1 · ספורט 2 · ספורט 3 · ספורט 4

### 🎬 VIVA (2)
VIVA · VIVA פלוס

### 🎭 ריאליטי ותוכן (2)
ארץ נהדרת · וואמוס

### 🎵 מוזיקה ובידור (3)
מיוזיק 24 · מיוזיק IL · ערוץ הקריוקי

### 🧒 ילדים (6)
יויו · לוגי · ילדותי · ג'וניור · FOMO · yes סרטים ילדים

### 🌿 לייפסטייל (5)
הידברות · פודי · ביוטיז · דייסטאר · A פלוס

### 🎥 סרטים (2)
קלאסיקות 30A · yes סרטים אקשן

### 🌍 ספורט גלובל (149)
International sport channels — football, basketball, motorsport, combat sports and more.

---

## Troubleshooting

**Sport 1–4 or other premium channels not loading**

- These channels carry a signed token that the integration resolves on demand,
  so the Home Assistant server needs outbound internet access.
- The token is refreshed automatically well before it expires, and playback
  continues across the handover. If a stream does stop, reopening the channel
  forces a fresh one.
- A channel that is off the air returns an error rather than a picture; try
  another channel to tell the two cases apart.

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
