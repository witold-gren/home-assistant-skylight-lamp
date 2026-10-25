"""Client for the local HTTP API of Skylight Wi-Fi lamps (the one used by SLcontrol).

The lamp runs a small ESP32 web server on port 80. Every command is a GET
request; answers are tab separated text. Commands used here:

    /scheduleSettings?ctrl=g0   description: name, model (UTF-16 hex), MAC
    /scheduleSettings?ctrl=g1   clock: sntp, year, month, day, hour, minute, second
    /scheduleSettings?ctrl=gt1  LED status: PWM frequency, 4 channel outputs, ...
    /scheduleSettings?ctrl=g30  schedule status: mode, enabled, active point, points
    /scheduleSettings?ctrl=g31  schedule string "h;m;s;colour;intensity:" per point
    /scheduleSettings?ctrl=g4   Wi-Fi status (contains the Wi-Fi password!)
    /scheduleSettings?ctrl=gu2  seconds left in manual mode, -10 = manual is permanent
    /scheduleSettings?ctrl=gu1  manual mode ends after one hour (back to schedule)
    /scheduleSettings?ctrl=gu3  manual mode stays on
    /scheduleSettings?ctrl=74<c0>h<c1>i<c2>j<c3>k<colour>l<intensity>m
                                manual mode with channel levels in % (colour picker)
    /scheduleSettings?params=6  store settings in EEPROM
    /scheduleSettings?params=9  mode off
    /scheduleSettings?params=a  mode auto (run the stored schedule)
    /scheduleSettings?params=c9001  demo

The Wi-Fi password the lamp returns in plain text is dropped right after
parsing and never logged or stored.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum
from itertools import pairwise
import logging

import aiohttp

from .const import CHANNEL_COUNT, REQUEST_RETRIES, REQUEST_TIMEOUT

_LOGGER = logging.getLogger(__name__)

ANSWER_OFF = "Lamp is turned off."
ANSWER_AUTO = "Lamp is turned on."
ANSWER_MANUAL = "LED_PWM all channels diagnostic."
ANSWER_DEMO = "Demo mode started."
ANSWER_STORED = "Schedule has been stored."
ANSWER_MANUAL_ONE_HOUR = "ManualMode set for 1 hour."
ANSWER_MANUAL_PERMANENT = "ManualMode set as default."

# gu2 answer when manual mode does not time out
MANUAL_PERMANENT_REMAINING = -10


class SkylightError(Exception):
    """Communication with the lamp failed or the answer was unexpected."""


class LampMode(IntEnum):
    """Working mode reported by the lamp (first field of g30)."""

    OFF = 0
    AUTO = 1
    MANUAL = 2
    DEMO = 3


@dataclass(frozen=True)
class LampInfo:
    """Static description of the lamp."""

    name: str
    model: str
    mac: str


@dataclass(frozen=True)
class SchedulePoint:
    """One point of the daily schedule."""

    seconds: int
    colour: int
    intensity: float


@dataclass(frozen=True)
class LampState:
    """Everything read from the lamp in one refresh."""

    mode: LampMode
    schedule_enabled: bool
    active_point: int | None
    schedule: tuple[SchedulePoint, ...]
    clock: datetime | None
    pwm_frequency: int | None
    outputs: tuple[float, ...]
    manual_colour: int | None
    night_mode: bool | None
    manual_remaining: int | None
    rssi: int | None
    ssid: str | None

    @property
    def manual_permanent(self) -> bool | None:
        """True when manual mode stays on, False when it ends after one hour."""
        if self.manual_remaining is None:
            return None
        return self.manual_remaining == MANUAL_PERMANENT_REMAINING

    def schedule_colour(self) -> int | None:
        """Colour of the schedule point that is running at the lamp's current time."""
        if not self.schedule or self.clock is None:
            return None
        now = self.clock.hour * 3600 + self.clock.minute * 60 + self.clock.second
        points = sorted(self.schedule, key=lambda point: point.seconds)
        started = [point for point in points if point.seconds <= now]
        return (started[-1] if started else points[0]).colour

    def schedule_level(self) -> float | None:
        """Intensity (%) the schedule asks for at the lamp's current time.

        Points are linearly interpolated; before the first and after the last
        point the nearest point's value is used.
        """
        if not self.schedule or self.clock is None:
            return None
        now = self.clock.hour * 3600 + self.clock.minute * 60 + self.clock.second
        points = sorted(self.schedule, key=lambda point: point.seconds)
        if now <= points[0].seconds:
            return points[0].intensity
        for prev, nxt in pairwise(points):
            if prev.seconds <= now <= nxt.seconds:
                span = nxt.seconds - prev.seconds
                if span <= 0:
                    return nxt.intensity
                ratio = (now - prev.seconds) / span
                return round(prev.intensity + (nxt.intensity - prev.intensity) * ratio, 1)
        return points[-1].intensity


def _fields(text: str) -> list[str]:
    """Split a single-line answer into tab separated fields."""
    return text.strip().split("\t")


def _int(value: str) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _float(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def decode_hex_utf16(value: str) -> str:
    """Decode a name sent as hex encoded UTF-16LE (e.g. 45004E00... -> "EN")."""
    try:
        return bytes.fromhex(value).decode("utf-16-le").strip("\x00").strip()
    except ValueError:
        return value


def parse_description(text: str) -> LampInfo:
    """Parse the g0 answer: name, model and MAC of the lamp."""
    fields = _fields(text)
    if len(fields) < 3 or len(fields[2]) != 12:
        raise SkylightError("Unexpected description answer")
    return LampInfo(
        name=decode_hex_utf16(fields[0]),
        model=decode_hex_utf16(fields[1]),
        mac=fields[2].upper(),
    )


def parse_clock(text: str) -> datetime | None:
    """Parse the g1 answer (sntp flag, year, month, day, hour, minute, second)."""
    fields = _fields(text)
    if len(fields) < 7:
        return None
    try:
        return datetime(*(int(value) for value in fields[1:7]))
    except ValueError:
        return None


def parse_led_status(
    text: str,
) -> tuple[int | None, tuple[float, ...], int | None, bool | None]:
    """Parse gt1: PWM frequency, channel outputs, manual colour and night mode flag."""
    fields = _fields(text)
    frequency = _int(fields[0]) if fields else None
    outputs = tuple(_float(value) or 0.0 for value in fields[1 : 1 + CHANNEL_COUNT])
    colour = _int(fields[6]) if len(fields) > 6 else None
    night_mode = fields[8] == "1" if len(fields) > 8 else None
    return frequency, outputs, colour, night_mode


def parse_schedule_status(text: str) -> tuple[LampMode, bool, int | None]:
    """Parse g30: lamp mode, schedule enabled and the active schedule point."""
    fields = _fields(text)
    mode = _int(fields[0]) if fields else None
    if mode not in {item.value for item in LampMode}:
        raise SkylightError(f"Unexpected schedule status answer: {text.strip()!r}")
    enabled = len(fields) > 1 and fields[1] == "1"
    active = _int(fields[2]) if len(fields) > 2 else None
    return LampMode(mode), enabled, active


def parse_schedule(text: str) -> tuple[SchedulePoint, ...]:
    """Parse g31: points "hour;minute;second;colour;intensity" separated by ':'."""
    points = []
    for item in text.strip().split(":"):
        parts = item.split(";")
        if len(parts) < 5:
            continue
        hour, minute, second, colour = (_int(value) for value in parts[:4])
        intensity = _float(parts[4])
        if None in (hour, minute, second, colour, intensity):
            continue
        points.append(
            SchedulePoint(
                seconds=hour * 3600 + minute * 60 + second,
                colour=colour,
                intensity=intensity,
            )
        )
    return tuple(points)


def parse_wifi_status(text: str) -> tuple[str | None, int | None]:
    """Parse g4 and return (ssid, rssi). Field 2 is the Wi-Fi password: ignored."""
    fields = _fields(text)
    ssid = (fields[0] or None) if fields else None
    rssi = _int(fields[4]) if len(fields) > 4 else None
    return ssid, rssi


def format_level(value: float) -> str:
    """Level for the manual command: 0-100, at most two decimals."""
    value = min(100.0, max(0.0, float(value)))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def manual_command(levels: tuple[float, ...], colour: int, intensity: float) -> str:
    """ctrl=74 argument: four channel levels, colour index and intensity."""
    c0, c1, c2, c3 = (format_level(value) for value in levels)
    return f"74{c0}h{c1}i{c2}j{c3}k{colour}l{format_level(intensity)}m"


class SkylightClient:
    """Talks to one lamp. Requests are serialised: the lamp handles one at a time."""

    def __init__(self, session: aiohttp.ClientSession, host: str) -> None:
        self._session = session
        self.host = host
        self._lock = asyncio.Lock()

    async def _request(self, path: str) -> str:
        url = f"http://{self.host}{path}"
        last_error: Exception | None = None
        async with self._lock:
            for _ in range(REQUEST_RETRIES):
                try:
                    async with asyncio.timeout(REQUEST_TIMEOUT):
                        response = await self._session.get(url)
                        response.raise_for_status()
                        return await response.text(errors="replace")
                except (aiohttp.ClientError, TimeoutError) as err:
                    last_error = err
                    # the lamp's Wi-Fi power saving sometimes drops the first packet
                    await asyncio.sleep(0.5)
        raise SkylightError(f"Cannot reach lamp at {self.host}: {last_error!r}")

    async def _ctrl(self, command: str) -> str:
        return await self._request(f"/scheduleSettings?ctrl={command}")

    async def _command(self, query: str, expected: str) -> None:
        answer = (await self._request(f"/scheduleSettings?{query}")).strip()
        if answer != expected:
            raise SkylightError(f"Lamp rejected command {query!r}: {answer!r}")

    async def _params(self, command: str, expected: str) -> None:
        await self._command(f"params={command}", expected)

    async def async_get_info(self) -> LampInfo:
        return parse_description(await self._ctrl("g0"))

    async def async_get_state(self) -> LampState:
        mode, enabled, active = parse_schedule_status(await self._ctrl("g30"))
        frequency, outputs, colour, night_mode = parse_led_status(await self._ctrl("gt1"))
        remaining = _int((await self._ctrl("gu2")).strip())
        schedule = parse_schedule(await self._ctrl("g31"))
        clock = parse_clock(await self._ctrl("g1"))
        try:
            ssid, rssi = parse_wifi_status(await self._ctrl("g4"))
        except SkylightError:
            ssid, rssi = None, None
        return LampState(
            mode=mode,
            schedule_enabled=enabled,
            active_point=active,
            schedule=schedule,
            clock=clock,
            pwm_frequency=frequency,
            outputs=outputs,
            manual_colour=colour,
            night_mode=night_mode,
            manual_remaining=remaining,
            rssi=rssi,
            ssid=ssid,
        )

    async def async_set_off(self) -> None:
        await self._params("9", ANSWER_OFF)

    async def async_set_auto(self) -> None:
        await self._params("a", ANSWER_AUTO)

    async def async_set_demo(self) -> None:
        await self._params("c9001", ANSWER_DEMO)

    async def async_set_manual(
        self, levels: tuple[float, ...], colour: int, intensity: float
    ) -> None:
        """Switch to manual mode the way the SLcontrol colour picker does."""
        await self._command(f"ctrl={manual_command(levels, colour, intensity)}", ANSWER_MANUAL)

    async def async_set_manual_permanent(self, permanent: bool) -> None:
        """Keep manual mode on, or let it fall back to the schedule after one hour."""
        if permanent:
            await self._command("ctrl=gu3", ANSWER_MANUAL_PERMANENT)
        else:
            await self._command("ctrl=gu1", ANSWER_MANUAL_ONE_HOUR)
        await self._params("6", ANSWER_STORED)
