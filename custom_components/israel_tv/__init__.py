"""Israel TV integration for Home Assistant."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .proxy import YesSportPlaylistView, YesSportSegmentView

PLATFORMS: list[str] = []  # no entity platforms — widget is pure frontend

_LOGGER = logging.getLogger(__name__)

# Track whether HTTP views / static paths / card JS have been registered
_VIEWS_REGISTERED = False

# URL path at which the Lovelace card JS is served from HA's HTTP server
_CARD_URL = "/israel_tv/frontend/israel-tv-card.js"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Israel TV component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Israel TV from a config entry."""
    global _VIEWS_REGISTERED  # noqa: PLW0603

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Register HTTP views, static assets and Lovelace card — once per HA lifetime
    if not _VIEWS_REGISTERED:
        hass.http.register_view(YesSportPlaylistView())
        hass.http.register_view(YesSportSegmentView())

        logos_path    = Path(__file__).parent / "logos"
        frontend_path = Path(__file__).parent / "frontend"

        # async_register_static_paths (HA ≥ 2024.x) with fallback for older builds
        try:
            from homeassistant.components.http import StaticPathConfig  # noqa: PLC0415
            await hass.http.async_register_static_paths([
                StaticPathConfig(
                    url_path="/israel_tv/logos",
                    path=logos_path,
                    cache_headers=True,
                ),
                StaticPathConfig(
                    url_path="/israel_tv/frontend",
                    path=frontend_path,
                    cache_headers=False,  # allow hot-reload of card JS during dev
                ),
            ])
        except (ImportError, AttributeError):
            hass.http.register_static_path(
                "/israel_tv/logos", str(logos_path), cache_headers=True
            )
            hass.http.register_static_path(
                "/israel_tv/frontend", str(frontend_path), cache_headers=False
            )

        # Auto-register the card with the HA Lovelace frontend so it appears
        # in the card picker without any manual resource setup.
        try:
            from homeassistant.components.frontend import add_extra_js_url  # noqa: PLC0415
            add_extra_js_url(hass, _CARD_URL)
            _LOGGER.debug("Israel TV card registered at %s", _CARD_URL)
        except Exception:  # noqa: BLE001
            _LOGGER.warning(
                "Could not auto-register Lovelace card. "
                "Add %s manually under Dashboard → Resources.", _CARD_URL
            )

        _VIEWS_REGISTERED = True
        _LOGGER.debug("Israel TV HTTP views, static paths and Lovelace card registered")

    _LOGGER.debug("Israel TV integration loaded (entry_id=%s)", entry.entry_id)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    hass.data[DOMAIN].pop(entry.entry_id, None)
    return True
