"""Parsing of the lamp's answers."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re

import pytest

from custom_components.skylight_lamp.api import (
    LampMode,
    LampState,
    SkylightError,
    decode_hex_utf16,
    format_level,
    manual_command,
    parse_clock,
    parse_description,
    parse_led_status,
    parse_schedule,
    parse_schedule_status,
    parse_wifi_status,
)
from custom_components.skylight_lamp.colours import (
    COLOUR_LABELS,
    COLOUR_RGB,
    channel_levels,
    colour_label,
    colour_rgb,
    nearest_colour,
)

from .conftest import ANSWERS


def test_description() -> None:
    info = parse_description(ANSWERS["g0"])
    assert info.name == "ENTRIQ60"
    assert info.model == "ENT.F.60"
    assert info.mac == "A1B2C3D4E5F6"


def test_description_invalid() -> None:
    with pytest.raises(SkylightError):
        parse_description("Unknown command.")


def test_decode_hex_utf16_keeps_plain_text() -> None:
    assert decode_hex_utf16("not-hex") == "not-hex"


def test_clock() -> None:
    assert parse_clock(ANSWERS["g1"]) == datetime(2026, 10, 24, 11, 15, 0)
    assert parse_clock("") is None


def test_led_status() -> None:
    frequency, outputs, colour, night_mode = parse_led_status(ANSWERS["gt1"])
    assert frequency == 19000
    assert outputs == (412.0, 118.0, 0.0, 0.0)
    assert colour == 59
    assert night_mode is True


def test_schedule_status() -> None:
    assert parse_schedule_status(ANSWERS["g30"]) == (LampMode.AUTO, True, 3)
    assert parse_schedule_status("\n2\t0\t6\t0")[0] is LampMode.MANUAL
    assert parse_schedule_status("\n0\t0\t6\t0")[0] is LampMode.OFF
    assert parse_schedule_status("\n3\t0\t6\t1")[0] is LampMode.DEMO
    with pytest.raises(SkylightError):
        parse_schedule_status("Unknown command.")


def test_schedule() -> None:
    points = parse_schedule(ANSWERS["g31"])
    assert len(points) == 5
    assert points[0].seconds == 9 * 3600 + 45 * 60
    assert (points[2].colour, points[2].intensity) == (6, 55.0)


def test_wifi_status_drops_password() -> None:
    ssid, rssi = parse_wifi_status(ANSWERS["g4"])
    assert (ssid, rssi) == ("home-net", -57)


@pytest.mark.parametrize(
    ("time", "expected"),
    [
        ((6, 0, 0), 0.0),
        ((10, 15, 0), 10.0),
        ((11, 15, 0), 37.5),
        ((12, 0, 0), 55.0),
        ((22, 0, 0), 0.0),
    ],
)
def test_schedule_level(time: tuple[int, int, int], expected: float) -> None:
    state = LampState(
        mode=LampMode.AUTO,
        schedule_enabled=True,
        active_point=None,
        schedule=parse_schedule(ANSWERS["g31"]),
        clock=datetime(2026, 10, 24, *time),
        pwm_frequency=None,
        outputs=(),
        manual_colour=None,
        night_mode=None,
        manual_remaining=None,
        rssi=None,
        ssid=None,
    )
    assert state.schedule_level() == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [(50, "50"), (12.346, "12.35"), (10.736, "10.74"), (150, "100"), (-1, "0"), (0.5, "0.5")],
)
def test_format_level(value: float, expected: str) -> None:
    assert format_level(value) == expected


def test_manual_command_matches_slcontrol() -> None:
    """Same query SLcontrol sends for colour A4 at 12.2 %."""
    levels = channel_levels(3, 12.2)
    assert manual_command(levels, 3, 12.2) == "7412.2h10.74i0j9.52k3l12.2m"


@pytest.mark.parametrize(
    ("colour", "intensity", "expected"),
    [
        (0, 12.2, (12.2, 0.0, 0.0, 1.83)),
        (59, 43.1, (0.0, 4.31, 38.79, 0.0)),
        (1, 40, (40.0, 10.0, 0.0, 12.0)),
    ],
)
def test_channel_levels(
    colour: int, intensity: float, expected: tuple[float, float, float, float]
) -> None:
    assert channel_levels(colour, intensity) == expected


def test_colour_labels() -> None:
    assert len(COLOUR_LABELS) == 60
    assert (COLOUR_LABELS[0], COLOUR_LABELS[9], COLOUR_LABELS[59]) == ("a1", "a10", "f10")
    assert colour_label(20) == "c1"
    assert colour_label(60) is None


@pytest.mark.parametrize(
    ("rgb", "expected"),
    [((255, 255, 255), "b5"), ((0, 0, 255), "c1"), ((255, 128, 0), "f10"), ((255, 0, 255), "f1")],
)
def test_nearest_colour(rgb: tuple[int, int, int], expected: str) -> None:
    assert COLOUR_LABELS[nearest_colour(rgb)] == expected


def test_palette_colours_map_to_themselves() -> None:
    assert colour_rgb(14) == (254, 254, 254)
    assert nearest_colour(colour_rgb(59)) == 59


def test_card_uses_the_same_palette() -> None:
    card = (
        Path(__file__).parents[1] / "custom_components/skylight_lamp/www/skylight-lamp-card.js"
    ).read_text()
    table = card.split("var COLOURS = [", 1)[1].split("]", 1)[0]
    assert re.findall(r'"([0-9a-f]{6})"', table) == list(COLOUR_RGB)
