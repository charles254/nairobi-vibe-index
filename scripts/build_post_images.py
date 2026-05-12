"""Generate 5 narrative-card post images for Facebook + Instagram.

1080x1080 squares (FB feed-ideal AND IG-native ratio). Each card has the
NVI gradient + brand mark + a big headline + supporting copy. Day-rotated
accent colors keep the feed visually varied without breaking the brand.

The 2 missing days (Fri, Sat) are intentionally dashboard screenshots —
those posts work better with the actual product visible.

Output:
  web/social/post-wed.png
  web/social/post-thu.png
  web/social/post-sun.png
  web/social/post-mon.png
  web/social/post-tue.png
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Script lives at web/scripts/; output goes to web/social/
WEB_DIR = Path(__file__).resolve().parent.parent

# Shared palette — must match web/template.html
BG_TOP   = (13, 10, 24)
BG_MID   = (7, 8, 13)
BG_BOT   = (10, 16, 32)
MAGENTA  = (255, 45, 146)
CYAN     = (0, 214, 255)
YELLOW   = (255, 204, 0)
ORANGE   = (255, 140, 51)
TEXT     = (232, 237, 247)
TEXT_DIM = (136, 150, 184)
TEXT_FAINT = (77, 88, 120)


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    candidates = {
        "sans":     ["arialbd.ttf",  "C:/Windows/Fonts/arialbd.ttf"],
        "sans_reg": ["arial.ttf",    "C:/Windows/Fonts/arial.ttf"],
        "mono":     ["consolab.ttf", "C:/Windows/Fonts/consolab.ttf"],
        "mono_reg": ["consola.ttf",  "C:/Windows/Fonts/consola.ttf"],
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


def draw_card(
    out_name: str,
    *,
    day_label: str,
    headline: list[str],         # 1-2 lines, big
    headline_size: int,          # px font size
    body: list[str],             # 1-3 lines of supporting copy
    accent: tuple[int, int, int],# accent color for headline + dot
    callout: str | None = None,  # optional emphasized line (specific names, etc.)
) -> None:
    W = H = 1080
    img = vertical_gradient((W, H), [(0.0, BG_TOP), (0.5, BG_MID), (1.0, BG_BOT)])
    img = img.convert("RGBA")
    # Glow toward the accent color, tinting the card
    img = Image.alpha_composite(img, radial_glow((W, H), (W // 4, H // 4), 700, accent, 90))
    img = Image.alpha_composite(img, radial_glow((W, H), (W, H), 700, CYAN, 50))
    d = ImageDraw.Draw(img)

    # --- Header (top bar) ---
    d.ellipse([60, 60, 84, 84], fill=accent)
    d.text((100, 56), "NVI . NAIROBI VIBE INDEX",
           font=font("mono", 24), fill=accent)
    d.text((W - 60, 56), day_label.upper(),
           font=font("mono", 24), fill=TEXT_DIM, anchor="rt")

    # --- Headline (centered block) ---
    f_h = font("mono", headline_size)
    # Pre-measure to vertically center the block
    line_heights = [d.textbbox((0, 0), ln, font=f_h)[3] for ln in headline]
    total_h = sum(line_heights) + (len(headline) - 1) * 12
    # Anchor headline vertically a bit above center
    y = (H // 2) - (total_h // 2) - 100
    for ln in headline:
        d.text((W // 2, y), ln, font=f_h, fill=accent, anchor="mt")
        y += d.textbbox((0, 0), ln, font=f_h)[3] + 12

    # --- Body copy under headline ---
    f_b = font("sans", 36)
    body_y = y + 50
    for ln in body:
        d.text((W // 2, body_y), ln, font=f_b, fill=TEXT, anchor="mt")
        body_y += 50

    # --- Optional callout ---
    if callout:
        d.text((W // 2, body_y + 30), callout,
               font=font("mono", 30), fill=accent, anchor="mt")

    # --- Footer ---
    d.text((W // 2, H - 90), "nairobivibe.com",
           font=font("mono", 32), fill=CYAN, anchor="mt")
    d.line([(W // 2 - 100, H - 50), (W // 2 + 100, H - 50)], fill=TEXT_FAINT, width=1)

    out = WEB_DIR / "social" / out_name
    out.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out, "PNG", optimize=True)
    print(f"Wrote {out}  ({out.stat().st_size:,} bytes)")


def draw_data_card(
    out_name: str,
    *,
    day_label: str,
    time_label: str,
    citywide: str,                # "72%"
    citywide_color: tuple[int, int, int],
    status: str,                  # "HIGH"
    status_color: tuple[int, int, int],
    tracked: str,                 # "175 / 177  +248"
    hottest: str,                 # "Tribeka Bar & Grill"
    alcoblow: bool = False,       # if True, show alcoblow safety panel
) -> None:
    """Mimic the live dashboard hero — for the data-drop posts (Fri, Sat).

    Same look as the live site so anyone seeing the post immediately
    recognizes 'oh that's the NVI dashboard view'. Generated cleanly
    instead of screenshot-cropped so it scales to 1080x1080 perfectly.
    """
    W = H = 1080
    img = vertical_gradient((W, H), [(0.0, BG_TOP), (0.5, BG_MID), (1.0, BG_BOT)])
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, radial_glow((W, H), (W // 4, 0), 720, MAGENTA, 90))
    img = Image.alpha_composite(img, radial_glow((W, H), (W, H), 720, CYAN, 60))
    d = ImageDraw.Draw(img)

    # --- Header (pixel-art NVI logo, smaller) ---
    # Big bold NVI in mono (matches profile pic — readable at small sizes)
    d.text((60, 60), "NVI", font=font("mono", 130), fill=MAGENTA)
    d.text((60, 200), "NAIROBI . VIBE . INDEX",
           font=font("mono", 22), fill=CYAN)

    # --- Status line (like the live site) ---
    d.ellipse([60, 260, 80, 280], fill=MAGENTA)
    d.text((96, 256), f"{day_label.upper()}  .  {time_label}  .  NAIROBI",
           font=font("mono", 24), fill=TEXT_DIM)

    # --- 4-stat hero block ---
    box_y = 330
    box_h = 270
    d.rounded_rectangle([60, box_y, W - 60, box_y + box_h],
                        radius=14, fill=(14, 16, 25), outline=(28, 34, 55), width=1)

    # Vertical divider lines between cells
    cell_w = (W - 120) // 4
    for i in range(1, 4):
        x = 60 + i * cell_w
        d.line([(x, box_y + 30), (x, box_y + box_h - 30)],
               fill=(28, 34, 55), width=1)

    f_label = font("mono", 16)
    f_value_big = font("mono", 64)
    f_value_med = font("mono", 38)
    f_value_sm  = font("sans", 28)

    # CITYWIDE NVI
    cx = 60 + cell_w // 2
    d.text((cx, box_y + 50), "CITYWIDE NVI", font=f_label, fill=TEXT_FAINT, anchor="mt")
    d.text((cx, box_y + 95), citywide, font=f_value_big, fill=citywide_color, anchor="mt")

    # STATUS
    cx = 60 + cell_w + cell_w // 2
    d.text((cx, box_y + 50), "STATUS", font=f_label, fill=TEXT_FAINT, anchor="mt")
    d.text((cx, box_y + 105), status, font=f_value_med, fill=status_color, anchor="mt")

    # TRACKED OPEN
    cx = 60 + cell_w * 2 + cell_w // 2
    d.text((cx, box_y + 50), "TRACKED OPEN", font=f_label, fill=TEXT_FAINT, anchor="mt")
    d.text((cx, box_y + 105), tracked, font=font("mono", 30), fill=TEXT, anchor="mt")

    # HOTTEST
    cx = 60 + cell_w * 3 + cell_w // 2
    d.text((cx, box_y + 50), "HOTTEST", font=f_label, fill=TEXT_FAINT, anchor="mt")
    # Truncate venue name if too long
    h_short = hottest if len(hottest) <= 16 else hottest[:14] + ".."
    d.text((cx, box_y + 105), h_short, font=f_value_sm, fill=TEXT, anchor="mt")

    # --- Optional Alcoblow panel ---
    if alcoblow:
        ab_y = box_y + box_h + 30
        d.rounded_rectangle([60, ab_y, W - 60, ab_y + 150],
                            radius=14, fill=(40, 8, 20), outline=(255, 51, 85, 100), width=2)
        d.text((90, ab_y + 30), "DON'T DRINK & DRIVE",
               font=font("mono", 22), fill=(255, 51, 85))
        d.text((90, ab_y + 70), "Alcoblow checkpoints active tonight on",
               font=f_value_sm, fill=TEXT)
        d.text((90, ab_y + 105), "Mombasa Rd . Thika Rd . Lang'ata Rd",
               font=font("mono", 22), fill=TEXT_DIM)
        footer_y = ab_y + 200
    else:
        footer_y = box_y + box_h + 80
        # Add a tagline if no alcoblow panel
        d.text((W // 2, footer_y - 50), "The data the city is too drunk to notice.",
               font=font("sans", 30), fill=TEXT, anchor="mt")

    # Footer
    d.text((W // 2, H - 100), "nairobivibe.com",
           font=font("mono", 32), fill=CYAN, anchor="mt")
    d.line([(W // 2 - 100, H - 60), (W // 2 + 100, H - 60)],
           fill=TEXT_FAINT, width=1)

    out = WEB_DIR / "social" / out_name
    out.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out, "PNG", optimize=True)
    print(f"Wrote {out}  ({out.stat().st_size:,} bytes)")


def main() -> None:
    # Wednesday — magenta — midweek truth
    draw_card(
        "post-wed.png",
        day_label="Wednesday",
        headline=["MIDWEEK", "TRUTH"],
        headline_size=200,
        body=["Most of Nairobi sleeps on Wednesdays.",
              "Three spots punch above their weight."],
        callout="Sankara . Kiza . Brew Bistro",
        accent=MAGENTA,
    )

    # Thursday — cyan — Friday forecast
    draw_card(
        "post-thu.png",
        day_label="Thursday",
        headline=["TOMORROW", "PEAKS"],
        headline_size=200,
        body=["Friday's heatmap is in.",
              "Westlands fills first. CBD goes red 23:30."],
        callout="Plan your route now.",
        accent=CYAN,
    )

    # Sunday — cyan/dim — recap
    draw_card(
        "post-sun.png",
        day_label="Sunday",
        headline=["LAST NIGHT", "IN DATA"],
        headline_size=180,
        body=["Saturday's hottest spot revealed.",
              "Plus 3 surprises from the heatmap."],
        callout="Recap on the dashboard.",
        accent=CYAN,
    )

    # Monday — yellow — week ahead
    draw_card(
        "post-mon.png",
        day_label="Monday",
        headline=["YOUR WEEK", "OF VIBES"],
        headline_size=170,
        body=["Mon karaoke. Tue lounges. Wed Tribeka.",
              "Thu rooftops. Fri the whole city."],
        callout="One screen. Whole week planned.",
        accent=YELLOW,
    )

    # Tuesday — magenta — slow night smart play
    draw_card(
        "post-tue.png",
        day_label="Tuesday",
        headline=["TUESDAY", "IS DEAD"],
        headline_size=200,
        body=["80% of Nairobi closed.",
              "The 20% alive — that's where the talk is."],
        callout="No queues. No surge. No shouting.",
        accent=MAGENTA,
    )

    # Friday — live data drop (mimics the dashboard hero)
    # Edit these numbers each week to match the actual live site
    draw_data_card(
        "post-fri.png",
        day_label="Friday",
        time_label="20:30 EAT",
        citywide="72%",
        citywide_color=ORANGE,
        status="HIGH",
        status_color=ORANGE,
        tracked="175 / 177",
        hottest="Tribeka Bar",
        alcoblow=False,
    )

    # Saturday — live data drop with alcoblow safety panel
    draw_data_card(
        "post-sat.png",
        day_label="Saturday",
        time_label="22:00 EAT",
        citywide="84%",
        citywide_color=(255, 51, 85),  # red
        status="CRAZY",
        status_color=(255, 51, 85),
        tracked="176 / 177",
        hottest="Kiza Lounge",
        alcoblow=True,
    )


if __name__ == "__main__":
    main()
