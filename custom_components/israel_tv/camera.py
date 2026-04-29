"""Camera platform for Israel TV — one live-streaming entity per channel.

Each channel is exposed as a standard HA camera entity.  HA's built-in
stream integration fetches the HLS playlist via ffmpeg and re-serves it
over the local network — the same mechanism used for IP security cameras.

Dashboard usage
---------------
1. Open a dashboard → Add Card → Picture Entity (or Picture Glance).
2. Pick the entity that matches the channel you want, e.g.
   ``camera.israel_tv_kan_11``.
3. Done — the channel starts playing inside the card, just like a camera.

No extra configuration is required beyond selecting the entity.
"""

from __future__ import annotations

import logging

from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .channels import CHANNELS, Channel
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up one camera entity for every channel in CHANNELS."""
    entities = [IsraelTVCamera(hass, ch) for ch in CHANNELS]
    async_add_entities(entities)
    _LOGGER.debug("Registered %d Israel TV camera entities", len(entities))


class IsraelTVCamera(Camera):
    """A camera entity that streams a single Israeli TV channel.

    Static channels (broadcast, Sport 5, etc.) use the direct CloudFront
    CDN URL as the stream source.

    YES Sport channels (Sport 1-4) require a short-lived token and a
    specific CDN Referer header for segment requests.  They are routed
    through our local HLS proxy (proxy.py) which handles all of that
    transparently — ffmpeg only talks to localhost.
    """

    _attr_has_entity_name = True
    _attr_supported_features = CameraEntityFeature.STREAM
    _attr_is_streaming = True
    _attr_is_on = True

    def __init__(self, hass: HomeAssistant, channel: Channel) -> None:
        """Initialise the camera entity for *channel*."""
        super().__init__()
        self.hass = hass
        self._channel = channel
        self._attr_unique_id = f"{DOMAIN}_{channel.id}"
        self._attr_name = channel.name
        # Show the channel logo in the HA entity registry / Lovelace cards.
        self._attr_entity_picture = channel.thumbnail

    @property
    def device_info(self) -> DeviceInfo:
        """All channel entities belong to a single virtual Israel TV device."""
        return DeviceInfo(
            identifiers={(DOMAIN, "israel_tv_channels")},
            name="Israel TV",
            manufacturer="Israel TV",
            model="Live Channels",
        )

    async def stream_source(self) -> str | None:
        """Return the HLS playlist URL that HA's stream integration will open.

        For YES Sport channels the proxy URL is constructed using localhost
        so that ffmpeg (running inside HA) can reach the proxy server-side
        without going through the external network.
        """
        if self._channel.channel_type == "yes_sport":
            port = getattr(self.hass.http, "server_port", 8123)
            return (
                f"http://localhost:{port}"
                f"/api/israel_tv/stream/{self._channel.id}/playlist.m3u8"
            )
        return self._channel.url

    async def async_camera_image(
        self,
        width: int | None = None,
        height: int | None = None,
    ) -> bytes | None:
        """Live TV channels do not provide static snapshots."""
        return None
