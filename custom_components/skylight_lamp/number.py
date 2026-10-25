"""Number: manual intensity (%).

Changing it switches the lamp to manual mode with the current colour.
"""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import SkylightConfigEntry
from .entity import SkylightEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SkylightConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([SkylightIntensityNumber(entry.runtime_data)])


class SkylightIntensityNumber(SkylightEntity, NumberEntity):
    """Intensity used in manual mode."""

    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "intensity")

    @property
    def native_value(self) -> float:
        return self.coordinator.intensity

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_manual(intensity=value)
