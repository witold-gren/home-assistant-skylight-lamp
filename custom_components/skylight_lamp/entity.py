"""Base entity shared by all platforms."""

from __future__ import annotations

from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo, format_mac
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import SkylightCoordinator


class SkylightEntity(CoordinatorEntity[SkylightCoordinator]):
    """Entity bound to one lamp device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SkylightCoordinator, key: str) -> None:
        super().__init__(coordinator)
        info = coordinator.info
        mac = format_mac(info.mac)
        self._attr_unique_id = f"{mac}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, mac)},
            connections={(CONNECTION_NETWORK_MAC, mac)},
            manufacturer=MANUFACTURER,
            model=info.model or None,
            name=info.name or info.model or "Skylight",
        )
