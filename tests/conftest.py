"""Shared fixtures: answers recorded from an ENTRIQ FL.60 (Wi-Fi data replaced)."""

from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.skylight_lamp.const import DOMAIN

HOST = "192.0.2.10"
BASE = f"http://{HOST}/scheduleSettings"

ANSWERS = {
    "g0": (
        "45004E00540052004900510036003000\t45004E0054002E0046002E0036003000\tA1B2C3D4E5F6\t1\t\t0"
    ),
    "g1": "\n1\t2026\t10\t24\t11\t15\t00",
    "gt1": "\n19000\t412\t118\t0\t0\t80.1\t59\t888\t1",
    "g30": "\n1\t1\t3\t5",
    "g31": "9;45;0;56;0:10;45;0;56;20:11;45;0;6;55:15;45;0;6;55:17;30;0;56;0:",
    "g4": "home-net\t1\tsecret-password\thome-net\t-57\t0\t0\t1\t3\t",
    "gu2": "\n3540",
}


def mock_lamp(aioclient_mock: AiohttpClientMocker, **overrides: str) -> None:
    """Register the lamp's read commands (and the write commands) on the mocker."""
    for command, answer in {**ANSWERS, **overrides}.items():
        aioclient_mock.get(f"{BASE}?ctrl={command}", text=answer)
    aioclient_mock.get(f"{BASE}?params=9", text="Lamp is turned off.")
    aioclient_mock.get(f"{BASE}?params=a", text="Lamp is turned on.")
    aioclient_mock.get(f"{BASE}?params=c9001", text="Demo mode started.")
    aioclient_mock.get(f"{BASE}?params=6", text="Schedule has been stored.")


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable custom_components in tests."""


@pytest.fixture
def config_entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN, title="ENTRIQ60", data={"host": HOST}, unique_id="a1:b2:c3:d4:e5:f6"
    )
