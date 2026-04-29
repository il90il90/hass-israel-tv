"""Israel TV integration for Home Assistant."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .proxy import YesSportPlaylistView, YesSportSegmentView

PLATFORMS: list[str] = []

_LOGGER = logging.getLogger(__name__)

_VIEWS_REGISTERED = False

# The card JS is copied to www/ so it's served at /local/israel_tv/...
# /local/ is HA's built-in mapping for the www/ config directory — always works.
_CARD_LOCAL_URL = "/local/israel_tv/israel-tv-card.js"
_CARD_SRC = Path(__file__).parent / "frontend" / "israel-tv-card.js"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Israel TV component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Israel TV from a config entry."""
    global _VIEWS_REGISTERED  # noqa: PLW0603

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    if not _VIEWS_REGISTERED:
        hass.http.register_view(YesSportPlaylistView())
        hass.http.register_view(YesSportSegmentView())

        # Register the logos static path so thumbnail URLs keep working
        logos_path = Path(__file__).parent / "logos"
        try:
            from homeassistant.components.http import StaticPathConfig  # noqa: PLC0415
            await hass.http.async_register_static_paths([
                StaticPathConfig(
                    url_path="/israel_tv/logos",
                    path=logos_path,
                    cache_headers=True,
                ),
            ])
        except (ImportError, AttributeError):
            hass.http.register_static_path(
                "/israel_tv/logos", str(logos_path), cache_headers=True
            )

        # Copy the Lovelace card JS to www/israel_tv/ so HA serves it at
        # /local/israel_tv/israel-tv-card.js — no custom static path needed.
        www_dir = Path(hass.config.path("www")) / "israel_tv"
        www_dir.mkdir(parents=True, exist_ok=True)
        dest = www_dir / "israel-tv-card.js"
        shutil.copy2(_CARD_SRC, dest)
        _LOGGER.debug("Copied Lovelace card to %s", dest)

        # Register with the HA frontend so the card appears in the card picker
        # automatically — no manual resource entry required.
        try:
            from homeassistant.components.frontend import add_extra_js_url  # noqa: PLC0415
            add_extra_js_url(hass, _CARD_LOCAL_URL)
            _LOGGER.debug("Registered Lovelace resource: %s", _CARD_LOCAL_URL)
        except Exception:  # noqa: BLE001
            _LOGGER.warning(
                "Could not auto-register Lovelace resource. "
                "Add '%s' manually under Settings → Dashboards → Resources.",
                _CARD_LOCAL_URL,
            )

        _VIEWS_REGISTERED = True
        _LOGGER.debug("Israel TV views and Lovelace card registered")

    _LOGGER.debug("Israel TV integration loaded (entry_id=%s)", entry.entry_id)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    hass.data[DOMAIN].pop(entry.entry_id, None)
    return True
