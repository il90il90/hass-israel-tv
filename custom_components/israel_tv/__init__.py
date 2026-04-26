"""Israel TV integration for Home Assistant."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .proxy import IsraelTVHLSProxyView

_LOGGER = logging.getLogger(__name__)

# Shared dict: channel_id → current real HLS URL (updated by media_source.py)
# Registered once at component setup so the proxy view can always read it.
STREAM_URL_STORE: dict[str, str] = {}


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Israel TV component and register the HLS proxy view."""
    hass.data.setdefault(DOMAIN, {})
    hass.http.register_view(IsraelTVHLSProxyView(STREAM_URL_STORE))
    _LOGGER.debug("Israel TV HLS proxy view registered")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Israel TV from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data
    _LOGGER.debug("Israel TV integration loaded (entry_id=%s)", entry.entry_id)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    hass.data[DOMAIN].pop(entry.entry_id, None)
    return True
