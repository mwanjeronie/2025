#!/usr/bin/env python3
"""Animated GIF: a man on a distant cliff peak lies back, then it begins to rain.

Scene (side profile, dusk):
  * A tall, slim man with an afro sits on the edge of a far-off, triangular
    cliff peak, legs hanging over the drop, leaning back on his hands and
    gently swaying.
  * He slowly leans back and lies down on his back on the summit.
  * Once he's settled, the sky darkens and rain begins, steadily intensifying.

Everything (sky, distant ranges, hazy peak, figure, rain) is drawn
procedurally with Pillow + numpy -- no external assets.
"""

import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 480, 360
FRAMES = 100
FPS = 20

# --- triangular peak geometry -------------------------------------------------
RIDGE_Y = 196          # height of the small summit
SL = (168, RIDGE_Y)    # summit left
EDGE = (300, RIDGE_Y)  # summit right = the cliff edge (drop-off)
BL = (44, 340)         # base left
BR = (452, 340)        # base right
NOTCH = (296, 236)     # slight steep lip just below the edge

HIP = (258, RIDGE_Y - 2)   # hip / pivot point on the summit
FIG_COL = (16, 15, 22)     # silhouette colour

random.seed(11)


def ease(t):
    return t * t * (3 - 2 * t)


def clamp01(t):
    return max(0.0, min(1.0, t))


def lerp(a, b, t):
    return a + (b - a) * t


def lerp2(p, q, t):
    return (lerp(p[0], q[0], t), lerp(p[1], q[1], t))


def blend(c1, c2, t):
    return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))


def rot(vx, vy, ang):
    ca, sa = math.cos(ang), math.sin(ang)
    return (vx * ca - vy * sa, vx * sa + vy * ca)


# ---------------------------------------------------------------- sky --------
def sky(rain):
    stops = [
        (0.00, (46, 40, 92),   (32, 34, 44)),
        (0.42, (120, 92, 140), (60, 64, 76)),
        (0.50, (238, 142, 98), (88, 92, 104)),
        (0.62, (168, 116, 122),(70, 74, 84)),
        (1.00, (110, 92, 112), (52, 54, 62)),
    ]
    ys = np.array([s[0] for s in stops])
    clear = np.array([s[1] for s in stops], dtype=float)
    rainy = np.array([s[2] for s in stops], dtype=float)
    cols = clear + (rainy - clear) * rain
    frac = np.linspace(0, 1, H)
    grad = np.stack([np.interp(frac, ys, cols[:, i]) for i in range(3)], axis=1)
    arr = np.repeat(grad[:, None, :], W, axis=1)
    return Image.fromarray(arr.astype(np.uint8), "RGB")


def sky_color_at(sky_img, y):
    """Sky colour at a given row (for haze tinting)."""
    return sky_img.getpixel((W // 2, int(max(0, min(H - 1, y)))))


def draw_distant_ranges(img, sky_img, rain):
    """Two faint mountain ranges near the horizon for aerial depth."""
    haze = sky_color_at(sky_img, 210)
    for (pts, mix, blur) in [
        ([(0, 214), (120, 176), (250, 208), (360, 168), (480, 206),
          (480, 260), (0, 260)], 0.62, 5),
        ([(0, 224), (90, 198), (210, 222), (330, 196), (440, 224),
          (480, 220), (480, 270), (0, 270)], 0.78, 7),
    ]:
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        col = blend((60, 54, 82), haze, mix)
        ImageDraw.Draw(layer).polygon(pts, fill=col + (255,))
        layer = layer.filter(ImageFilter.GaussianBlur(blur))
        img.paste(Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB"),
                  (0, 0))


def draw_peak(img, sky_img, rain):
    """The main triangular cliff peak, hazed toward the sky near its base."""
    base_rock = blend((44, 40, 64), (18, 20, 30), rain)
    haze = sky_color_at(sky_img, 300)
    rock = blend(base_rock, haze, 0.28)

    peak = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(peak)
    outline = [SL, EDGE, NOTCH, BR, BL]
    pd.polygon(outline, fill=rock + (255,))

    # lit rim along the sunlit right ridge + summit
    rim = blend((150, 120, 150), (86, 90, 104), rain)
    pd.line([SL, EDGE, NOTCH], fill=rim + (255,), width=3)

    # a few darker rock striations for a bit of texture
    strat = blend(base_rock, (0, 0, 0), 0.25)
    for (x0, y0, x1, y1) in [(150, 250, 250, 300), (300, 260, 400, 320),
                             (90, 300, 200, 336)]:
        pd.line([x0, y0, x1, y1], fill=strat + (120,), width=2)

    # aerial haze: fade the base into the atmosphere
    hz = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hz)
    for y in range(RIDGE_Y + 40, 341):
        a = int(150 * clamp01((y - (RIDGE_Y + 40)) / (341 - (RIDGE_Y + 40))))
        hd.line([(0, y), (W, y)], fill=sky_color_at(sky_img, y) + (a,))
    peak = Image.alpha_composite(peak, hz)

    img.paste(Image.alpha_composite(img.convert("RGBA"), peak).convert("RGB"),
              (0, 0))


# ------------------------------------------------------------- figure --------
def capsule(d, p1, p2, width, col):
    d.line([p1, p2], fill=col, width=int(width))
    r = width / 2
    for (x, y) in (p1, p2):
        d.ellipse([x - r, y - r, x + r, y + r], fill=col)


def taper(d, p1, p2, w1, w2, col):
    """A capsule that tapers from width w1 at p1 to w2 at p2."""
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    ln = math.hypot(dx, dy) or 1
    nx, ny = -dy / ln, dx / ln
    poly = [(p1[0] + nx * w1 / 2, p1[1] + ny * w1 / 2),
            (p2[0] + nx * w2 / 2, p2[1] + ny * w2 / 2),
            (p2[0] - nx * w2 / 2, p2[1] - ny * w2 / 2),
            (p1[0] - nx * w1 / 2, p1[1] - ny * w1 / 2)]
    d.polygon(poly, fill=col)
    for (x, y), w in ((p1, w1), (p2, w2)):
        d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=col)


def get_pose(t, f, idle):
    breath = math.sin(f * 0.26) * idle * 1.1

    # torso: leans back a touch when sitting, rotates flat when lying, with a
    # gentle spine curve
    torso_ang = math.radians(lerp(12, 90, t))
    ux, uy = -math.sin(torso_ang), -math.cos(torso_ang)
    torso_len = 82 + breath
    # slight S-curve: mid-torso bows a little toward the front while sitting
    mid = (HIP[0] + ux * torso_len * 0.5, HIP[1] + uy * torso_len * 0.5)
    bow = (1 - t) * 6
    mid = (mid[0] + uy * bow, mid[1] - ux * bow)
    shoulder = (HIP[0] + ux * torso_len, HIP[1] + uy * torso_len)

    # head + facing: looks out over the valley (right) when up, up when lying
    neck_len, head_r = 11, 13
    neck_top = (shoulder[0] + ux * neck_len, shoulder[1] + uy * neck_len)
    head_c = (neck_top[0] + ux * head_r, neck_top[1] + uy * head_r)
    face_ang = math.radians(lerp(6, -88, t))
    face_dir = (math.cos(face_ang), math.sin(face_ang))

    # legs: thigh along the summit to the edge, shin hanging with idle sway
    knee = EDGE
    sway = math.radians(8 * math.sin(f * 0.2) * idle)
    shin_len = 62
    foot = (knee[0] + math.sin(sway) * shin_len,
            knee[1] + math.cos(sway) * shin_len)

    # near arm: props back on the summit when sitting, rests by the side lying
    hand_sit = (HIP[0] - 40, RIDGE_Y + 1)
    hand_lie = (shoulder[0] + 18, RIDGE_Y + 1)
    hand = lerp2(hand_sit, hand_lie, t)
    ex = (shoulder[0] + hand[0]) / 2
    ey = (shoulder[1] + hand[1]) / 2 + lerp(4, 12, 1 - t)
    return {
        "hip": HIP, "mid": mid, "shoulder": shoulder, "neck_top": neck_top,
        "head_c": head_c, "head_r": head_r, "u": (ux, uy),
        "face": face_dir, "knee": knee, "foot": foot,
        "hand": hand, "elbow": (ex, ey),
    }


def _figure_shapes(d, ps, col):
    ux, uy = ps["u"]
    fx, fy = ps["face"]
    hc = ps["head_c"]
    hr = ps["head_r"]

    # leg (behind torso)
    taper(d, ps["hip"], ps["knee"], 15, 12, col)     # thigh
    taper(d, ps["knee"], ps["foot"], 12, 9, col)     # shin
    # foot points in the facing direction
    ft = ps["foot"]
    d.polygon([(ft[0] - 4, ft[1] - 4), (ft[0] + 4, ft[1] - 4),
               (ft[0] + fx * 11 + 4, ft[1] + 5), (ft[0] - 4, ft[1] + 5)], fill=col)

    # arm
    taper(d, ps["shoulder"], ps["elbow"], 9, 8, col)
    taper(d, ps["elbow"], ps["hand"], 8, 6, col)
    hx, hy = ps["hand"]
    d.ellipse([hx - 4, hy - 4, hx + 4, hy + 4], fill=col)

    # torso: tapered waist -> chest, via a slightly bowed midpoint
    taper(d, ps["hip"], ps["mid"], 15, 19, col)
    taper(d, ps["mid"], ps["shoulder"], 19, 16, col)
    # neck
    taper(d, ps["shoulder"], ps["neck_top"], 11, 8, col)

    # head with a defined profile (forehead / nose / chin along facing dir)
    d.ellipse([hc[0] - hr, hc[1] - hr, hc[0] + hr, hc[1] + hr], fill=col)
    # nose bump
    nose = (hc[0] + fx * (hr + 2), hc[1] + fy * (hr + 2))
    perp = (-fy, fx)
    d.polygon([(hc[0] + fx * hr * 0.6 + perp[0] * 4, hc[1] + fy * hr * 0.6 + perp[1] * 4),
               nose,
               (hc[0] + fx * hr * 0.6 - perp[0] * 4, hc[1] + fy * hr * 0.6 - perp[1] * 4)],
              fill=col)
    # chin / jaw
    chin = (hc[0] + fx * hr * 0.5 - perp[0] * hr * 0.7,
            hc[1] + fy * hr * 0.5 - perp[1] * hr * 0.7)
    d.ellipse([chin[0] - 5, chin[1] - 5, chin[0] + 5, chin[1] + 5], fill=col)

    # afro: full rounded mass over the crown and back of the head
    ac = (hc[0] - fx * 5, hc[1] - fy * 5)
    ar = int(hr * 1.55)
    d.ellipse([ac[0] - ar, ac[1] - ar, ac[0] + ar, ac[1] + ar], fill=col)
    for k in range(11):
        a = k / 11 * 2 * math.pi
        bx, by = ac[0] + math.cos(a) * ar * 0.95, ac[1] + math.sin(a) * ar * 0.95
        br = 8
        d.ellipse([bx - br, by - br, bx + br, by + br], fill=col)
    # small hairline tuft toward the face/forehead
    hl = (hc[0] + fx * hr * 0.5 + perp[0] * hr * 0.6,
          hc[1] + fy * hr * 0.5 + perp[1] * hr * 0.6)
    d.ellipse([hl[0] - 6, hl[1] - 6, hl[0] + 6, hl[1] + 6], fill=col)


def draw_figure(t, f, idle, rain):
    ps = get_pose(t, f, idle)
    rim = blend((182, 154, 196), (98, 102, 118), rain)
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    _figure_shapes(ImageDraw.Draw(halo), ps, rim + (255,))
    halo = halo.filter(ImageFilter.GaussianBlur(2.2))
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
        alpha = int(lerp(55, 145, intensity))
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
            if SL[0] < x - self.slant < EDGE[0] and RIDGE_Y <= y + ln < RIDGE_Y + 6:
                sx = x - self.slant
                d.line([sx - 3, RIDGE_Y, sx, RIDGE_Y - 4], fill=(205, 218, 238, alpha))
                d.line([sx, RIDGE_Y - 4, sx + 3, RIDGE_Y], fill=(205, 218, 238, alpha))
        return layer


def main():
    rain = Rain()
    frames = []
    for f in range(FRAMES):
        p = f / (FRAMES - 1)
        t = ease(clamp01((p - 0.24) / 0.30))
        idle = 1 - ease(clamp01((p - 0.14) / 0.14))
        rain_i = ease(clamp01((p - 0.54) / 0.42))

        frame = sky(rain_i)
        sky_img = frame.copy()
        draw_distant_ranges(frame, sky_img, rain_i)
        draw_peak(frame, sky_img, rain_i)
        frame = frame.convert("RGBA")
        frame = Image.alpha_composite(frame, draw_figure(t, f, idle, rain_i))
        if rain_i > 0:
            frame = Image.alpha_composite(
                frame, Image.new("RGBA", (W, H), (18, 20, 30, int(70 * rain_i))))
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
