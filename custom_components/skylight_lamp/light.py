"""Light: the lamp as a whole, with brightness, colour and colours as effects.

Turning on (or changing brightness, colour or effect) switches the lamp to
manual mode with a colour of the SLcontrol picker (effects "a1" ... "f10",
shown with their names, e.g. "F10 · Amber") and intensity. A colour picked on
the colour wheel is matched to the closest colour of the picker; the light
shows the colour as SLcontrol draws it. Turning off sets the lamp's off mode;
use the "Mode" select or the "Resume schedule" button to go back to the
schedule.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import LampMode
from .colours import COLOUR_LABELS, colour_label, colour_rgb, nearest_colour
from .coordinator import SkylightConfigEntry
from .entity import SkylightEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SkylightConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([SkylightLight(entry.runtime_data)])


class SkylightLight(SkylightEntity, LightEntity):
    """The lamp."""

    _attr_name = None
    _attr_color_mode = ColorMode.RGB
    _attr_supported_features = LightEntityFeature.EFFECT

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "lamp")
        self._attr_supported_color_modes = {ColorMode.RGB}
        self._attr_effect_list = list(COLOUR_LABELS)

    def _level(self) -> float | None:
        """Light level (%) the lamp is set to right now."""
        state = self.coordinator.data
        if state.mode is LampMode.MANUAL:
            return self.coordinator.intensity
        if state.mode is LampMode.AUTO:
            return state.schedule_level()
        return 0.0

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data.mode is LampMode.DEMO:
            return True
        level = self._level()
        return None if level is None else level > 0

    @property
    def brightness(self) -> int | None:
        level = self._level()
        if not level:
            return None
        return max(1, round(level * 255 / 100))

    def _colour(self) -> int | None:
        """Colour the lamp shows now: manual colour, or the running schedule point's."""
        state = self.coordinator.data
        if state.mode is LampMode.MANUAL:
            return self.coordinator.colour
        if state.mode is LampMode.AUTO:
            return state.schedule_colour()
        return None

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        colour = self._colour()
        if colour_label(colour) is None:
            return None
        return colour_rgb(colour)  # type: ignore[arg-type]

    @property
    def effect(self) -> str | None:
        if self.coordinator.data.mode is LampMode.MANUAL:
            return colour_label(self.coordinator.colour)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        state = self.coordinator.data
        return {
            "mode": state.mode.name.lower(),
            "intensity": self.coordinator.intensity,
            "schedule_level": state.schedule_level(),
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        colour = None
        if (effect := kwargs.get(ATTR_EFFECT)) is not None:
            if effect not in COLOUR_LABELS:
                raise ServiceValidationError(f"Unknown colour {effect!r}")
            colour = COLOUR_LABELS.index(effect)
        elif (rgb := kwargs.get(ATTR_RGB_COLOR)) is not None:
            colour = nearest_colour(rgb)
        intensity = None
        if ATTR_BRIGHTNESS in kwargs:
            intensity = kwargs[ATTR_BRIGHTNESS] * 100 / 255
        elif self.coordinator.intensity <= 0:
            intensity = 100.0
        await self.coordinator.async_set_manual(colour, intensity)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_mode(LampMode.OFF)
