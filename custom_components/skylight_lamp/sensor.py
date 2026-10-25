"""Sensors: what the schedule asks for now, Wi-Fi signal and lamp clock."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, SIGNAL_STRENGTH_DECIBELS_MILLIWATT, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import LampState
from .colours import colour_label
from .coordinator import SkylightConfigEntry
from .entity import SkylightEntity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class SkylightSensorDescription(SensorEntityDescription):
    value_fn: Callable[[LampState], Any]
    attrs_fn: Callable[[LampState], dict[str, Any]] | None = None


def _schedule_attrs(state: LampState) -> dict[str, Any]:
    return {
        "points": [
            {
                "time": f"{p.seconds // 3600:02d}:{p.seconds // 60 % 60:02d}",
                "intensity": p.intensity,
                "colour": (colour_label(p.colour) or str(p.colour)).upper(),
            }
            for p in state.schedule
        ],
        "active_point": state.active_point,
    }


def _clock(state: LampState) -> str | None:
    clock: datetime | None = state.clock
    return clock.strftime("%Y-%m-%d %H:%M:%S") if clock else None


SENSORS: tuple[SkylightSensorDescription, ...] = (
    SkylightSensorDescription(
        key="schedule_level",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: state.schedule_level(),
        attrs_fn=_schedule_attrs,
    ),
    SkylightSensorDescription(
        key="wifi_signal",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda state: state.rssi,
    ),
    SkylightSensorDescription(
        key="lamp_clock",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=_clock,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SkylightConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(SkylightSensor(coordinator, description) for description in SENSORS)


class SkylightSensor(SkylightEntity, SensorEntity):
    entity_description: SkylightSensorDescription

    def __init__(self, coordinator, description: SkylightSensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.attrs_fn is None:
            return None
        return self.entity_description.attrs_fn(self.coordinator.data)
