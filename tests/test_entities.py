"""Entities and the commands they send."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.skylight_lamp.const import OPT_COLOUR, OPT_INTENSITY

from .conftest import BASE, mock_lamp

LIGHT = "light.entriq60"
MANUAL_ANSWER = "LED_PWM all channels diagnostic."


READS = {"g0", "g1", "gt1", "g30", "g31", "g4", "gu2"}


def sent(aioclient_mock: AiohttpClientMocker) -> list[str]:
    """Write commands (params=... or a non-read ctrl=...) sent to the lamp."""
    commands = []
    for call in aioclient_mock.mock_calls:
        query = call[1].query
        if "params" in query:
            commands.append(f"params={query['params']}")
        elif query.get("ctrl") not in READS:
            commands.append(f"ctrl={query['ctrl']}")
    return commands


async def setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_states_in_schedule_mode(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    mock_lamp(aioclient_mock)
    await setup(hass, config_entry)
    assert config_entry.state is ConfigEntryState.LOADED

    light = hass.states.get(LIGHT)
    assert light.state == "on"
    assert light.attributes["brightness"] == round(37.5 * 255 / 100)
    assert light.attributes["mode"] == "auto"
    assert light.attributes["effect"] is None
    # colour of the schedule point running at 11:15 (10:45, colour 56 = F7)
    assert light.attributes["rgb_color"] == (247, 203, 226)
    assert len(light.attributes["effect_list"]) == 60
    assert hass.states.get("select.entriq60_mode").state == "schedule"
    # the colour last set on the lamp (gt1), also when it came from SLcontrol
    assert hass.states.get("select.entriq60_colour").state == "f10"
    assert hass.states.get("number.entriq60_intensity").state == "100.0"
    assert hass.states.get("sensor.entriq60_schedule_level").state == "37.5"
    points = hass.states.get("sensor.entriq60_schedule_level").attributes["points"]
    assert points[2] == {"time": "11:45", "intensity": 55.0, "colour": "A7"}
    assert hass.states.get("sensor.entriq60_wi_fi_signal").state == "-57"
    switch = hass.states.get("switch.entriq60_keep_manual_mode_on")
    assert switch.state == "off"
    assert switch.attributes["manual_seconds_left"] == 3540
    # nothing of the Wi-Fi status apart from the signal ends up in the states
    for state in hass.states.async_all():
        assert "secret-password" not in str(state.attributes)


async def test_manual_and_demo_modes(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(config_entry, options={OPT_INTENSITY: 40.0})
    mock_lamp(aioclient_mock, g30="\n2\t0\t6\t0", gu2="\n-10")
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    light = hass.states.get(LIGHT)
    assert light.state == "on"
    assert light.attributes["brightness"] == round(40 * 255 / 100)
    assert light.attributes["effect"] == "f10"
    assert light.attributes["rgb_color"] == (245, 194, 66)
    assert hass.states.get("select.entriq60_mode").state == "manual"
    switch = hass.states.get("switch.entriq60_keep_manual_mode_on")
    assert switch.state == "on"
    assert "manual_seconds_left" not in switch.attributes

    aioclient_mock.clear_requests()
    mock_lamp(aioclient_mock, g30="\n3\t0\t6\t1")
    await config_entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(LIGHT).state == "on"
    assert hass.states.get("select.entriq60_mode").state == "demo"


async def test_off_mode(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    mock_lamp(aioclient_mock, g30="\n0\t0\t3\t0")
    await setup(hass, config_entry)
    assert hass.states.get(LIGHT).state == "off"
    assert hass.states.get("select.entriq60_mode").state == "off"


async def test_turn_on_with_brightness_and_effect(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    mock_lamp(aioclient_mock)
    aioclient_mock.get(f"{BASE}?ctrl=7440h0i0j6k0l40m", text=MANUAL_ANSWER)
    aioclient_mock.get(f"{BASE}?ctrl=740h4i36j0k59l40m", text=MANUAL_ANSWER)
    await setup(hass, config_entry)

    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": LIGHT, "brightness_pct": 40, "effect": "a1"},
        blocking=True,
    )
    assert config_entry.options[OPT_COLOUR] == 0
    assert config_entry.options[OPT_INTENSITY] == 40.0

    aioclient_mock.mock_calls.clear()
    # orange on the colour wheel -> F10 amber
    await hass.services.async_call(
        "light", "turn_on", {"entity_id": LIGHT, "rgb_color": [255, 128, 0]}, blocking=True
    )
    await hass.services.async_call("light", "turn_on", {"entity_id": LIGHT}, blocking=True)
    # the colour comes back from the lamp (gt1 still says 59 in this mock)
    assert sent(aioclient_mock) == ["ctrl=740h4i36j0k59l40m", "ctrl=740h4i36j0k59l40m"]


async def test_colour_and_intensity_entities(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    mock_lamp(aioclient_mock)
    aioclient_mock.get(f"{BASE}?ctrl=7480h20i0j24k1l80m", text=MANUAL_ANSWER)
    aioclient_mock.get(f"{BASE}?ctrl=740h3i27j0k59l30m", text=MANUAL_ANSWER)
    await setup(hass, config_entry)
    aioclient_mock.mock_calls.clear()

    config_entry.runtime_data.async_set_updated_data(
        config_entry.runtime_data.data.__class__(
            **{**config_entry.runtime_data.data.__dict__, "manual_colour": None}
        )
    )
    hass.config_entries.async_update_entry(config_entry, options={OPT_INTENSITY: 80.0})
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": "select.entriq60_colour", "option": "a2"},
        blocking=True,
    )
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": "number.entriq60_intensity", "value": 30},
        blocking=True,
    )
    assert [c for c in sent(aioclient_mock) if c.startswith("ctrl=74")] == [
        "ctrl=7480h20i0j24k1l80m",
        "ctrl=740h3i27j0k59l30m",
    ]


async def test_mode_select_switch_and_button(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    mock_lamp(aioclient_mock)
    aioclient_mock.get(f"{BASE}?ctrl=gu3", text="ManualMode set as default.")
    aioclient_mock.get(f"{BASE}?ctrl=gu1", text="ManualMode set for 1 hour.")
    await setup(hass, config_entry)
    aioclient_mock.mock_calls.clear()

    await hass.services.async_call("light", "turn_off", {"entity_id": LIGHT}, blocking=True)
    for option in ("demo", "schedule"):
        await hass.services.async_call(
            "select",
            "select_option",
            {"entity_id": "select.entriq60_mode", "option": option},
            blocking=True,
        )
    await hass.services.async_call(
        "button", "press", {"entity_id": "button.entriq60_resume_schedule"}, blocking=True
    )
    switch = "switch.entriq60_keep_manual_mode_on"
    await hass.services.async_call("switch", "turn_on", {"entity_id": switch}, blocking=True)
    await hass.services.async_call("switch", "turn_off", {"entity_id": switch}, blocking=True)
    assert sent(aioclient_mock) == [
        "params=9",
        "params=c9001",
        "params=a",
        "params=a",
        "ctrl=gu3",
        "params=6",
        "ctrl=gu1",
        "params=6",
    ]


async def test_rejected_command_raises(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    mock_lamp(aioclient_mock)
    aioclient_mock.get(f"{BASE}?ctrl=740h10i90j0k59l100m", text="Unknown command.")
    await setup(hass, config_entry)
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call("light", "turn_on", {"entity_id": LIGHT}, blocking=True)


async def test_lamp_unreachable_on_setup(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    aioclient_mock.get(f"{BASE}?ctrl=g0", status=500)
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.SETUP_RETRY
