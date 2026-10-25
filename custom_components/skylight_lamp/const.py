"""Constants for the Skylight Lamp integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "skylight_lamp"
MANUFACTURER: Final = "Skylight"

UPDATE_INTERVAL: Final = timedelta(seconds=30)
REQUEST_TIMEOUT: Final = 8
REQUEST_RETRIES: Final = 3

# The lamp has four PWM channels; colours are mixes of all four.
CHANNEL_COUNT: Final = 4

# Manual colour and intensity last chosen in Home Assistant (config entry options).
OPT_COLOUR: Final = "colour"
OPT_INTENSITY: Final = "intensity"
DEFAULT_COLOUR: Final = 5  # A6: all channels almost equal
DEFAULT_INTENSITY: Final = 100.0

# Lovelace card shipped with the integration (custom:skylight-lamp-card)
CARD_URL_BASE: Final = "/skylight_lamp_static"
CARD_FILENAME: Final = "skylight-lamp-card.js"
