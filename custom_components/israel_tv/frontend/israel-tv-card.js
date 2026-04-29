/**
 * Israel TV — Custom Lovelace Card
 * Shows all live Israeli TV channels in a grid.
 * Click a channel to play it on any media_player in the house,
 * or watch it inline using HLS.js when no entity is configured.
 */

// ── Channel data (mirrors channels.py) ────────────────────────────────────────
const LOGO_BASE =
  "https://raw.githubusercontent.com/il90il90/hass-israel-tv/main/custom_components/israel_tv/logos/";

const CHANNELS = [
  // Broadcast
  { id: "kan11",         name: "כאן 11",            cat: "broadcast", logo: "kan11" },
  { id: "kan11_subs",    name: "כאן 11 כתוביות",    cat: "broadcast", logo: "kan11" },
  { id: "keshet_12",     name: "קשת 12",             cat: "broadcast", logo: "keshet_12" },
  { id: "keshet_12_subs",name: "קשת 12 כתוביות",    cat: "broadcast", logo: "keshet_12" },
  { id: "reshet_13",     name: "רשת 13",             cat: "broadcast", logo: "reshet_13" },
  { id: "reshet_13_subs",name: "רשת 13 כתוביות",    cat: "broadcast", logo: "reshet_13" },
  { id: "ch14",          name: "ערוץ 14",            cat: "broadcast", logo: "ch14" },
  { id: "ch14_subs",     name: "ערוץ 14 כתוביות",   cat: "broadcast", logo: "ch14" },
  { id: "ch9",           name: "ערוץ 9",             cat: "broadcast", logo: "ch9" },
  // Sport
  { id: "sport_5",       name: "ספורט 5",            cat: "sport",    logo: "sport_5" },
  { id: "sport_5_plus",  name: "ספורט 5 פלוס",       cat: "sport",    logo: "sport_5_plus" },
  { id: "sport_5_gold",  name: "ספורט 5 גולד",       cat: "sport",    logo: "sport_5_gold" },
  { id: "sport_5_live",  name: "ספורט 5 לייב",       cat: "sport",    logo: "sport_5_live" },
  { id: "sport_5_max",   name: "ספורט 5 מקס",        cat: "sport",    logo: "sport_5" },
  { id: "sport_5_4k",    name: "ספורט 5 4K",         cat: "sport",    logo: "sport_5_4k" },
  { id: "one_1",         name: "ONE 1",               cat: "sport",    logo: "one_1" },
  { id: "one_2",         name: "ONE 2",               cat: "sport",    logo: "one_2" },
  { id: "one_doco",      name: "ONE דוקו",            cat: "sport",    logo: "one_1" },
  { id: "one_edge",      name: "ONE אדג'",            cat: "sport",    logo: "one_1" },
  { id: "yes1",          name: "ספורט 1",             cat: "sport",    logo: "yes1" },
  { id: "yes2",          name: "ספורט 2",             cat: "sport",    logo: "yes2" },
  { id: "yes3",          name: "ספורט 3",             cat: "sport",    logo: "yes3" },
  { id: "yes4",          name: "ספורט 4",             cat: "sport",    logo: "yes4" },
  // VIVA
  { id: "viva",          name: "VIVA",                cat: "viva",     logo: "viva" },
  { id: "viva_plus",     name: "VIVA פלוס",           cat: "viva",     logo: "viva_plus" },
  // Reality
  { id: "erez_nehederet",name: "ארץ נהדרת",           cat: "reality",  logo: null },
  { id: "vamos",         name: "וואמוס",              cat: "reality",  logo: null },
  // Music
  { id: "music24",       name: "מיוזיק 24",           cat: "music",    logo: null },
  { id: "music_il",      name: "מיוזיק IL",           cat: "music",    logo: "music_il" },
  { id: "karaoke",       name: "ערוץ הקריוקי",        cat: "music",    logo: null },
  // Kids
  { id: "yoyo",          name: "יויו",                cat: "kids",     logo: "yoyo" },
  { id: "logi",          name: "לוגי",                cat: "kids",     logo: null },
  { id: "yalduti",       name: "ילדותי",              cat: "kids",     logo: null },
  { id: "junior",        name: "ג'וניור",             cat: "kids",     logo: "junior" },
  { id: "fomo",          name: "FOMO",                cat: "kids",     logo: null },
  // Lifestyle
  { id: "hidabroot",     name: "הידברות",             cat: "lifestyle",logo: "hidabroot" },
  { id: "foody",         name: "פודי",                cat: "lifestyle",logo: "foody" },
  { id: "beautyz",       name: "ביוטיז",              cat: "lifestyle",logo: null },
  { id: "daystar",       name: "דייסטאר",             cat: "lifestyle",logo: null },
  { id: "a_plus",        name: "A פלוס",              cat: "lifestyle",logo: null },
  // Movies
  { id: "30a_classic_movies", name: "קלאסיקות 30A",  cat: "movies",   logo: null },
];

const CATS = {
  broadcast: "שידורי ישראל",
  sport:     "ספורט",
  viva:      "VIVA",
  reality:   "ריאליטי",
  music:     "מוזיקה",
  kids:      "ילדים",
  lifestyle: "לייפסטייל",
  movies:    "סרטים",
};

// HLS.js loaded on demand
const HLS_JS_URL = "https://cdn.jsdelivr.net/npm/hls.js@1.5.15/dist/hls.min.js";
let _hlsLoaded = false;

async function loadHls() {
  if (window.Hls || _hlsLoaded) return window.Hls;
  return new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = HLS_JS_URL;
    s.onload = () => { _hlsLoaded = true; resolve(window.Hls); };
    s.onerror = reject;
    document.head.appendChild(s);
  });
}

// ── CSS ────────────────────────────────────────────────────────────────────────
const STYLES = `
  :host { display: block; font-family: var(--paper-font-body1_-_font-family, sans-serif); direction: rtl; }

  .card {
    background: var(--ha-card-background, var(--card-background-color, #1c1c1e));
    border-radius: var(--ha-card-border-radius, 12px);
    overflow: hidden;
    box-shadow: var(--ha-card-box-shadow, 0 2px 8px rgba(0,0,0,.3));
  }

  /* ── Header ── */
  .header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 16px;
    background: var(--primary-color, #03a9f4);
    color: #fff;
  }
  .header-icon { font-size: 22px; }
  .header-title { font-size: 17px; font-weight: 700; flex: 1; }
  .header-back {
    background: none; border: none; color: #fff; font-size: 20px;
    cursor: pointer; padding: 0 6px; line-height: 1;
  }

  /* ── Category tabs ── */
  .cats {
    display: flex;
    overflow-x: auto;
    gap: 6px;
    padding: 10px 12px;
    scrollbar-width: none;
    border-bottom: 1px solid var(--divider-color, rgba(255,255,255,.12));
    background: var(--secondary-background-color, #111);
  }
  .cats::-webkit-scrollbar { display: none; }
  .cat-btn {
    flex-shrink: 0;
    padding: 5px 13px;
    border-radius: 20px;
    border: 1px solid var(--divider-color, rgba(255,255,255,.2));
    background: transparent;
    color: var(--primary-text-color, #eee);
    font-size: 12px;
    cursor: pointer;
    transition: background .15s, color .15s;
    white-space: nowrap;
  }
  .cat-btn.active {
    background: var(--primary-color, #03a9f4);
    color: #fff;
    border-color: transparent;
  }

  /* ── Channel grid ── */
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(88px, 1fr));
    gap: 8px;
    padding: 12px;
  }

  .tile {
    position: relative;
    aspect-ratio: 1;
    border-radius: 10px;
    overflow: hidden;
    cursor: pointer;
    background: var(--secondary-background-color, #2a2a2e);
    transition: transform .15s, box-shadow .15s;
  }
  .tile:hover { transform: scale(1.06); box-shadow: 0 4px 16px rgba(0,0,0,.5); }
  .tile:active { transform: scale(0.97); }

  .tile img {
    width: 100%; height: 100%;
    object-fit: cover;
    display: block;
  }
  .tile-fallback {
    width: 100%; height: 100%;
    display: flex; align-items: center; justify-content: center;
    font-size: 11px; font-weight: 600;
    color: var(--primary-text-color, #eee);
    text-align: center; padding: 6px;
    background: linear-gradient(135deg, #1e3a5f, #0a1628);
  }
  .tile-name {
    position: absolute; bottom: 0; left: 0; right: 0;
    background: linear-gradient(transparent, rgba(0,0,0,.85));
    color: #fff;
    font-size: 10px; font-weight: 500;
    padding: 14px 4px 4px;
    text-align: center;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }

  /* ── Player view ── */
  .player {
    display: flex; flex-direction: column;
  }
  video {
    width: 100%;
    aspect-ratio: 16 / 9;
    background: #000;
    display: block;
  }
  .player-info {
    display: flex; align-items: center; gap: 10px;
    padding: 10px 14px;
    background: var(--secondary-background-color, #111);
  }
  .player-logo {
    width: 40px; height: 40px; border-radius: 6px; object-fit: cover;
  }
  .player-name { font-size: 15px; font-weight: 600; color: var(--primary-text-color, #eee); }
  .player-status { font-size: 11px; color: var(--secondary-text-color, #999); margin-top: 2px; }

  /* ── Status overlay ── */
  .overlay {
    position: absolute; inset: 0;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    background: rgba(0,0,0,.7);
    color: #fff; font-size: 13px; gap: 10px;
  }
  .spinner {
    width: 32px; height: 32px;
    border: 3px solid rgba(255,255,255,.3);
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin .8s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* ── Entity picker dialog ── */
  .picker-overlay {
    position: fixed; inset: 0; z-index: 9999;
    background: rgba(0,0,0,.6);
    display: flex; align-items: center; justify-content: center;
  }
  .picker-box {
    background: var(--ha-card-background, #1c1c1e);
    border-radius: 14px; padding: 20px;
    min-width: 260px; max-width: 90vw;
    box-shadow: 0 8px 32px rgba(0,0,0,.6);
  }
  .picker-title { font-size: 15px; font-weight: 700; margin-bottom: 14px; color: var(--primary-text-color,#eee); }
  .picker-entity {
    display: flex; align-items: center; gap: 10px;
    padding: 10px 12px; border-radius: 8px; cursor: pointer;
    transition: background .1s;
  }
  .picker-entity:hover { background: rgba(255,255,255,.08); }
  .picker-entity-icon { font-size: 20px; }
  .picker-entity-name { font-size: 13px; color: var(--primary-text-color,#eee); }
  .picker-cancel {
    margin-top: 12px; width: 100%; padding: 9px;
    border-radius: 8px; border: 1px solid var(--divider-color,rgba(255,255,255,.2));
    background: transparent; color: var(--secondary-text-color,#999);
    font-size: 13px; cursor: pointer;
  }
`;

// ── Card class ─────────────────────────────────────────────────────────────────
class IsraelTvCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._config = {};
    this._activeCat = "broadcast";
    this._view = "grid"; // "grid" | "player"
    this._playingChannel = null;
    this._hls = null;
    this._mediaStatus = "";
  }

  // ── HA lifecycle ──────────────────────────────────────────────────────────

  setConfig(config) {
    this._config = config || {};
    if (this._config.category && CATS[this._config.category]) {
      this._activeCat = this._config.category;
    }
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
  }

  connectedCallback() {
    if (!this._rendered) this._render();
  }

  // ── Rendering ─────────────────────────────────────────────────────────────

  _render() {
    this._rendered = true;
    const shadow = this.shadowRoot;
    shadow.innerHTML = "";

    const style = document.createElement("style");
    style.textContent = STYLES;
    shadow.appendChild(style);

    const card = document.createElement("div");
    card.className = "card";

    if (this._view === "player" && this._playingChannel) {
      card.appendChild(this._buildPlayerView());
    } else {
      card.appendChild(this._buildHeader());
      card.appendChild(this._buildCatBar());
      card.appendChild(this._buildGrid(this._activeCat));
    }

    shadow.appendChild(card);
  }

  _buildHeader() {
    const el = document.createElement("div");
    el.className = "header";
    el.innerHTML = `
      <span class="header-icon">📺</span>
      <span class="header-title">Israel TV</span>
    `;
    return el;
  }

  _buildCatBar() {
    const bar = document.createElement("div");
    bar.className = "cats";
    Object.entries(CATS).forEach(([id, label]) => {
      const btn = document.createElement("button");
      btn.className = "cat-btn" + (id === this._activeCat ? " active" : "");
      btn.textContent = label;
      btn.addEventListener("click", () => {
        this._activeCat = id;
        this._render();
      });
      bar.appendChild(btn);
    });
    return bar;
  }

  _buildGrid(category) {
    const grid = document.createElement("div");
    grid.className = "grid";
    const channels = CHANNELS.filter((c) => c.cat === category);
    channels.forEach((ch) => {
      const tile = document.createElement("div");
      tile.className = "tile";
      tile.title = ch.name;

      if (ch.logo) {
        const img = document.createElement("img");
        img.src = LOGO_BASE + ch.logo + ".png";
        img.alt = ch.name;
        img.onerror = () => {
          img.replaceWith(this._fallbackEl(ch.name));
        };
        tile.appendChild(img);
      } else {
        tile.appendChild(this._fallbackEl(ch.name));
      }

      const nameEl = document.createElement("div");
      nameEl.className = "tile-name";
      nameEl.textContent = ch.name;
      tile.appendChild(nameEl);

      tile.addEventListener("click", () => this._handleChannelClick(ch));
      grid.appendChild(tile);
    });
    return grid;
  }

  _fallbackEl(name) {
    const d = document.createElement("div");
    d.className = "tile-fallback";
    d.textContent = name;
    return d;
  }

  // ── Player view ───────────────────────────────────────────────────────────

  _buildPlayerView() {
    const ch = this._playingChannel;
    const wrapper = document.createElement("div");
    wrapper.className = "player";

    // Header with back button
    const header = document.createElement("div");
    header.className = "header";
    header.innerHTML = `
      <button class="header-back" title="חזרה">‹</button>
      <span class="header-icon">📺</span>
      <span class="header-title">${ch.name}</span>
    `;
    header.querySelector(".header-back").addEventListener("click", () => {
      this._stopPlayer();
      this._view = "grid";
      this._render();
    });
    wrapper.appendChild(header);

    // Video element + overlay wrapper
    const videoWrap = document.createElement("div");
    videoWrap.style.position = "relative";

    const video = document.createElement("video");
    video.controls = true;
    video.autoplay = true;
    video.playsInline = true;
    video.style.width = "100%";
    video.style.aspectRatio = "16/9";
    video.style.background = "#000";
    videoWrap.appendChild(video);

    // Loading overlay
    const overlay = document.createElement("div");
    overlay.className = "overlay";
    overlay.innerHTML = `<div class="spinner"></div><span>טוען…</span>`;
    videoWrap.appendChild(overlay);

    wrapper.appendChild(videoWrap);

    // Channel info bar
    const info = document.createElement("div");
    info.className = "player-info";
    if (ch.logo) {
      const img = document.createElement("img");
      img.className = "player-logo";
      img.src = LOGO_BASE + ch.logo + ".png";
      img.alt = ch.name;
      info.appendChild(img);
    }
    const txt = document.createElement("div");
    txt.innerHTML = `
      <div class="player-name">${ch.name}</div>
      <div class="player-status" id="pstatus">מחבר…</div>
    `;
    info.appendChild(txt);
    wrapper.appendChild(info);

    // Start playback after DOM is attached
    requestAnimationFrame(() => {
      this._startInlinePlayback(video, overlay, wrapper.querySelector("#pstatus"));
    });

    return wrapper;
  }

  // ── Playback logic ────────────────────────────────────────────────────────

  async _handleChannelClick(channel) {
    const mp = this._config.media_player;

    if (mp) {
      // Send to a specific media_player entity
      this._playOnEntity(channel, mp);
      return;
    }

    // Check if multiple media_player entities exist → let user pick
    if (this._hass) {
      const players = Object.keys(this._hass.states).filter(
        (e) => e.startsWith("media_player.")
      );
      if (players.length === 1) {
        this._playOnEntity(channel, players[0]);
        return;
      }
      if (players.length > 1) {
        this._showEntityPicker(channel, players);
        return;
      }
    }

    // No media_player found → play inline
    this._playingChannel = channel;
    this._view = "player";
    this._render();
  }

  _playOnEntity(channel, entityId) {
    if (!this._hass) return;
    this._hass.callService("media_player", "play_media", {
      entity_id: entityId,
      media_content_id: `media-source://israel_tv/${channel.id}`,
      media_content_type: "video",
    });
    // Show a brief toast-like feedback (fire HA notification)
    this._hass.callService("persistent_notification", "create", {
      message: `▶ ${channel.name} נשלח ל-${entityId}`,
      notification_id: "israel_tv_play",
    });
  }

  async _startInlinePlayback(videoEl, overlayEl, statusEl) {
    try {
      // Resolve the actual HLS URL via the media_source backend
      const result = await this._hass.callWS({
        type: "media_source/resolve_media",
        media_content_id: `media-source://israel_tv/${this._playingChannel.id}`,
      });
      const url = result.url;

      const Hls = await loadHls();

      if (Hls && Hls.isSupported()) {
        this._stopPlayer();
        const hls = new Hls({ enableWorker: false });
        this._hls = hls;
        hls.loadSource(url);
        hls.attachMedia(videoEl);
        hls.on(Hls.Events.MANIFEST_PARSED, () => {
          overlayEl.style.display = "none";
          if (statusEl) statusEl.textContent = "בשידור חי";
          videoEl.play().catch(() => {});
        });
        hls.on(Hls.Events.ERROR, (_ev, data) => {
          if (data.fatal) {
            if (statusEl) statusEl.textContent = "שגיאת סטרימינג";
          }
        });
      } else if (videoEl.canPlayType("application/vnd.apple.mpegurl")) {
        // Native HLS (Safari / iOS)
        videoEl.src = url;
        videoEl.addEventListener("loadedmetadata", () => {
          overlayEl.style.display = "none";
          if (statusEl) statusEl.textContent = "בשידור חי";
          videoEl.play().catch(() => {});
        });
      } else {
        overlayEl.innerHTML = "הדפדפן אינו תומך בסטרימינג HLS";
      }
    } catch (err) {
      console.error("Israel TV card playback error:", err);
      if (overlayEl) overlayEl.innerHTML = "שגיאה בטעינת הערוץ";
      if (statusEl) statusEl.textContent = "שגיאה";
    }
  }

  _stopPlayer() {
    if (this._hls) {
      this._hls.destroy();
      this._hls = null;
    }
  }

  // ── Entity picker dialog ──────────────────────────────────────────────────

  _showEntityPicker(channel, players) {
    const overlay = document.createElement("div");
    overlay.className = "picker-overlay";

    const box = document.createElement("div");
    box.className = "picker-box";

    const title = document.createElement("div");
    title.className = "picker-title";
    title.textContent = `בחר נגן עבור "${channel.name}"`;
    box.appendChild(title);

    players.forEach((entityId) => {
      const state = this._hass.states[entityId];
      const friendlyName = state?.attributes?.friendly_name || entityId;
      const row = document.createElement("div");
      row.className = "picker-entity";
      row.innerHTML = `
        <span class="picker-entity-icon">🔊</span>
        <span class="picker-entity-name">${friendlyName}</span>
      `;
      row.addEventListener("click", () => {
        overlay.remove();
        this._playOnEntity(channel, entityId);
      });
      box.appendChild(row);
    });

    // Inline playback option
    const inlineRow = document.createElement("div");
    inlineRow.className = "picker-entity";
    inlineRow.innerHTML = `
      <span class="picker-entity-icon">📱</span>
      <span class="picker-entity-name">צפייה בממשק זה (inline)</span>
    `;
    inlineRow.addEventListener("click", () => {
      overlay.remove();
      this._playingChannel = channel;
      this._view = "player";
      this._render();
    });
    box.appendChild(inlineRow);

    // Cancel
    const cancel = document.createElement("button");
    cancel.className = "picker-cancel";
    cancel.textContent = "ביטול";
    cancel.addEventListener("click", () => overlay.remove());
    box.appendChild(cancel);

    overlay.appendChild(box);
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) overlay.remove();
    });

    // Append to document body (not shadow root) so it overlays everything
    document.body.appendChild(overlay);
  }

  // ── HA card metadata ──────────────────────────────────────────────────────

  static getStubConfig() {
    return {
      // Optional: pin a specific media_player entity.
      // If omitted, the card auto-discovers or shows an inline player.
      // media_player: "media_player.my_tv",

      // Optional: start on a specific category (broadcast/sport/kids/…)
      // category: "broadcast",
    };
  }

  getCardSize() {
    return 6;
  }
}

customElements.define("israel-tv-card", IsraelTvCard);

// Register in HA's custom card registry so it appears in the card picker
window.customCards = window.customCards || [];
if (!window.customCards.find((c) => c.type === "israel-tv-card")) {
  window.customCards.push({
    type: "israel-tv-card",
    name: "Israel TV",
    description: "ערוצי טלוויזיה ישראלית חיים — בחרו ערוץ לצפייה",
    preview: false,
    documentationURL:
      "https://github.com/il90il90/hass-israel-tv",
  });
}
