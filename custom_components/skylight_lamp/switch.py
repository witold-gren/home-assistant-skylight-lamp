"""Switch: keep manual mode on instead of going back to the schedule after one hour.

This is the SLcontrol setting "Set manual mode as default" (on) / "Set schedule
mode as default" (off). The lamp stores it in its memory.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import MANUAL_PERMANENT_REMAINING
from .coordinator import SkylightConfigEntry
from .entity import SkylightEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SkylightConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([SkylightManualPermanentSwitch(entry.runtime_data)])


class SkylightManualPermanentSwitch(SkylightEntity, SwitchEntity):
    """On: manual mode stays on. Off: manual mode ends after one hour."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "manual_permanent")

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.manual_permanent

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        remaining = self.coordinator.data.manual_remaining
        if remaining is None or remaining == MANUAL_PERMANENT_REMAINING:
            return {}
        return {"manual_seconds_left": max(0, remaining)}

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_manual_permanent(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_manual_permanent(False)
