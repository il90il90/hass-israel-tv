/**
 * Israel TV — Custom Lovelace Card
 *
 * Configuration:
 *   type: custom:israel-tv-card
 *   channel: kan11          # required — channel id to play
 *   show_name: true          # optional — show channel name bar (default true)
 *
 * In the visual card editor simply pick a channel from the dropdown.
 * The card then plays that channel's live HLS stream continuously,
 * exactly like a camera picture-entity card.
 */

// ── Channel data (mirrors channels.py) ────────────────────────────────────────
const LOGO_BASE =
  "https://raw.githubusercontent.com/il90il90/hass-israel-tv/main/custom_components/israel_tv/logos/";

const CHANNELS = [
  // Broadcast
  { id: "kan11",          name: "כאן 11",           cat: "broadcast", logo: "kan11" },
  { id: "kan11_subs",     name: "כאן 11 כתוביות",   cat: "broadcast", logo: "kan11" },
  { id: "keshet_12",      name: "קשת 12",            cat: "broadcast", logo: "keshet_12" },
  { id: "keshet_12_subs", name: "קשת 12 כתוביות",   cat: "broadcast", logo: "keshet_12" },
  { id: "reshet_13",      name: "רשת 13",            cat: "broadcast", logo: "reshet_13" },
  { id: "reshet_13_subs", name: "רשת 13 כתוביות",   cat: "broadcast", logo: "reshet_13" },
  { id: "ch14",           name: "ערוץ 14",           cat: "broadcast", logo: "ch14" },
  { id: "ch14_subs",      name: "ערוץ 14 כתוביות",  cat: "broadcast", logo: "ch14" },
  { id: "ch9",            name: "ערוץ 9",            cat: "broadcast", logo: "ch9" },
  // Sport
  { id: "sport_5",        name: "ספורט 5",           cat: "sport",    logo: "sport_5" },
  { id: "sport_5_plus",   name: "ספורט 5 פלוס",      cat: "sport",    logo: "sport_5_plus" },
  { id: "sport_5_gold",   name: "ספורט 5 גולד",      cat: "sport",    logo: "sport_5_gold" },
  { id: "sport_5_live",   name: "ספורט 5 לייב",      cat: "sport",    logo: "sport_5_live" },
  { id: "sport_5_max",    name: "ספורט 5 מקס",       cat: "sport",    logo: "sport_5" },
  { id: "sport_5_4k",     name: "ספורט 5 4K",        cat: "sport",    logo: "sport_5_4k" },
  { id: "one_1",          name: "ONE 1",              cat: "sport",    logo: "one_1" },
  { id: "one_2",          name: "ONE 2",              cat: "sport",    logo: "one_2" },
  { id: "one_doco",       name: "ONE דוקו",           cat: "sport",    logo: "one_1" },
  { id: "one_edge",       name: "ONE אדג'",           cat: "sport",    logo: "one_1" },
  { id: "yes1",           name: "ספורט 1",            cat: "sport",    logo: "yes1" },
  { id: "yes2",           name: "ספורט 2",            cat: "sport",    logo: "yes2" },
  { id: "yes3",           name: "ספורט 3",            cat: "sport",    logo: "yes3" },
  { id: "yes4",           name: "ספורט 4",            cat: "sport",    logo: "yes4" },
  // VIVA
  { id: "viva",           name: "VIVA",               cat: "viva",     logo: "viva" },
  { id: "viva_plus",      name: "VIVA פלוס",          cat: "viva",     logo: "viva_plus" },
  // Reality
  { id: "erez_nehederet", name: "ארץ נהדרת",          cat: "reality",  logo: null },
  { id: "vamos",          name: "וואמוס",             cat: "reality",  logo: null },
  // Music
  { id: "music24",        name: "מיוזיק 24",          cat: "music",    logo: null },
  { id: "music_il",       name: "מיוזיק IL",          cat: "music",    logo: "music_il" },
  { id: "karaoke",        name: "ערוץ הקריוקי",       cat: "music",    logo: null },
  // Kids
  { id: "yoyo",           name: "יויו",               cat: "kids",     logo: "yoyo" },
  { id: "logi",           name: "לוגי",               cat: "kids",     logo: null },
  { id: "yalduti",        name: "ילדותי",             cat: "kids",     logo: null },
  { id: "junior",         name: "ג'וניור",            cat: "kids",     logo: "junior" },
  { id: "fomo",           name: "FOMO",               cat: "kids",     logo: null },
  // Lifestyle
  { id: "hidabroot",      name: "הידברות",            cat: "lifestyle",logo: "hidabroot" },
  { id: "foody",          name: "פודי",               cat: "lifestyle",logo: "foody" },
  { id: "beautyz",        name: "ביוטיז",             cat: "lifestyle",logo: null },
  { id: "daystar",        name: "דייסטאר",            cat: "lifestyle",logo: null },
  { id: "a_plus",         name: "A פלוס",             cat: "lifestyle",logo: null },
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

// ── HLS.js loader ─────────────────────────────────────────────────────────────
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

// ── Styles ─────────────────────────────────────────────────────────────────────
const CARD_STYLES = `
  :host { display: block; direction: rtl; font-family: var(--paper-font-body1_-_font-family, sans-serif); }

  .wrapper {
    background: #000;
    border-radius: var(--ha-card-border-radius, 12px);
    overflow: hidden;
    box-shadow: var(--ha-card-box-shadow, 0 2px 8px rgba(0,0,0,.4));
    position: relative;
  }

  /* ── Video ── */
  video {
    width: 100%;
    aspect-ratio: 16 / 9;
    display: block;
    background: #000;
    cursor: pointer;
  }

  /* ── Name bar (bottom) ── */
  .name-bar {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    background: var(--ha-card-background, var(--card-background-color, #1c1c1e));
  }
  .channel-logo {
    width: 32px; height: 32px;
    border-radius: 5px;
    object-fit: cover;
    flex-shrink: 0;
  }
  .channel-name {
    font-size: 14px;
    font-weight: 600;
    color: var(--primary-text-color, #eee);
    flex: 1;
  }
  .live-badge {
    font-size: 10px;
    font-weight: 700;
    color: #fff;
    background: #e53935;
    border-radius: 4px;
    padding: 2px 6px;
    letter-spacing: 0.5px;
  }

  /* ── Loading / error overlay ── */
  .overlay {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: rgba(0,0,0,.75);
    color: #fff;
    gap: 12px;
    font-size: 14px;
  }
  .overlay.hidden { display: none; }
  .spinner {
    width: 36px; height: 36px;
    border: 3px solid rgba(255,255,255,.25);
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin .8s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* ── Not configured placeholder ── */
  .placeholder {
    aspect-ratio: 16 / 9;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 10px;
    background: var(--ha-card-background, #1c1c1e);
    color: var(--secondary-text-color, #888);
    font-size: 14px;
    padding: 20px;
    text-align: center;
  }
  .placeholder-icon { font-size: 40px; }
`;

// ── Main Card ──────────────────────────────────────────────────────────────────
class IsraelTvCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._config = {};
    this._hls = null;
    this._currentChannelId = null;
    this._retryTimer = null;
  }

  // ── HA lifecycle ──────────────────────────────────────────────────────────

  setConfig(config) {
    if (!config) throw new Error("Invalid configuration");
    this._config = config;
    // Re-render and reload stream only when channel changes
    if (config.channel !== this._currentChannelId) {
      this._stopStream();
      this._render();
      if (config.channel) this._startStream(config.channel);
    }
  }

  set hass(hass) {
    this._hass = hass;
  }

  disconnectedCallback() {
    this._stopStream();
  }

  // ── Render ────────────────────────────────────────────────────────────────

  _render() {
    const channelId = this._config.channel;
    const channel   = CHANNELS.find((c) => c.id === channelId);
    const showName  = this._config.show_name !== false; // default true

    const shadow = this.shadowRoot;
    shadow.innerHTML = "";

    const style = document.createElement("style");
    style.textContent = CARD_STYLES;
    shadow.appendChild(style);

    const wrapper = document.createElement("div");
    wrapper.className = "wrapper";

    if (!channel) {
      // No channel configured — show placeholder
      wrapper.innerHTML = `
        <div class="placeholder">
          <div class="placeholder-icon">📺</div>
          <div>ערוץ לא נבחר</div>
          <div style="font-size:12px;opacity:.6">ערוך את הכרטיס ובחר ערוץ</div>
        </div>`;
      shadow.appendChild(wrapper);
      return;
    }

    // Video element
    const video = document.createElement("video");
    video.muted    = true;
    video.autoplay = true;
    video.playsInline = true;
    video.controls = true;
    video.id = "itv-video";
    wrapper.appendChild(video);

    // Loading overlay
    const overlay = document.createElement("div");
    overlay.className = "overlay";
    overlay.id = "itv-overlay";
    overlay.innerHTML = `<div class="spinner"></div><span>טוען ${channel.name}…</span>`;
    wrapper.appendChild(overlay);

    // Name bar
    if (showName) {
      const bar = document.createElement("div");
      bar.className = "name-bar";
      if (channel.logo) {
        const img = document.createElement("img");
        img.className = "channel-logo";
        img.src = LOGO_BASE + channel.logo + ".png";
        img.alt = channel.name;
        bar.appendChild(img);
      }
      const name = document.createElement("span");
      name.className = "channel-name";
      name.textContent = channel.name;
      bar.appendChild(name);
      const live = document.createElement("span");
      live.className = "live-badge";
      live.textContent = "LIVE";
      bar.appendChild(live);
      wrapper.appendChild(bar);
    }

    shadow.appendChild(wrapper);
  }

  // ── Stream playback ───────────────────────────────────────────────────────

  async _startStream(channelId) {
    this._currentChannelId = channelId;
    clearTimeout(this._retryTimer);

    const video   = this.shadowRoot.getElementById("itv-video");
    const overlay = this.shadowRoot.getElementById("itv-overlay");
    if (!video) return;

    try {
      // Resolve the actual HLS URL via the media_source backend
      const result = await this._hass.callWS({
        type: "media_source/resolve_media",
        media_content_id: `media-source://israel_tv/${channelId}`,
      });
      const url = result.url;

      const Hls = await loadHls();

      if (Hls && Hls.isSupported()) {
        this._stopStream();
        const hls = new Hls({
          enableWorker: false,
          liveSyncDurationCount: 3,
          liveMaxLatencyDurationCount: 10,
        });
        this._hls = hls;

        hls.loadSource(url);
        hls.attachMedia(video);

        hls.on(Hls.Events.MANIFEST_PARSED, () => {
          if (overlay) overlay.classList.add("hidden");
          video.play().catch(() => {});
        });

        hls.on(Hls.Events.ERROR, (_e, data) => {
          if (data.fatal) {
            hls.destroy();
            this._hls = null;
            if (overlay) {
              overlay.classList.remove("hidden");
              overlay.innerHTML = `<span>מתחבר מחדש…</span>`;
            }
            // Auto-retry after 5 s
            this._retryTimer = setTimeout(() => this._startStream(channelId), 5000);
          }
        });

      } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
        // Native HLS (Safari / iOS)
        video.src = url;
        video.addEventListener("loadedmetadata", () => {
          if (overlay) overlay.classList.add("hidden");
          video.play().catch(() => {});
        }, { once: true });
      } else {
        if (overlay) overlay.innerHTML = "הדפדפן אינו תומך בסטרימינג";
      }
    } catch (err) {
      console.error("Israel TV card error:", err);
      if (overlay) overlay.innerHTML = `<span>שגיאה בטעינה — מנסה שוב…</span>`;
      this._retryTimer = setTimeout(() => this._startStream(channelId), 8000);
    }
  }

  _stopStream() {
    clearTimeout(this._retryTimer);
    if (this._hls) {
      this._hls.destroy();
      this._hls = null;
    }
    this._currentChannelId = null;
  }

  // ── Card size hint for HA grid ────────────────────────────────────────────
  getCardSize() { return 3; }

  // ── Visual card editor ────────────────────────────────────────────────────
  static getConfigElement() {
    return document.createElement("israel-tv-card-editor");
  }

  static getStubConfig() {
    return { channel: "kan11", show_name: true };
  }
}

// ── Card Editor (shown in the visual card picker) ──────────────────────────────
class IsraelTvCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = { ...config };
    this._render();
  }

  _render() {
    this.innerHTML = `
      <style>
        .editor { padding: 16px; direction: rtl; font-family: sans-serif; }
        label { display: block; margin-bottom: 6px; font-size: 13px; color: var(--secondary-text-color, #888); }
        select, input[type=checkbox] { font-size: 14px; }
        select {
          width: 100%; padding: 8px 10px; border-radius: 8px; margin-bottom: 14px;
          background: var(--secondary-background-color, #111);
          color: var(--primary-text-color, #eee);
          border: 1px solid var(--divider-color, rgba(255,255,255,.2));
        }
        .row { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
      </style>
      <div class="editor">
        <label>בחר ערוץ</label>
        <select id="channel-select">
          ${Object.entries(CATS).map(([catId, catLabel]) => `
            <optgroup label="${catLabel}">
              ${CHANNELS.filter(c => c.cat === catId).map(c => `
                <option value="${c.id}" ${c.id === this._config.channel ? "selected" : ""}>${c.name}</option>
              `).join("")}
            </optgroup>
          `).join("")}
        </select>
        <div class="row">
          <input type="checkbox" id="show-name" ${this._config.show_name !== false ? "checked" : ""}>
          <label style="margin:0">הצג שם ערוץ</label>
        </div>
      </div>
    `;

    this.querySelector("#channel-select").addEventListener("change", (e) => {
      this._config.channel = e.target.value;
      this._fireChanged();
    });
    this.querySelector("#show-name").addEventListener("change", (e) => {
      this._config.show_name = e.target.checked;
      this._fireChanged();
    });
  }

  _fireChanged() {
    this.dispatchEvent(new CustomEvent("config-changed", {
      detail: { config: { ...this._config } },
      bubbles: true,
      composed: true,
    }));
  }
}

// ── Register ───────────────────────────────────────────────────────────────────
customElements.define("israel-tv-card-editor", IsraelTvCardEditor);
customElements.define("israel-tv-card",        IsraelTvCard);

window.customCards = window.customCards || [];
if (!window.customCards.find((c) => c.type === "israel-tv-card")) {
  window.customCards.push({
    type:        "israel-tv-card",
    name:        "Israel TV",
    description: "ערוץ טלוויזיה ישראלי חי — בחר ערוץ בהגדרות",
    preview:     false,
    documentationURL: "https://github.com/il90il90/hass-israel-tv",
  });
}
