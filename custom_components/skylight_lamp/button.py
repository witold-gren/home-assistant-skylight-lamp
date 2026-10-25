"""Button: go back to the lamp's own daily schedule."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import LampMode
from .coordinator import SkylightConfigEntry
from .entity import SkylightEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SkylightConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([SkylightResumeScheduleButton(entry.runtime_data)])


class SkylightResumeScheduleButton(SkylightEntity, ButtonEntity):
    """Switch the lamp back to automatic (schedule) mode."""

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "resume_schedule")

    async def async_press(self) -> None:
        await self.coordinator.async_set_mode(LampMode.AUTO)
