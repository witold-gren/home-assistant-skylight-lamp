"""Selects: lamp mode (schedule / manual / demo / off) and manual colour."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import LampMode
from .colours import COLOUR_LABELS, colour_label
from .coordinator import SkylightConfigEntry
from .entity import SkylightEntity

PARALLEL_UPDATES = 1

OPTIONS: dict[str, LampMode] = {
    "schedule": LampMode.AUTO,
    "manual": LampMode.MANUAL,
    "demo": LampMode.DEMO,
    "off": LampMode.OFF,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SkylightConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities([SkylightModeSelect(coordinator), SkylightColourSelect(coordinator)])


class SkylightModeSelect(SkylightEntity, SelectEntity):
    """Working mode of the lamp."""

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "mode")
        self._attr_options = list(OPTIONS)

    @property
    def current_option(self) -> str | None:
        mode = self.coordinator.data.mode
        return next((key for key, value in OPTIONS.items() if value is mode), None)

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_set_mode(OPTIONS[option])


class SkylightColourSelect(SkylightEntity, SelectEntity):
    """Colour of the SLcontrol picker (A1 ... F10) used in manual mode."""

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "colour")
        self._attr_options = list(COLOUR_LABELS)

    @property
    def current_option(self) -> str | None:
        return colour_label(self.coordinator.colour)

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_set_manual(colour=COLOUR_LABELS.index(option))
