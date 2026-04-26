"""Channel definitions for Israel TV integration."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Channel:
    """Represents a single TV channel."""

    id: str
    name: str
    name_en: str
    category: str
    url: str
    thumbnail: str | None = None
    # When True the url is a webpage — the real HLS URL must be extracted from its HTML
    needs_extraction: bool = False


CATEGORY_LABELS: dict[str, str] = {
    "broadcast": "שידורי ישראל",
    "sport": "ספורט 5",
    "yes": "YES ספורט",
    "one": "ONE",
    "viva": "VIVA",
    "reality": "ריאליטי ותוכן",
    "music": "מוזיקה ובידור",
    "kids": "ילדים",
    "lifestyle": "לייפסטייל",
    "movies": "סרטים",
}

_CDN = "https://d1zqtf09wb8nt5.cloudfront.net/livehls/oil/freetv/live"


def _cdn(slug: str) -> str:
    # fmp4 gives modern fragmented-MP4 segments; omitting &renditions forces a
    # single fixed-quality stream so the player never switches quality mid-stream.
    return f"{_CDN}/{slug}/live.livx/playlist.m3u8?fmp4"


CHANNELS: list[Channel] = [
    # ── Broadcast ──────────────────────────────────────────────────────────────
    Channel(
        id="kan11",
        name="כאן 11",
        name_en="Channel 11",
        category="broadcast",
        url=_cdn("kan11"),
    ),
    Channel(
        id="kan11_hevc",
        name="כאן 11 HEVC",
        name_en="Channel 11 HEVC",
        category="broadcast",
        url=_cdn("kan11_hevc"),
    ),
    Channel(
        id="kan11_subs",
        name="כאן 11 כתוביות",
        name_en="Channel 11 Subtitles",
        category="broadcast",
        url=_cdn("kan11_subs"),
    ),
    Channel(
        id="keshet_12",
        name="קשת 12",
        name_en="Channel 12",
        category="broadcast",
        url=_cdn("keshet_12"),
    ),
    Channel(
        id="keshet_12_hevc",
        name="קשת 12 HEVC",
        name_en="Channel 12 HEVC",
        category="broadcast",
        url=_cdn("keshet_12_hevc"),
    ),
    Channel(
        id="keshet_12_subs",
        name="קשת 12 כתוביות",
        name_en="Channel 12 Subtitles",
        category="broadcast",
        url=_cdn("keshet_12_subs"),
    ),
    Channel(
        id="reshet_13",
        name="רשת 13",
        name_en="Channel 13",
        category="broadcast",
        url=_cdn("reshet_13"),
    ),
    Channel(
        id="reshet_13_hevc",
        name="רשת 13 HEVC",
        name_en="Channel 13 HEVC",
        category="broadcast",
        url=_cdn("reshet_13_hevc"),
    ),
    Channel(
        id="reshet_13_subs",
        name="רשת 13 כתוביות",
        name_en="Channel 13 Subtitles",
        category="broadcast",
        url=_cdn("reshet_13_subs"),
    ),
    Channel(
        id="ch14",
        name="ערוץ 14",
        name_en="Channel 14",
        category="broadcast",
        url=_cdn("ch14"),
    ),
    Channel(
        id="ch14_hevc",
        name="ערוץ 14 HEVC",
        name_en="Channel 14 HEVC",
        category="broadcast",
        url=_cdn("ch14_hevc"),
    ),
    Channel(
        id="ch14_subs",
        name="ערוץ 14 כתוביות",
        name_en="Channel 14 Subtitles",
        category="broadcast",
        url=_cdn("ch14_subs"),
    ),
    Channel(
        id="ch9",
        name="ערוץ 9",
        name_en="Channel 9",
        category="broadcast",
        url=_cdn("ch9"),
    ),
    # ── Sport 5 ────────────────────────────────────────────────────────────────
    Channel(
        id="sport_5",
        name="ספורט 5",
        name_en="Sport 5",
        category="sport",
        url=_cdn("sport_5"),
    ),
    Channel(
        id="sport_5_plus",
        name="ספורט 5 פלוס",
        name_en="Sport 5 Plus",
        category="sport",
        url=_cdn("sport_5_plus"),
    ),
    Channel(
        id="sport_5_plus_hevc",
        name="ספורט 5 פלוס HEVC",
        name_en="Sport 5 Plus HEVC",
        category="sport",
        url=_cdn("sport_5_plus_hevc"),
    ),
    Channel(
        id="sport_5_gold",
        name="ספורט 5 גולד",
        name_en="Sport 5 Gold",
        category="sport",
        url=_cdn("sport_5_gold"),
    ),
    Channel(
        id="sport_5_live",
        name="ספורט 5 לייב",
        name_en="Sport 5 Live",
        category="sport",
        url=_cdn("sport_5_live"),
    ),
    Channel(
        id="sport_5_live_hevc",
        name="ספורט 5 לייב HEVC",
        name_en="Sport 5 Live HEVC",
        category="sport",
        url=_cdn("sport_5_live_hevc"),
    ),
    Channel(
        id="sport_5_max",
        name="ספורט 5 מקס",
        name_en="Sport 5 Max",
        category="sport",
        url=_cdn("sport_5_max"),
    ),
    Channel(
        id="sport_5_4k",
        name="ספורט 5 4K",
        name_en="Sport 5 4K",
        category="sport",
        url=_cdn("sport_5_4k"),
    ),
    # ── YES Sport ──────────────────────────────────────────────────────────────
    Channel(
        id="yes_sport1",
        name="YES ספורט 1",
        name_en="YES Sport 1",
        category="yes",
        url="https://nextbet7.tv/kanal-izle/yes-1",
        needs_extraction=True,
    ),
    Channel(
        id="yes_sport2",
        name="YES ספורט 2",
        name_en="YES Sport 2",
        category="yes",
        url="https://nextbet7.tv/kanal-izle/yes-2",
        needs_extraction=True,
    ),
    Channel(
        id="yes_sport3",
        name="YES ספורט 3",
        name_en="YES Sport 3",
        category="yes",
        url="https://nextbet7.tv/kanal-izle/yes-3",
        needs_extraction=True,
    ),
    Channel(
        id="yes_sport4",
        name="YES ספורט 4",
        name_en="YES Sport 4",
        category="yes",
        url="https://nextbet7.tv/kanal-izle/yes-4",
        needs_extraction=True,
    ),
    # ── ONE ────────────────────────────────────────────────────────────────────
    Channel(
        id="one_1",
        name="ONE 1",
        name_en="ONE 1",
        category="one",
        url=_cdn("one_1"),
    ),
    Channel(
        id="one_2",
        name="ONE 2",
        name_en="ONE 2",
        category="one",
        url=_cdn("one_2"),
    ),
    Channel(
        id="one_doco",
        name="ONE דוקו",
        name_en="ONE Doco",
        category="one",
        url=_cdn("one_doco"),
    ),
    Channel(
        id="one_edge",
        name="ONE אדג'",
        name_en="ONE Edge",
        category="one",
        url=_cdn("one_edge"),
    ),
    # ── VIVA ───────────────────────────────────────────────────────────────────
    Channel(
        id="viva",
        name="VIVA",
        name_en="VIVA",
        category="viva",
        url=_cdn("viva"),
    ),
    Channel(
        id="viva_plus",
        name="VIVA פלוס",
        name_en="VIVA Plus",
        category="viva",
        url=_cdn("viva_plus"),
    ),
    # ── Reality & Content ──────────────────────────────────────────────────────
    Channel(
        id="erez_nehederet",
        name="ארץ נהדרת",
        name_en="Eretz Nehederet",
        category="reality",
        url=_cdn("erez_nehederet"),
    ),
    Channel(
        id="vamos",
        name="וואמוס",
        name_en="Vamos",
        category="reality",
        url=_cdn("vamos"),
    ),
    # ── Music & Entertainment ──────────────────────────────────────────────────
    Channel(
        id="music24",
        name="מיוזיק 24",
        name_en="Music 24",
        category="music",
        url=_cdn("music24"),
    ),
    Channel(
        id="music_il",
        name="מיוזיק IL",
        name_en="Music IL",
        category="music",
        url=_cdn("music_il"),
    ),
    Channel(
        id="karaoke",
        name="ערוץ הקריוקי",
        name_en="Karaoke Channel",
        category="music",
        url=_cdn("karaoke"),
    ),
    # ── Kids ───────────────────────────────────────────────────────────────────
    Channel(
        id="yoyo",
        name="יויו",
        name_en="Yoyo",
        category="kids",
        url=_cdn("yoyo"),
    ),
    Channel(
        id="logi",
        name="לוגי",
        name_en="Logi",
        category="kids",
        url=_cdn("logi"),
    ),
    Channel(
        id="yalduti",
        name="ילדותי",
        name_en="Yalduti",
        category="kids",
        url=_cdn("yalduti"),
    ),
    Channel(
        id="junior",
        name="ג'וניור",
        name_en="Junior",
        category="kids",
        url=_cdn("junior"),
    ),
    Channel(
        id="fomo",
        name="FOMO",
        name_en="FOMO",
        category="kids",
        url=_cdn("fomo"),
    ),
    # ── Lifestyle ──────────────────────────────────────────────────────────────
    Channel(
        id="foody",
        name="פודי",
        name_en="Foody",
        category="lifestyle",
        url=_cdn("foody"),
    ),
    Channel(
        id="beautyz",
        name="ביוטיז",
        name_en="Beautyz",
        category="lifestyle",
        url=_cdn("beautyz"),
    ),
    Channel(
        id="daystar",
        name="דייסטאר",
        name_en="Daystar",
        category="lifestyle",
        url=_cdn("daystar"),
    ),
    Channel(
        id="a_plus",
        name="A פלוס",
        name_en="A Plus",
        category="lifestyle",
        url=_cdn("a_plus"),
    ),
    # ── Movies ─────────────────────────────────────────────────────────────────
    Channel(
        id="30a_classic_movies",
        name="קלאסיקות 30A",
        name_en="30A Classic Movies",
        category="movies",
        url="https://30a-tv.com/feeds/pzaz/30atvmovies.m3u8",
    ),
]

CHANNELS_BY_ID: dict[str, Channel] = {ch.id: ch for ch in CHANNELS}


def get_channels_by_category(category: str) -> list[Channel]:
    """Return all channels belonging to the given category."""
    return [ch for ch in CHANNELS if ch.category == category]
