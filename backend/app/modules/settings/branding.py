"""Colour helpers: palette generation and contrast (WCAG 2.x)."""

DARK_TEXT = "#111827"
LIGHT_TEXT = "#ffffff"

# How far each shade moves from the base colour (which is shade 600).
LIGHTER_SHADES = {50: 0.92, 100: 0.84, 200: 0.68, 300: 0.50, 400: 0.30, 500: 0.12}
DARKER_SHADES = {700: 0.15, 800: 0.30, 900: 0.45, 950: 0.60}


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def mix(color: str, other: str, amount: float) -> str:
    """Blend `color` toward `other`. amount 0 = color, 1 = other."""
    first, second = hex_to_rgb(color), hex_to_rgb(other)
    blended = tuple(round(a + (b - a) * amount) for a, b in zip(first, second))
    return rgb_to_hex(blended)


def _channel(value: int) -> float:
    scaled = value / 255
    if scaled <= 0.03928:
        return scaled / 12.92
    return ((scaled + 0.055) / 1.055) ** 2.4


def luminance(color: str) -> float:
    r, g, b = hex_to_rgb(color)
    return 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)


def contrast_ratio(first: str, second: str) -> float:
    """WCAG contrast ratio, from 1 (none) to 21 (black on white)."""
    lighter, darker = sorted((luminance(first), luminance(second)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def readable_text_color(background: str) -> str:
    """Return white or near-black, whichever reads better on `background`."""
    if contrast_ratio(background, LIGHT_TEXT) >= contrast_ratio(background, DARK_TEXT):
        return LIGHT_TEXT
    return DARK_TEXT


def build_palette(base: str) -> dict[str, str]:
    """Generate shades 50-950 from one base colour (used as shade 600)."""
    palette = {str(shade): mix(base, "#ffffff", amt) for shade, amt in LIGHTER_SHADES.items()}
    palette["600"] = base.lower()
    palette.update({str(shade): mix(base, "#000000", amt) for shade, amt in DARKER_SHADES.items()})
    return dict(sorted(palette.items(), key=lambda item: int(item[0])))