#!/usr/bin/env python3
"""Generate an animated GIF of a campfire being put out by rain.

The animation arc:
  * It starts dry-ish with a tall, lively flame and light rain.
  * Rain steadily intensifies while the flame shrinks and flickers weaker.
  * Steam puffs appear where the rain hits the dying fire.
  * The flame goes out, leaving smoke, faintly glowing embers, and heavy rain.

No external assets required -- everything is drawn procedurally with Pillow.
"""

import math
import random

from PIL import Image, ImageDraw, ImageFilter

W, H = 480, 360
FRAMES = 90
FPS = 18
GROUND_Y = H - 70
FIRE_X = W // 2

random.seed(7)


def ease(t: float) -> float:
    """Smoothstep easing for nicer transitions."""
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def background() -> Image.Image:
    """Dark, rainy night gradient with a faint ground."""
    bg = Image.new("RGB", (W, H))
    px = bg.load()
    top = (14, 18, 32)
    bot = (32, 40, 58)
    for y in range(H):
        t = y / (H - 1)
        px_row = tuple(int(lerp(top[i], bot[i], t)) for i in range(3))
        for x in range(W):
            px[x, y] = px_row
    d = ImageDraw.Draw(bg)
    # ground
    d.rectangle([0, GROUND_Y, W, H], fill=(26, 30, 26))
    d.ellipse([FIRE_X - 150, GROUND_Y - 14, FIRE_X + 150, GROUND_Y + 26],
              fill=(34, 38, 32))
    return bg


def draw_logs(d: ImageDraw.ImageDraw):
    log_col = (74, 49, 32)
    log_edge = (52, 33, 21)
    for (x0, y0, x1, y1) in [
        (FIRE_X - 70, GROUND_Y + 6, FIRE_X + 40, GROUND_Y - 8),
        (FIRE_X - 40, GROUND_Y - 8, FIRE_X + 70, GROUND_Y + 6),
    ]:
        d.line([x0, y0, x1, y1], fill=log_edge, width=20)
        d.line([x0, y0, x1, y1], fill=log_col, width=14)
    d.ellipse([FIRE_X + 34, GROUND_Y - 14, FIRE_X + 54, GROUND_Y + 6],
              fill=(95, 64, 42))
    d.ellipse([FIRE_X - 76, GROUND_Y - 2, FIRE_X - 58, GROUND_Y + 14],
              fill=(95, 64, 42))


def flame_polygon(cx, base_y, height, half_w, phase, sway_amp):
    n = 18
    left, right = [], []
    for i in range(n + 1):
        t = i / n  # 0 at base, 1 at tip
        y = base_y - t * height
        # width: widest in lower third, converging to a point at the tip
        width = half_w * (1 - t ** 1.4) * (0.55 + 0.45 * math.sin(t * 2.4))
        width *= 1 + 0.18 * math.sin(phase * 1.7 + t * 7)
        sway = sway_amp * math.sin(phase + t * 2.6) * (t ** 1.2)
        left.append((cx - width + sway, y))
        right.append((cx + width + sway, y))
    return left + right[::-1]


def draw_fire(intensity, phase):
    """Return an RGBA layer with the layered flame + ember glow."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if intensity <= 0.02:
        return layer
    d = ImageDraw.Draw(layer)

    base_h = lerp(28, 150, intensity)
    base_w = lerp(10, 46, intensity)
    a = int(lerp(120, 255, intensity))

    layers = [
        (1.00, 1.00, (200, 60, 12, a)),       # outer deep orange
        (0.82, 0.78, (240, 120, 24, a)),      # orange
        (0.60, 0.58, (255, 190, 60, a)),      # yellow
        (0.36, 0.40, (255, 244, 200, min(255, a + 20))),  # white-hot core
    ]
    for hi, wi, col in layers:
        poly = flame_polygon(
            FIRE_X, GROUND_Y - 2,
            base_h * hi, base_w * wi,
            phase, sway_amp=lerp(2, 9, intensity) * hi,
        )
        d.polygon(poly, fill=col)

    layer = layer.filter(ImageFilter.GaussianBlur(1.4))

    # warm ember glow at the base
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gr = lerp(26, 80, intensity)
    galpha = int(lerp(40, 150, intensity))
    gd.ellipse([FIRE_X - gr, GROUND_Y - gr * 0.7, FIRE_X + gr, GROUND_Y + gr * 0.5],
               fill=(255, 140, 40, galpha))
    glow = glow.filter(ImageFilter.GaussianBlur(14))
    return Image.alpha_composite(glow, layer)


def draw_embers(intensity, phase, out_amount):
    """Faint glowing ember dots that linger after the flame dies."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rng = random.Random(99)
    for _ in range(10):
        ex = FIRE_X + rng.randint(-55, 55)
        ey = GROUND_Y + rng.randint(-6, 8)
        flicker = 0.5 + 0.5 * math.sin(phase * 2.2 + ex)
        # embers brighten as the flame fades, then slowly cool at the very end
        glow_amt = (0.35 + 0.65 * out_amount) * (1 - 0.5 * max(0, out_amount - 0.7) / 0.3)
        a = int(150 * flicker * glow_amt)
        if a <= 4:
            continue
        r = rng.randint(2, 4)
        d.ellipse([ex - r, ey - r, ex + r, ey + r], fill=(255, 110, 30, a))
    return layer.filter(ImageFilter.GaussianBlur(0.8))


class Rain:
    def __init__(self, n=260):
        self.drops = []
        for _ in range(n):
            self.drops.append([
                random.uniform(0, W + 80),
                random.uniform(-H, H),
                random.uniform(10, 20),     # length
                random.uniform(13, 20),     # speed
            ])
        self.slant = 5

    def step_and_draw(self, intensity):
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        visible = int(len(self.drops) * lerp(0.35, 1.0, intensity))
        speed_mul = lerp(0.85, 1.35, intensity)
        alpha = int(lerp(70, 160, intensity))
        for i, drop in enumerate(self.drops):
            drop[1] += drop[3] * speed_mul
            if drop[1] > H:
                drop[1] = random.uniform(-40, 0)
                drop[0] = random.uniform(0, W + 80)
            if i >= visible:
                continue
            x, y, ln = drop[0], drop[1], drop[2]
            d.line([x, y, x - self.slant, y + ln],
                   fill=(180, 205, 235, alpha), width=1)
            # tiny splash when a drop reaches the ground
            if y + ln >= GROUND_Y and y < GROUND_Y + 6:
                sx = x - self.slant
                d.line([sx - 3, GROUND_Y, sx, GROUND_Y - 4],
                       fill=(190, 215, 240, alpha), width=1)
                d.line([sx, GROUND_Y - 4, sx + 3, GROUND_Y],
                       fill=(190, 215, 240, alpha), width=1)
        return layer


class Puffs:
    """Rising smoke / steam puffs."""
    def __init__(self):
        self.items = []  # x, y, r, age, life, kind

    def spawn(self, smoke_rate, steam_rate):
        if random.random() < smoke_rate:
            self.items.append([FIRE_X + random.uniform(-12, 12), GROUND_Y - 20,
                               random.uniform(6, 12), 0.0,
                               random.uniform(28, 46), "smoke"])
        if random.random() < steam_rate:
            self.items.append([FIRE_X + random.uniform(-26, 26), GROUND_Y - 6,
                               random.uniform(4, 8), 0.0,
                               random.uniform(16, 26), "steam"])

    def step_and_draw(self):
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        alive = []
        for it in self.items:
            x, y, r, age, life, kind = it
            age += 1
            if age >= life:
                continue
            t = age / life
            y -= lerp(1.6, 2.6, t)
            x += math.sin(age * 0.25 + r) * 0.8
            r2 = r * (1 + 1.6 * t)
            if kind == "smoke":
                base_a = int(110 * (1 - t))
                col = (90, 92, 96, base_a)
            else:  # steam -- whiter, fades faster
                base_a = int(150 * (1 - t) ** 1.3)
                col = (215, 222, 230, base_a)
            if base_a > 3:
                d.ellipse([x - r2, y - r2, x + r2, y + r2], fill=col)
            it[1], it[3] = y, age
            it[0] = x
            alive.append(it)
        self.items = alive
        return layer.filter(ImageFilter.GaussianBlur(3))


def main():
    base = background()
    rain = Rain()
    puffs = Puffs()
    frames = []

    for f in range(FRAMES):
        p = f / (FRAMES - 1)
        phase = f * 0.5

        # rain ramps up over the first ~40% then stays heavy
        rain_intensity = ease(min(1.0, p / 0.45))

        # fire stays strong briefly, then is overwhelmed by the rain
        if p < 0.18:
            fire = lerp(1.0, 0.9, p / 0.18)
        elif p < 0.72:
            fire = lerp(0.9, 0.0, ease((p - 0.18) / 0.54))
        else:
            fire = 0.0
        # nervous flicker that gets more erratic as the fire weakens
        flick = 1 + (0.10 + 0.22 * (1 - fire)) * math.sin(phase * 3.1)
        fire_eff = max(0.0, min(1.0, fire * flick)) if fire > 0 else 0.0
        out_amount = 1 - fire

        # more smoke as it dies; steam peaks while fire and rain coexist
        smoke_rate = lerp(0.15, 0.7, out_amount)
        steam_rate = 0.7 * rain_intensity * (fire ** 0.5) if fire > 0.04 else 0.0
        puffs.spawn(smoke_rate, steam_rate)

        frame = base.copy()
        d = ImageDraw.Draw(frame)
        draw_logs(d)
        frame = frame.convert("RGBA")

        frame = Image.alpha_composite(frame, draw_fire(fire_eff, phase))
        frame = Image.alpha_composite(frame, draw_embers(fire_eff, phase, out_amount))
        frame = Image.alpha_composite(frame, puffs.step_and_draw())
        frame = Image.alpha_composite(frame, rain.step_and_draw(rain_intensity))

        frames.append(frame.convert("RGB"))

    # quantize for a smaller, clean GIF palette
    pal_frames = [fr.quantize(colors=128, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG)
                  for fr in frames]

    out = "fire_rain.gif"
    pal_frames[0].save(
        out,
        save_all=True,
        append_images=pal_frames[1:],
        duration=int(1000 / FPS),
        loop=0,
        optimize=True,
        disposal=2,
    )
    print(f"wrote {out} ({FRAMES} frames, {W}x{H})")


if __name__ == "__main__":
    main()
