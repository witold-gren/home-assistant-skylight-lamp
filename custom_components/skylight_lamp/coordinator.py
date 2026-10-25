"""Coordinator: polls the lamp and keeps the manual colour and intensity."""

from __future__ import annotations

from collections.abc import Awaitable
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import LampInfo, LampMode, LampState, SkylightClient, SkylightError
from .colours import COLOUR_RATIOS, channel_levels
from .const import (
    DEFAULT_COLOUR,
    DEFAULT_INTENSITY,
    DOMAIN,
    OPT_COLOUR,
    OPT_INTENSITY,
    UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

type SkylightConfigEntry = ConfigEntry[SkylightCoordinator]


def _valid_colour(value: object) -> bool:
    return isinstance(value, int) and 0 <= value < len(COLOUR_RATIOS)


class SkylightCoordinator(DataUpdateCoordinator[LampState]):
    """Reads the lamp state every UPDATE_INTERVAL and sends commands."""

    config_entry: SkylightConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: SkylightConfigEntry,
        client: SkylightClient,
        info: LampInfo,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.client = client
        self.info = info

    async def _async_update_data(self) -> LampState:
        try:
            return await self.client.async_get_state()
        except SkylightError as err:
            raise UpdateFailed(str(err)) from err

    @property
    def colour(self) -> int:
        """Manual colour index: the lamp's own (also set by SLcontrol), else the stored one."""
        if self.data is not None and _valid_colour(self.data.manual_colour):
            return self.data.manual_colour  # type: ignore[return-value]
        stored = self.config_entry.options.get(OPT_COLOUR)
        return stored if _valid_colour(stored) else DEFAULT_COLOUR

    @property
    def intensity(self) -> float:
        """Manual intensity (%) last chosen in Home Assistant."""
        stored = self.config_entry.options.get(OPT_INTENSITY)
        if isinstance(stored, int | float) and 0 <= stored <= 100:
            return float(stored)
        return DEFAULT_INTENSITY

    async def _run(self, command: Awaitable[None]) -> None:
        try:
            await command
        except SkylightError as err:
            raise HomeAssistantError(str(err)) from err
        await self.async_request_refresh()

    async def async_set_mode(self, mode: LampMode) -> None:
        if mode is LampMode.OFF:
            await self._run(self.client.async_set_off())
        elif mode is LampMode.AUTO:
            await self._run(self.client.async_set_auto())
        elif mode is LampMode.DEMO:
            await self._run(self.client.async_set_demo())
        else:
            await self.async_set_manual()

    async def async_set_manual(
        self, colour: int | None = None, intensity: float | None = None
    ) -> None:
        """Switch to manual mode; missing values are taken from the last ones."""
        colour = self.colour if colour is None else colour
        intensity = self.intensity if intensity is None else intensity
        intensity = round(min(100.0, max(0.0, intensity)), 1)
        self.hass.config_entries.async_update_entry(
            self.config_entry,
            options={**self.config_entry.options, OPT_COLOUR: colour, OPT_INTENSITY: intensity},
        )
        levels = channel_levels(colour, intensity)
        await self._run(self.client.async_set_manual(levels, colour, intensity))

    async def async_set_manual_permanent(self, permanent: bool) -> None:
        await self._run(self.client.async_set_manual_permanent(permanent))
