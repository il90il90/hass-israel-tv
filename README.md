# Israel TV for Home Assistant

[![HACS Custom][hacs-badge]][hacs-url]
[![HA Version][ha-badge]][ha-url]
[![License: MIT][license-badge]][license-url]

Live Israeli TV channels inside Home Assistant's **Media Browser** — stream and cast to any compatible device.

---

## Features

- 42 live Israeli TV channels (HLS / M3U8)
- Organized by category: Broadcast, Sport, ONE, VIVA, Kids, Lifestyle, Music, Movies
- Full integration with the **Media Browser** (no extra cards needed)
- **Cast** to Chromecast, Apple TV, Roku, Smart TV, or any `media_player` entity
- No credentials, no API keys
- HACS-installable

---

## Requirements

| Requirement | Version |
|---|---|
| Home Assistant | 2023.6 or newer |
| HACS | 1.x or newer |

---

## Installation

### Method A — HACS Custom Repository (recommended)

1. Open **HACS** in your Home Assistant sidebar.
2. Click the **three-dot menu** (⋮) in the top-right corner → **Custom repositories**.
3. Paste the repository URL:
   ```
   https://github.com/il90il90/hass-israel-tv
   ```
4. Set **Category** to `Integration` → click **Add**.
5. Search for **Israel TV** in HACS → click **Download**.
6. **Restart Home Assistant**.

### Method B — Manual

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

**Total: 42 channels**

### שידורי ישראל — Israeli Broadcast

| # | Channel | Hebrew | Stream |
|---|---------|--------|--------|
| 1 | Channel 11 | כאן 11 | HLS |
| 2 | Channel 11 HEVC | כאן 11 HEVC | HLS |
| 3 | Channel 11 Subtitles | כאן 11 כתוביות | HLS |
| 4 | Channel 12 | קשת 12 | HLS |
| 5 | Channel 12 HEVC | קשת 12 HEVC | HLS |
| 6 | Channel 12 Subtitles | קשת 12 כתוביות | HLS |
| 7 | Channel 13 | רשת 13 | HLS |
| 8 | Channel 13 HEVC | רשת 13 HEVC | HLS |
| 9 | Channel 13 Subtitles | רשת 13 כתוביות | HLS |
| 10 | Channel 14 | ערוץ 14 | HLS |
| 11 | Channel 14 HEVC | ערוץ 14 HEVC | HLS |
| 12 | Channel 14 Subtitles | ערוץ 14 כתוביות | HLS |
| 13 | Channel 9 | ערוץ 9 | HLS |

### ספורט 5 — Sport 5

| # | Channel | Hebrew | Stream |
|---|---------|--------|--------|
| 1 | Sport 5 | ספורט 5 | HLS |
| 2 | Sport 5 Plus | ספורט 5 פלוס | HLS |
| 3 | Sport 5 Plus HEVC | ספורט 5 פלוס HEVC | HLS |
| 4 | Sport 5 Gold | ספורט 5 גולד | HLS |
| 5 | Sport 5 Live | ספורט 5 לייב | HLS |
| 6 | Sport 5 Live HEVC | ספורט 5 לייב HEVC | HLS |
| 7 | Sport 5 Max | ספורט 5 מקס | HLS |
| 8 | Sport 5 4K | ספורט 5 4K | HLS |

### ONE

| # | Channel | Hebrew | Stream |
|---|---------|--------|--------|
| 1 | ONE 1 | ONE 1 | HLS |
| 2 | ONE 2 | ONE 2 | HLS |
| 3 | ONE Doco | ONE דוקו | HLS |
| 4 | ONE Edge | ONE אדג' | HLS |

### VIVA

| # | Channel | Hebrew | Stream |
|---|---------|--------|--------|
| 1 | VIVA | VIVA | HLS |
| 2 | VIVA Plus | VIVA פלוס | HLS |

### ריאליטי ותוכן — Reality & Content

| # | Channel | Hebrew | Stream |
|---|---------|--------|--------|
| 1 | Eretz Nehederet | ארץ נהדרת | HLS |
| 2 | Vamos | וואמוס | HLS |

### מוזיקה ובידור — Music & Entertainment

| # | Channel | Hebrew | Stream |
|---|---------|--------|--------|
| 1 | Music 24 | מיוזיק 24 | HLS |
| 2 | Music IL | מיוזיק IL | HLS |
| 3 | Karaoke Channel | ערוץ הקריוקי | HLS |

### ילדים — Kids

| # | Channel | Hebrew | Stream |
|---|---------|--------|--------|
| 1 | Yoyo | יויו | HLS |
| 2 | Logi | לוגי | HLS |
| 3 | Yalduti | ילדותי | HLS |
| 4 | Junior | ג'וניור | HLS |
| 5 | FOMO | FOMO | HLS |

### לייפסטייל — Lifestyle

| # | Channel | Hebrew | Stream |
|---|---------|--------|--------|
| 1 | Foody | פודי | HLS |
| 2 | Beautyz | ביוטיז | HLS |
| 3 | Daystar | דייסטאר | HLS |
| 4 | A Plus | A פלוס | HLS |

### סרטים — Movies

| # | Channel | Hebrew | Stream |
|---|---------|--------|--------|
| 1 | 30A Classic Movies | קלאסיקות 30A | HLS |

---

## Troubleshooting

**Channel not loading / buffering**

- Check that your Home Assistant server has internet access.
- Try a different source URL for the same channel (where multiple sources are listed).
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
[ha-badge]: https://img.shields.io/badge/Home%20Assistant-2023.6%2B-blue.svg
[ha-url]: https://www.home-assistant.io
[license-badge]: https://img.shields.io/badge/License-MIT-yellow.svg
[license-url]: LICENSE
