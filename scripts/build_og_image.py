"""Render og-image.png (1200x630) for social previews.

Mirrors the layout of web/og-image.svg but in Pillow so it can run on
machines without libcairo. Uses Windows default fonts (Arial / Consolas)
which are close enough to the live site's Inter / JetBrains Mono for OG
preview purposes.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1200, 630
# Script lives at web/scripts/; output goes to web/og-image.png
WEB_DIR = Path(__file__).resolve().parent.parent
OUT = WEB_DIR / "og-image.png"

# Colors (match web/template.html)
BG_TOP    = (13, 10, 24)     # #0d0a18
BG_MID    = (7, 8, 13)       # #07080d
BG_BOT    = (10, 16, 32)     # #0a1020
MAGENTA   = (255, 45, 146)   # #ff2d92
CYAN      = (0, 214, 255)    # #00d6ff
TEXT      = (232, 237, 247)  # #e8edf7
TEXT_DIM  = (136, 150, 184)  # #8896b8
ORANGE    = (255, 140, 51)   # #ff8c33
YELLOW    = (255, 204, 0)    # #ffcc00
RED       = (255, 51, 85)    # #ff3355
CARD_BG   = (14, 16, 25)     # #0e1019
CARD_BORD = (28, 34, 55)     # #1c2237


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    """Best-effort font lookup with a few Windows fallbacks."""
    candidates = {
        "sans":      ["arialbd.ttf", "arial.ttf", "C:/Windows/Fonts/arialbd.ttf"],
        "sans_reg":  ["arial.ttf",   "C:/Windows/Fonts/arial.ttf"],
        "mono":      ["consolab.ttf","consola.ttf","C:/Windows/Fonts/consolab.ttf"],
    }[name]
    for c in candidates:
        try:
            return ImageFont.truetype(c, size)
        except OSError:
            continue
    return ImageFont.load_default()


def vertical_gradient(size: tuple[int, int], stops: list[tuple[float, tuple[int, int, int]]]) -> Image.Image:
    """Build a vertical gradient image. stops = [(0.0, color), (1.0, color), ...]."""
    w, h = size
    img = Image.new("RGB", size, stops[0][1])
    px = img.load()
    for y in range(h):
        t = y / max(1, h - 1)
        # find segment
        for i in range(len(stops) - 1):
            t0, c0 = stops[i]
            t1, c1 = stops[i + 1]
            if t0 <= t <= t1:
                k = (t - t0) / max(1e-9, t1 - t0)
                r = int(c0[0] + (c1[0] - c0[0]) * k)
                g = int(c0[1] + (c1[1] - c0[1]) * k)
                b = int(c0[2] + (c1[2] - c0[2]) * k)
                for x in range(w):
                    px[x, y] = (r, g, b)
                break
    return img


def radial_glow(size: tuple[int, int], center: tuple[int, int], radius: int, color: tuple[int, int, int], peak_alpha: int) -> Image.Image:
    """Soft radial glow as RGBA, suitable for alpha_composite."""
    w, h = size
    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    px = glow.load()
    cx, cy = center
    r2 = radius * radius
    for y in range(h):
        for x in range(w):
            dx = x - cx
            dy = y - cy
            d2 = dx * dx + dy * dy
            if d2 < r2:
                t = 1.0 - (d2 / r2) ** 0.5
                a = int(peak_alpha * t * t)
                px[x, y] = (*color, a)
    return glow


def main() -> None:
    img = vertical_gradient((W, H), [(0.0, BG_TOP), (0.5, BG_MID), (1.0, BG_BOT)])

    # Soft glows (lower alpha than SVG since gradient overlay is approximate)
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, radial_glow((W, H), (240, 0), 720, MAGENTA, 90))
    img = Image.alpha_composite(img, radial_glow((W, H), (1200, 630), 720, CYAN, 65))

    d = ImageDraw.Draw(img)

    # Pulse dot + brand line
    d.ellipse([72, 92, 88, 108], fill=MAGENTA)
    d.text((104, 88), "NVI . NAIROBI VIBE INDEX", font=font("mono", 22), fill=MAGENTA)

    # Big NVI pixel logo (rect blocks at translate(80, 200))
    blocks = [
        # N
        (0, 0, 36, 180),
        (48, 0, 36, 36), (48, 36, 36, 36), (48, 72, 36, 36),
        (96, 108, 36, 36),
        (144, 0, 36, 180),
        # V
        (216, 0, 36, 36),
        (252, 36, 36, 36),
        (288, 0, 36, 36),
        (252, 72, 36, 108),
    ]
    ox, oy = 80, 200
    for (x, y, w, h) in blocks:
        d.rectangle([ox + x, oy + y, ox + x + w, oy + y + h], fill=MAGENTA)

    # Subtitle
    d.text((80, 425), "The data the city is too drunk to notice.", font=font("sans", 40), fill=TEXT)
    d.text((80, 480), "Live nightlife intelligence - vibe scores for Nairobi's", font=font("sans_reg", 22), fill=TEXT_DIM)
    d.text((80, 510), "clubs, bars, and restaurants.", font=font("sans_reg", 22), fill=TEXT_DIM)

    # Right card: gauge
    gx, gy = 870, 240
    d.rounded_rectangle([gx, gy, gx + 240, gy + 160], radius=14, fill=CARD_BG, outline=CARD_BORD, width=1)
    d.text((gx + 120, gy + 22), "CITYWIDE VIBE", font=font("mono", 12), fill=TEXT_DIM, anchor="mt")
    d.text((gx + 120, gy + 50), "72%", font=font("mono", 72), fill=TEXT, anchor="mt")
    d.text((gx + 120, gy + 130), "HIGH", font=font("mono", 14), fill=ORANGE, anchor="mt")

    # Right card: bar chart
    bx, by = 870, 430
    d.rounded_rectangle([bx, by, bx + 240, by + 100], radius=10, fill=CARD_BG, outline=CARD_BORD, width=1)
    d.text((bx + 14, by + 12), "POPULAR TIMES", font=font("mono", 10), fill=TEXT_DIM)
    bars = [
        (0, 48, 12, CYAN), (12, 50, 10, CYAN), (24, 46, 14, CYAN),
        (36, 40, 20, YELLOW), (48, 32, 28, YELLOW),
        (60, 22, 38, ORANGE), (72, 12, 48, ORANGE),
        (84, 4, 56, RED), (96, 0, 60, RED),
        (108, 6, 54, ORANGE), (120, 14, 46, ORANGE),
        (132, 22, 38, YELLOW), (144, 36, 24, YELLOW),
        (156, 44, 16, CYAN), (168, 50, 10, CYAN),
        (180, 52, 8, CYAN), (192, 54, 6, CYAN), (204, 50, 10, CYAN),
    ]
    base_x, base_y = bx + 14, by + 32
    for (x, y, h, col) in bars:
        d.rounded_rectangle([base_x + x, base_y + y, base_x + x + 9, base_y + y + h], radius=2, fill=col)

    img = img.convert("RGB")
    img.save(OUT, "PNG", optimize=True)
    print(f"Wrote {OUT}  ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
