#!/usr/bin/env python3
"""Animated GIF: a man on a cliff edge lies back, then it begins to rain.

Scene (side profile, dusk):
  * A tall, slim man with an afro sits on the edge of a cliff, legs hanging
    over the drop, gently swaying.
  * He slowly leans back and lies down on his back on the cliff top.
  * Once he's settled, rain begins to fall and steadily intensifies while the
    sky darkens.

The whole thing is drawn procedurally with Pillow -- no external assets.
"""

import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 480, 360
FRAMES = 100
FPS = 20

X_EDGE = 268          # x of the cliff edge (drop-off)
Y_TOP = 250           # y of the cliff-top surface
HIP = (232, 244)      # hip / pivot point (just above the surface)

FIG_COL = (17, 16, 24)   # silhouette colour

random.seed(11)


def ease(t):
    return t * t * (3 - 2 * t)


def clamp01(t):
    return max(0.0, min(1.0, t))


def lerp(a, b, t):
    return a + (b - a) * t


def lerp2(p, q, t):
    return (lerp(p[0], q[0], t), lerp(p[1], q[1], t))


# ---------------------------------------------------------------- sky --------
def sky(rain):
    """Vertical dusk gradient that turns grey and dark as `rain` rises (0..1)."""
    # (anchor_y_fraction, clear_rgb, rainy_rgb)
    stops = [
        (0.00, (46, 40, 92),   (32, 34, 44)),
        (0.48, (120, 92, 140), (60, 64, 76)),
        (0.55, (236, 138, 96), (86, 90, 102)),
        (0.72, (150, 104, 118),(66, 70, 80)),
        (1.00, (92, 78, 96),   (48, 50, 58)),
    ]
    ys = np.array([s[0] for s in stops])
    clear = np.array([s[1] for s in stops], dtype=float)
    rainy = np.array([s[2] for s in stops], dtype=float)
    cols = clear + (rainy - clear) * rain

    frac = np.linspace(0, 1, H)
    r = np.interp(frac, ys, cols[:, 0])
    g = np.interp(frac, ys, cols[:, 1])
    b = np.interp(frac, ys, cols[:, 2])
    grad = np.stack([r, g, b], axis=1)                      # (H,3)
    arr = np.repeat(grad[:, None, :], W, axis=1)            # (H,W,3)
    return Image.fromarray(arr.astype(np.uint8), "RGB")


def draw_cliff(img, rain):
    """Opaque rock mass in the lower-left, with a lit top edge and grass."""
    d = ImageDraw.Draw(img, "RGBA")
    rock = (26, 24, 34)
    rock_lit = tuple(int(c * (1 - 0.35 * rain)) for c in (78, 66, 74))

    top_pts = [
        (0, Y_TOP + 4), (60, Y_TOP - 2), (140, Y_TOP + 2),
        (210, Y_TOP - 3), (X_EDGE - 20, Y_TOP), (X_EDGE, Y_TOP + 2),
    ]
    poly = top_pts + [(X_EDGE + 6, H), (0, H)]
    d.polygon(poly, fill=rock)

    # a thin lit rim along the cliff top catching the dusk light
    d.line(top_pts, fill=rock_lit, width=3)

    # jagged right face of the cliff
    face = [(X_EDGE, Y_TOP + 2), (X_EDGE + 6, 300), (X_EDGE - 10, 330),
            (X_EDGE + 2, H), (0, H), (0, Y_TOP)]
    d.polygon(face, fill=rock)

    # a few grass tufts near the edge
    grass = tuple(int(c * (1 - 0.3 * rain)) for c in (60, 78, 52))
    for gx in range(150, X_EDGE, 12):
        h = random.Random(gx).randint(5, 10)
        d.line([gx, Y_TOP, gx - 2, Y_TOP - h], fill=grass, width=2)
        d.line([gx, Y_TOP, gx + 2, Y_TOP - h + 1], fill=grass, width=2)


# ------------------------------------------------------------- figure --------
def capsule(d, p1, p2, width, col):
    d.line([p1, p2], fill=col, width=width)
    r = width / 2
    for (x, y) in (p1, p2):
        d.ellipse([x - r, y - r, x + r, y + r], fill=col)


def get_pose(t, f, idle):
    """Compute joint positions. t: lie progress 0..1, f: frame, idle: 0..1."""
    breath = math.sin(f * 0.28) * idle * 1.2

    # torso angle from vertical: ~10deg (sitting, leaning back a touch) -> 90deg
    torso_ang = math.radians(lerp(10, 90, t))
    dirx, diry = -math.sin(torso_ang), -math.cos(torso_ang)
    torso_len = 84 + breath
    shoulder = (HIP[0] + dirx * torso_len, HIP[1] + diry * torso_len)

    neck, head_r = 12, 15
    head_c = (shoulder[0] + dirx * (neck + head_r),
              shoulder[1] + diry * (neck + head_r))

    # legs: thigh along/over the edge, shin hanging down with a gentle sway
    knee = (X_EDGE + 12, Y_TOP + 1)
    sway = math.radians(9 * math.sin(f * 0.22) * idle)
    shin_len = 64
    foot = (knee[0] + math.sin(sway) * shin_len,
            knee[1] + math.cos(sway) * shin_len)

    # near arm: props back on the surface when sitting, rests by side when lying
    hand_sit = (HIP[0] - 30, Y_TOP)
    hand_lie = (shoulder[0] + 20, Y_TOP)
    hand = lerp2(hand_sit, hand_lie, t)
    elbow = ((shoulder[0] + hand[0]) / 2, (shoulder[1] + hand[1]) / 2 + 10 * (1 - t))

    return {
        "shoulder": shoulder, "head_c": head_c, "head_r": head_r,
        "knee": knee, "foot": foot, "hand": hand, "elbow": elbow,
        "dir": (dirx, diry),
    }


def _figure_shapes(d, ps, col):
    # legs (draw first, behind torso)
    capsule(d, HIP, ps["knee"], 17, col)          # thigh
    capsule(d, ps["knee"], ps["foot"], 13, col)   # shin
    d.ellipse([ps["foot"][0] - 8, ps["foot"][1] - 5,
               ps["foot"][0] + 10, ps["foot"][1] + 6], fill=col)  # foot

    # arm
    capsule(d, ps["shoulder"], ps["elbow"], 10, col)
    capsule(d, ps["elbow"], ps["hand"], 9, col)

    # torso + neck
    capsule(d, HIP, ps["shoulder"], 24, col)

    # head
    hx, hy = ps["head_c"]
    r = ps["head_r"]
    d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=col)

    # afro: a bumpy mass centred slightly behind the head
    dx, dy = ps["dir"]
    ac = (hx - dx * 4, hy - dy * 4)
    ar = 23
    d.ellipse([ac[0] - ar, ac[1] - ar, ac[0] + ar, ac[1] + ar], fill=col)
    for k in range(10):
        a = k / 10 * 2 * math.pi
        bx = ac[0] + math.cos(a) * ar
        by = ac[1] + math.sin(a) * ar
        br = 9
        d.ellipse([bx - br, by - br, bx + br, by + br], fill=col)


def draw_figure(t, f, idle, rain):
    ps = get_pose(t, f, idle)

    # soft dusk rim-light so the silhouette reads against the dark cliff
    rim = tuple(int(lerp(c, g, rain)) for c, g in
                zip((176, 150, 190), (96, 100, 116)))
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    _figure_shapes(ImageDraw.Draw(halo), ps, rim + (255,))
    halo = halo.filter(ImageFilter.GaussianBlur(2.5))

    dark = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    _figure_shapes(ImageDraw.Draw(dark), ps, FIG_COL + (255,))
    return Image.alpha_composite(halo, dark)


# --------------------------------------------------------------- rain --------
class Rain:
    def __init__(self, n=280):
        self.drops = []
        for _ in range(n):
            self.drops.append([random.uniform(0, W + 90),
                               random.uniform(-H, H),
                               random.uniform(9, 18),
                               random.uniform(14, 22)])
        self.slant = 6

    def step_and_draw(self, intensity):
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if intensity <= 0.01:
            return layer
        d = ImageDraw.Draw(layer)
        visible = int(len(self.drops) * lerp(0.25, 1.0, intensity))
        speed = lerp(0.9, 1.4, intensity)
        alpha = int(lerp(60, 150, intensity))
        for i, dr in enumerate(self.drops):
            dr[1] += dr[3] * speed
            if dr[1] > H:
                dr[1] = random.uniform(-40, 0)
                dr[0] = random.uniform(0, W + 90)
            if i >= visible:
                continue
            x, y, ln = dr[0], dr[1], dr[2]
            d.line([x, y, x - self.slant, y + ln],
                   fill=(200, 214, 235, alpha), width=1)
            # splash where rain lands on the cliff top
            if x - self.slant < X_EDGE and Y_TOP <= y + ln < Y_TOP + 6:
                sx = x - self.slant
                d.line([sx - 3, Y_TOP, sx, Y_TOP - 4], fill=(205, 218, 238, alpha))
                d.line([sx, Y_TOP - 4, sx + 3, Y_TOP], fill=(205, 218, 238, alpha))
        return layer


def main():
    rain = Rain()
    frames = []

    for f in range(FRAMES):
        p = f / (FRAMES - 1)

        t = ease(clamp01((p - 0.24) / 0.30))            # sit -> lie
        idle = 1 - ease(clamp01((p - 0.14) / 0.14))     # sway fades as he lies
        rain_i = ease(clamp01((p - 0.54) / 0.42))       # rain after he lies

        frame = sky(rain_i)
        draw_cliff(frame, rain_i)
        frame = frame.convert("RGBA")
        frame = Image.alpha_composite(frame, draw_figure(t, f, idle, rain_i))

        # sky darkens a touch overall as the storm arrives
        if rain_i > 0:
            dark = Image.new("RGBA", (W, H), (18, 20, 30, int(70 * rain_i)))
            frame = Image.alpha_composite(frame, dark)

        frame = Image.alpha_composite(frame, rain.step_and_draw(rain_i))
        frames.append(frame.convert("RGB"))

    pal = [fr.quantize(colors=128, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG)
           for fr in frames]
    out = "cliff_figure_rain.gif"
    pal[0].save(out, save_all=True, append_images=pal[1:],
                duration=int(1000 / FPS), loop=0, optimize=True, disposal=2)
    print(f"wrote {out} ({FRAMES} frames, {W}x{H})")


if __name__ == "__main__":
    main()
