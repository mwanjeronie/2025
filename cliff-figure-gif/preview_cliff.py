#!/usr/bin/env python3
"""Static mockups of two "actual cliff" compositions, for confirmation."""

import numpy as np
from PIL import Image, ImageDraw

W, H = 480, 360


def sky():
    stops = [(0.00, (46, 40, 92)), (0.42, (120, 92, 140)),
             (0.50, (238, 142, 98)), (0.62, (168, 116, 122)),
             (1.00, (110, 92, 112))]
    ys = np.array([s[0] for s in stops])
    cols = np.array([s[1] for s in stops], dtype=float)
    frac = np.linspace(0, 1, H)
    grad = np.stack([np.interp(frac, ys, cols[:, i]) for i in range(3)], axis=1)
    arr = np.repeat(grad[:, None, :], W, axis=1)
    return Image.fromarray(arr.astype(np.uint8), "RGB")


def simple_figure_profile(d, edge, col=(16, 15, 22)):
    """Seated profile figure at a side-view cliff edge (facing right)."""
    ex, ey = edge
    hip = (ex - 44, ey)
    shoulder = (hip[0] - 6, hip[1] - 78)
    d.line([hip, shoulder], fill=col, width=22)
    d.line([hip, (ex, ey)], fill=col, width=15)          # thigh to edge
    d.line([(ex, ey), (ex, ey + 64)], fill=col, width=12)  # dangling shin
    hc = (shoulder[0] + 2, shoulder[1] - 24)
    d.ellipse([hc[0] - 20, hc[1] - 20, hc[0] + 20, hc[1] + 20], fill=col)  # afro


def simple_figure_front(d, lip_mid, col=(16, 15, 22)):
    """Seated front-facing figure on the near lip, legs dangling down."""
    mx, my = lip_mid
    d.line([(mx, my), (mx, my - 70)], fill=col, width=24)      # torso
    d.ellipse([mx - 22, my - 118, mx + 22, my - 74], fill=col)  # afro
    d.line([(mx, my), (mx - 12, my + 60)], fill=col, width=12)  # left leg
    d.line([(mx, my), (mx + 12, my + 60)], fill=col, width=12)  # right leg


def option_a():
    """Side view: solid flat-topped cliff, sheer vertical face, open drop."""
    img = sky()
    d = ImageDraw.Draw(img, "RGBA")
    top_y, edge_x = 232, 300
    rock = (40, 36, 58)
    # cliff body: flat top on the left, vertical face on the right
    d.polygon([(0, top_y), (edge_x, top_y), (edge_x, H), (0, H)], fill=rock)
    # faint valley haze far below/right to imply a big drop
    for y in range(300, H):
        a = int(70 * (y - 300) / (H - 300))
        d.line([(edge_x, y), (W, y)], fill=(150, 120, 140, a))
    d.line([(0, top_y), (edge_x, top_y)], fill=(150, 120, 150), width=3)  # lip
    simple_figure_profile(d, (edge_x, top_y))
    img.save("preview_A_side.png")


def option_b():
    """3/4 view: flat cliff top receding inward, near lip is a horizontal line."""
    img = sky()
    d = ImageDraw.Draw(img, "RGBA")
    lip_y = 258
    # flat cliff top seen in perspective (recedes up/inward)
    top = [(60, lip_y), (420, lip_y), (352, 210), (128, 210)]
    d.polygon(top, fill=(58, 52, 78))
    # sheer front face dropping away below the near lip
    d.polygon([(60, lip_y), (420, lip_y), (438, H), (42, H)], fill=(30, 27, 44))
    d.line([(60, lip_y), (420, lip_y)], fill=(158, 128, 156), width=3)  # lip line
    simple_figure_front(d, (240, lip_y))
    img.save("preview_B_frontal.png")


if __name__ == "__main__":
    option_a()
    option_b()
    print("wrote preview_A_side.png and preview_B_frontal.png")
