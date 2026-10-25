"""Entity ids are English in a Polish installation; the shown names stay translated."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import slugify
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from .conftest import mock_lamp
from .test_entities import setup


def _polish_entity_ids(hass: HomeAssistant, entry_id: str) -> list[str]:
    """Entity ids that end with the Polish name (what HA builds in a Polish installation)."""
    entries = er.async_entries_for_config_entry(er.async_get(hass), entry_id)
    assert entries
    return [
        e.entity_id
        for e in entries
        if e.original_name
        and e.entity_id.split(".")[1].endswith(slugify(e.original_name))
        and not e.entity_id.split(".")[1].endswith(slugify(e.object_id_base or ""))
    ]


async def test_entity_ids_are_english(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    hass.config.language = "pl"
    mock_lamp(aioclient_mock)
    await setup(hass, config_entry)

    assert _polish_entity_ids(hass, config_entry.entry_id) == []
    mode = hass.states.get("select.entriq60_mode")
    assert mode.attributes["friendly_name"] == "ENTRIQ60 Tryb"
    registry = er.async_get(hass)
    assert registry.async_get("sensor.entriq60_lamp_clock") is not None  # disabled by default
    assert hass.states.get("light.entriq60") is not None  # named after the device
