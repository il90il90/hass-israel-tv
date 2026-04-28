"""Israel TV integration for Home Assistant."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .proxy import YesSportPlaylistView, YesSportSegmentView

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

    # Register the YES Sport HLS proxy views once per HA instance lifetime
    if not _VIEWS_REGISTERED:
        hass.http.register_view(YesSportPlaylistView())
        hass.http.register_view(YesSportSegmentView())
        _VIEWS_REGISTERED = True
        _LOGGER.debug("YES Sport HLS proxy views registered")

    _LOGGER.debug("Israel TV integration loaded (entry_id=%s)", entry.entry_id)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    hass.data[DOMAIN].pop(entry.entry_id, None)
    return True
