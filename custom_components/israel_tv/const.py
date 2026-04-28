"""Constants for the Israel TV integration."""

DOMAIN = "israel_tv"
VERSION = "1.0.0"

MEDIA_SOURCE_ID = DOMAIN

# Media content type for HLS streams
HLS_MIME_TYPE = "application/x-mpegURL"

# Root identifier used when browsing the media source
ROOT_ID = "/"

# Fallback thumbnail shown for channels that have no specific logo
DEFAULT_THUMBNAIL = (
    "https://raw.githubusercontent.com/il90il90/hass-israel-tv"
    "/main/custom_components/israel_tv/icon.png"
)
