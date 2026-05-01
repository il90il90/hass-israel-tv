"""Israel TV integration for Home Assistant."""

from __future__ import annotations

import logging
from pathlib import Path

import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .proxy import YesSportPlaylistView, YesSportSegmentView

# Integration has no YAML configuration — all setup is done via config entries.
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

_LOGGER = logging.getLogger(__name__)

# Track whether the HTTP views have been registered (they survive config reloads)
_VIEWS_REGISTERED = False


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Israel TV component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Israel TV from a config entry."""
    global _VIEWS_REGISTERED  # noqa: PLW0603

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Register HTTP views and static assets once per HA instance lifetime
    if not _VIEWS_REGISTERED:
        hass.http.register_view(YesSportPlaylistView())
        hass.http.register_view(YesSportSegmentView())
        # async_register_static_paths (HA ≥ 2024.x) — fall back to the
        # older synchronous API for installations running an earlier version.
        logos_path = Path(__file__).parent / "logos"
        try:
            from homeassistant.components.http import StaticPathConfig  # noqa: PLC0415
            await hass.http.async_register_static_paths([
                StaticPathConfig(
                    url_path="/israel_tv/logos",
                    path=logos_path,
                    cache_headers=True,
                )
            ])
        except (ImportError, AttributeError):
            hass.http.register_static_path(
                "/israel_tv/logos", str(logos_path), cache_headers=True
            )
        _VIEWS_REGISTERED = True
        _LOGGER.debug("YES Sport HLS proxy views and logo assets registered")

    _LOGGER.debug("Israel TV integration loaded (entry_id=%s)", entry.entry_id)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    hass.data[DOMAIN].pop(entry.entry_id, None)
    return True
