"""Render NVI brand images for Facebook (and reusable for X / IG / LinkedIn).

Outputs:
  web/social/profile-1200.png    1200x1200  (FB profile, IG square avatar)
  web/social/cover-1640x856.png  1640x856   (FB cover, with mobile-safe zone)

Both share the same palette and pixel-art NVI logo as og-image.png so
all surfaces feel like one brand. Cover keeps content in the center
820x312 safe zone (FB crops the cover differently on desktop vs mobile)
and leaves the bottom-left clear for the profile-pic overlay circle.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Script lives at web/scripts/; output goes to web/social/
WEB_DIR = Path(__file__).resolve().parent.parent

# Shared palette — must match web/template.html
BG_TOP    = (13, 10, 24)
BG_MID    = (7, 8, 13)
BG_BOT    = (10, 16, 32)
MAGENTA   = (255, 45, 146)
CYAN      = (0, 214, 255)
TEXT      = (232, 237, 247)
TEXT_DIM  = (136, 150, 184)
ORANGE    = (255, 140, 51)
YELLOW    = (255, 204, 0)
RED       = (255, 51, 85)
CARD_BG   = (14, 16, 25)
CARD_BORD = (28, 34, 55)


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    candidates = {
        "sans":     ["arialbd.ttf", "C:/Windows/Fonts/arialbd.ttf"],
        "sans_reg": ["arial.ttf",   "C:/Windows/Fonts/arial.ttf"],
        "mono":     ["consolab.ttf","C:/Windows/Fonts/consolab.ttf"],
    }[name]
    for c in candidates:
        try:
            return ImageFont.truetype(c, size)
        except OSError:
            continue
    return ImageFont.load_default()


def vertical_gradient(size, stops):
    w, h = size
    img = Image.new("RGB", size, stops[0][1])
    px = img.load()
    for y in range(h):
        t = y / max(1, h - 1)
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


def radial_glow(size, center, radius, color, peak_alpha):
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


def draw_nvi_pixels(d: ImageDraw.ImageDraw, ox: int, oy: int, unit: int, color=MAGENTA) -> int:
    """Draw the NVI pixel logo at (ox, oy) with a given unit size.
    Returns the rendered width in pixels.
    """
    blocks = [
        # N (5 cols x 5 rows in unit grid)
        (0, 0, 1, 5),
        (1, 0, 1, 1), (1, 1, 1, 1), (1, 2, 1, 1),
        (2, 3, 1, 1),
        (4, 0, 1, 5),
        # V (translated; reuses tighter glyph)
        (6, 0, 1, 1), (10, 0, 1, 1),
        (7, 1, 1, 1), (9, 1, 1, 1),
        (7, 2, 1, 1), (9, 2, 1, 1),
        (8, 3, 1, 1),
        (8, 4, 1, 1),
        # I (vertical bar)
        (12, 0, 1, 5),
    ]
    for (x, y, w, h) in blocks:
        d.rectangle([ox + x * unit, oy + y * unit,
                     ox + (x + w) * unit, oy + (y + h) * unit], fill=color)
    return 13 * unit


def build_profile() -> None:
    """Profile pic — must read as 'NVI' even at 32x32 favicon size.

    Uses bold mono typography (Consolas Bold) instead of the abstract
    pixel-art logo because the pixel letters lose legibility once
    Facebook crops the square down to a 168x168 circle and apps further
    shrink it to 32x32 in feed previews.
    """
    W = H = 1200
    img = vertical_gradient((W, H), [(0.0, BG_TOP), (0.5, BG_MID), (1.0, BG_BOT)])
    img = img.convert("RGBA")
    # Strong center glow so the letters pop on small thumbnails
    img = Image.alpha_composite(img, radial_glow((W, H), (W // 2, H // 2 - 60), 720, MAGENTA, 130))
    img = Image.alpha_composite(img, radial_glow((W, H), (W, H), 700, CYAN, 70))
    d = ImageDraw.Draw(img)

    # Big bold NVI in monospace, centered
    f_logo = font("mono", 520)
    f_sub  = font("mono", 56)
    f_tag  = font("sans_reg", 32)

    # Center the NVI text
    bbox = d.textbbox((0, 0), "NVI", font=f_logo)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    cx, cy = W // 2, H // 2 - 80
    # Drop shadow / glow ring (poor man's neon)
    for off in (12, 8, 4):
        d.text((cx, cy), "NVI", font=f_logo, fill=(255, 45, 146, 80),
               anchor="mm", stroke_width=off, stroke_fill=(255, 45, 146, 60))
    d.text((cx, cy), "NVI", font=f_logo, fill=MAGENTA, anchor="mm")

    # Subtitle
    d.text((W // 2, cy + text_h // 2 + 60),
           "NAIROBI . VIBE . INDEX",
           font=f_sub, fill=CYAN, anchor="mt")
    d.text((W // 2, cy + text_h // 2 + 140),
           "the data the city is too drunk to notice",
           font=f_tag, fill=TEXT_DIM, anchor="mt")

    # Top-left pulse dot
    d.ellipse([60, 60, 92, 92], fill=MAGENTA)

    out = WEB_DIR / "social" / "profile-1200.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out, "PNG", optimize=True)
    print(f"Wrote {out}  ({out.stat().st_size:,} bytes)")


def build_cover() -> None:
    W, H = 1640, 856
    img = vertical_gradient((W, H), [(0.0, BG_TOP), (0.5, BG_MID), (1.0, BG_BOT)])
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, radial_glow((W, H), (200, 0), 900, MAGENTA, 90))
    img = Image.alpha_composite(img, radial_glow((W, H), (1640, 856), 900, CYAN, 70))
    d = ImageDraw.Draw(img)

    # FB safe zone is center 820x312 — keep all critical content in
    # x:410..1230, y:272..584. Avoid bottom-left ~250x250 (profile overlay).

    # Brand line top-center
    f_brand = font("mono", 22)
    d.ellipse([W // 2 - 215, 60, W // 2 - 197, 78], fill=MAGENTA)
    d.text((W // 2 - 185, 56), "NVI . NAIROBI VIBE INDEX",
           font=f_brand, fill=MAGENTA)

    # NVI pixel logo, centered horizontally, in safe zone vertically
    unit = 50
    logo_w = 13 * unit
    logo_h = 5 * unit
    ox = (W - logo_w) // 2
    oy = 200
    draw_nvi_pixels(d, ox, oy, unit)

    # Tagline below logo
    f_tag = font("sans", 56)
    f_sub = font("sans_reg", 28)
    d.text((W // 2, oy + logo_h + 50), "The data the city is too drunk to notice.",
           font=f_tag, fill=TEXT, anchor="mt")
    d.text((W // 2, oy + logo_h + 130), "Live nightlife intelligence for Nairobi - 287 venues across the city.",
           font=f_sub, fill=TEXT_DIM, anchor="mt")
    d.text((W // 2, oy + logo_h + 175), "nairobivibe.com",
           font=font("mono", 26), fill=CYAN, anchor="mt")

    out = WEB_DIR / "social" / "cover-1640x856.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out, "PNG", optimize=True)
    print(f"Wrote {out}  ({out.stat().st_size:,} bytes)")


def build_x_header() -> None:
    """X / Twitter header (1500x500, 3:1).

    Different from FB cover — wider, shorter. X also overlays the
    profile circle in the bottom-left, so keep that area clear.
    """
    W, H = 1500, 500
    img = vertical_gradient((W, H), [(0.0, BG_TOP), (0.5, BG_MID), (1.0, BG_BOT)])
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, radial_glow((W, H), (300, 0), 700, MAGENTA, 100))
    img = Image.alpha_composite(img, radial_glow((W, H), (W, H), 700, CYAN, 70))
    d = ImageDraw.Draw(img)

    # Brand line top-left (out of profile-circle overlay zone)
    d.ellipse([60, 50, 80, 70], fill=MAGENTA)
    d.text((96, 46), "NVI . NAIROBI VIBE INDEX",
           font=font("mono", 22), fill=MAGENTA)

    # Big bold NVI text — right-of-center so the profile circle doesn't cover it
    f_logo = font("mono", 220)
    d.text((900, H // 2), "NVI", font=f_logo, fill=MAGENTA, anchor="mm")

    # Tagline + URL stacked under the logo (right side)
    d.text((900, 380), "The data the city is too drunk to notice.",
           font=font("sans", 28), fill=TEXT, anchor="mt")
    d.text((900, 425), "nairobivibe.com",
           font=font("mono", 26), fill=CYAN, anchor="mt")

    out = WEB_DIR / "social" / "x-header-1500x500.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out, "PNG", optimize=True)
    print(f"Wrote {out}  ({out.stat().st_size:,} bytes)")


if __name__ == "__main__":
    build_profile()
    build_cover()
    build_x_header()
