"""Colour table of the SLcontrol colour picker (rows A-F, columns 1-10).

Colour index = row * 10 + column (A1 = 0 ... F10 = 59), the number the lamp
stores and shows in schedules. Columns go from cool (blue) to warm (yellow),
rows from a green tint (A) to a pink tint (F); B5 is neutral white. Each
colour is the ratio of the four LED channels; the app multiplies it by the
intensity (%). Recorded from the commands SLcontrol 1.1.39 sends to an
ENTRIQ FL.60. Colour names are in the translations (keys "a1" ... "f10").
"""

from __future__ import annotations

import colorsys
import math
from typing import Final

ROWS: Final = "ABCDEF"
COLUMNS: Final = 10

COLOUR_RATIOS: Final[tuple[tuple[float, float, float, float], ...]] = (
    (1.0, 0.0, 0.0, 0.15),  #  0 A1 blue
    (1.0, 0.25, 0.0, 0.3),  #  1 A2 light blue
    (1.0, 0.5, 0.0, 0.5),  #  2 A3 sky blue
    (1.0, 0.88, 0.0, 0.78),  #  3 A4 ice blue
    (1.0, 1.0, 0.0, 0.7),  #  4 A5 mint white
    (0.95, 0.95, 0.0, 0.95),  #  5 A6 green-tinted white
    (1.0, 0.35, 0.0, 1.0),  #  6 A7 pale green
    (0.75, 0.0, 0.0, 1.0),  #  7 A8 pistachio
    (0.2, 0.2, 0.05, 1.0),  #  8 A9 light lime
    (0.2, 0.0, 0.1, 1.0),  #  9 A10 lime
    (1.0, 0.5, 0.0, 0.1),  # 10 B1 cornflower
    (1.0, 0.5, 0.0, 0.2),  # 11 B2 light cornflower
    (1.0, 1.0, 0.0, 0.35),  # 12 B3 lavender blue
    (1.0, 1.0, 0.1, 0.7),  # 13 B4 cool white
    (0.93, 0.93, 0.2, 0.9),  # 14 B5 neutral white
    (0.9, 0.9, 0.38, 0.92),  # 15 B6 cream white
    (0.8, 0.44, 0.38, 1.0),  # 16 B7 vanilla
    (0.5, 0.25, 0.35, 1.0),  # 17 B8 pale yellow
    (0.25, 0.1, 0.35, 1.0),  # 18 B9 lemon
    (0.15, 0.05, 0.35, 1.0),  # 19 B10 yellow-green
    (1.0, 1.0, 0.0, 0.05),  # 20 C1 indigo
    (1.0, 1.0, 0.0, 0.1),  # 21 C2 lavender
    (1.0, 1.0, 0.0, 0.2),  # 22 C3 pale lavender
    (1.0, 1.0, 0.3, 0.5),  # 23 C4 lavender white
    (0.9, 0.9, 0.52, 0.72),  # 24 C5 pinkish white
    (0.9, 0.9, 0.48, 0.78),  # 25 C6 warm white
    (0.65, 0.65, 0.78, 0.93),  # 26 C7 light cream
    (0.4, 0.4, 0.75, 0.9),  # 27 C8 cream
    (0.2, 0.2, 0.75, 0.9),  # 28 C9 straw
    (0.08, 0.08, 0.75, 0.9),  # 29 C10 yellow
    (1.0, 1.0, 0.05, 0.0),  # 30 D1 violet
    (1.0, 1.0, 0.1, 0.0),  # 31 D2 lilac
    (1.0, 1.0, 0.2, 0.0),  # 32 D3 light lilac
    (1.0, 1.0, 0.42, 0.22),  # 33 D4 lilac white
    (0.9, 0.9, 0.66, 0.46),  # 34 D5 pink white
    (0.9, 0.9, 0.69, 0.44),  # 35 D6 peach white
    (0.6, 0.6, 0.91, 0.76),  # 36 D7 beige
    (0.4, 0.4, 0.9, 0.75),  # 37 D8 light apricot
    (0.2, 0.2, 0.9, 0.75),  # 38 D9 light gold
    (0.08, 0.08, 0.95, 0.75),  # 39 D10 golden yellow
    (0.5, 1.0, 0.0, 0.0),  # 40 E1 purple
    (0.5, 1.0, 0.2, 0.0),  # 41 E2 light purple
    (1.0, 1.0, 0.35, 0.0),  # 42 E3 heather
    (1.0, 1.0, 0.48, 0.05),  # 43 E4 light heather
    (0.85, 0.85, 0.8, 0.2),  # 44 E5 pale violet
    (0.8, 0.8, 0.85, 0.3),  # 45 E6 powder pink
    (0.4, 0.8, 0.9, 0.35),  # 46 E7 light salmon
    (0.25, 0.5, 0.9, 0.35),  # 47 E8 salmon
    (0.1, 0.25, 0.9, 0.35),  # 48 E9 apricot
    (0.05, 0.1, 0.9, 0.35),  # 49 E10 gold
    (0.0, 1.0, 0.0, 0.0),  # 50 F1 magenta
    (0.25, 1.0, 0.3, 0.0),  # 51 F2 orchid
    (0.5, 1.0, 0.5, 0.0),  # 52 F3 light orchid
    (0.65, 1.0, 0.6, 0.0),  # 53 F4 pink lilac
    (0.85, 0.85, 0.85, 0.0),  # 54 F5 pale pink lilac
    (0.75, 0.75, 0.9, 0.15),  # 55 F6 pink mist
    (0.35, 0.9, 0.9, 0.0),  # 56 F7 pink
    (0.0, 0.75, 0.9, 0.0),  # 57 F8 rose
    (0.0, 0.35, 0.9, 0.0),  # 58 F9 peach
    (0.0, 0.1, 0.9, 0.0),  # 59 F10 amber
)

# How SLcontrol draws each colour in its picker (hex RGB, same order). Used to
# show the colour in Home Assistant; the light itself is set by COLOUR_RATIOS.
COLOUR_RGB: Final[tuple[str, ...]] = (
    # A1-A10
    "bac4fa",
    "c9d7fc",
    "d5e7fd",
    "e5f5fe",
    "f2fef7",
    "edfee7",
    "ecfed5",
    "ebfec7",
    "e8fe98",
    "d9fe58",
    # B1-B10
    "bab7fa",
    "c6c9fb",
    "d2d8fc",
    "e6ecfd",
    "fefefe",
    "fcffed",
    "faffd9",
    "fcfec7",
    "fdff99",
    "ebfe53",
    # C1-C10
    "b7a4f9",
    "c8c1fa",
    "d7d1fb",
    "ece5fd",
    "fdf3fb",
    "fdf5ec",
    "fef9ce",
    "fdf3c6",
    "fdf297",
    "ffff54",
    # D1-D10
    "c191f8",
    "c9b8fa",
    "dac6fb",
    "eedefd",
    "fbe8f8",
    "fceee3",
    "fbebcd",
    "fbe5c5",
    "fae495",
    "fcee4f",
    # E1-E10
    "cc85f8",
    "ceadfa",
    "debffb",
    "efd2fc",
    "f9dafc",
    "fae2eb",
    "f9dad3",
    "f8d7cf",
    "f8d8a6",
    "f8d748",
    # F1-F10
    "d26bf7",
    "db9af9",
    "ebb7fa",
    "f6c5fb",
    "f7cffc",
    "f8d3f3",
    "f7cbe2",
    "f6c7d8",
    "f6c8b3",
    "f5c242",
)

# Option / effect keys, translated to "A1 · Blue" ... "F10 · Amber"
COLOUR_LABELS: Final[tuple[str, ...]] = tuple(
    f"{ROWS[index // COLUMNS].lower()}{index % COLUMNS + 1}" for index in range(len(COLOUR_RATIOS))
)


def colour_label(index: int | None) -> str | None:
    """Key (e.g. "f10") of a colour index, None when out of range."""
    if index is None or not 0 <= index < len(COLOUR_LABELS):
        return None
    return COLOUR_LABELS[index]


def channel_levels(colour: int, intensity: float) -> tuple[float, float, float, float]:
    """Levels (%) of the four channels for a colour at the given intensity."""
    return tuple(round(ratio * intensity, 2) for ratio in COLOUR_RATIOS[colour])  # type: ignore[return-value]


def colour_rgb(index: int) -> tuple[int, int, int]:
    """RGB of a colour as drawn in the SLcontrol picker."""
    value = COLOUR_RGB[index]
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def _hue_point(rgb: tuple[int, int, int], saturation_scale: float) -> tuple[float, float]:
    """Point on the colour wheel: angle = hue, radius = saturation."""
    hue, saturation, _ = colorsys.rgb_to_hsv(*(value / 255 for value in rgb))
    radius = min(1.0, saturation / saturation_scale)
    return radius * math.cos(hue * 2 * math.pi), radius * math.sin(hue * 2 * math.pi)


_PALETTE_SATURATION: Final = max(
    colorsys.rgb_to_hsv(*(value / 255 for value in colour_rgb(index)))[1]
    for index in range(len(COLOUR_RGB))
)
_PALETTE_POINTS: Final = tuple(
    _hue_point(colour_rgb(index), _PALETTE_SATURATION) for index in range(len(COLOUR_RGB))
)


def nearest_colour(rgb: tuple[int, int, int]) -> int:
    """Palette colour closest to any RGB colour (e.g. picked on the colour wheel).

    The palette is pastel, so the wheel's saturation is scaled to the palette's
    range before comparing hue and saturation.
    """
    exact = "{:02x}{:02x}{:02x}".format(*rgb)
    if exact in COLOUR_RGB:
        return COLOUR_RGB.index(exact)
    x, y = _hue_point(rgb, 1.0)
    return min(
        range(len(_PALETTE_POINTS)),
        key=lambda index: math.dist(_PALETTE_POINTS[index], (x, y)),
    )
