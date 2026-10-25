"""Skylight Lamp: local control of Skylight Wi-Fi aquarium lamps (SLcontrol)."""

from __future__ import annotations

from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .api import SkylightClient, SkylightError
from .const import DOMAIN
from .coordinator import SkylightConfigEntry, SkylightCoordinator
from .frontend import async_register_card

PLATFORMS: list[Platform] = [
    Platform.BUTTON,
    Platform.LIGHT,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Serve the Lovelace card."""
    await async_register_card(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: SkylightConfigEntry) -> bool:
    """Set up the lamp from a config entry."""
    client = SkylightClient(async_get_clientsession(hass), entry.data[CONF_HOST])
    try:
        info = await client.async_get_info()
    except SkylightError as err:
        raise ConfigEntryNotReady(str(err)) from err
    coordinator = SkylightCoordinator(hass, entry, client, info)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SkylightConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
