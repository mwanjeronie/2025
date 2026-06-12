# 🔥🌧️ Fire Burning Out in the Rain

An animated GIF of a campfire being slowly extinguished by rain.

![Fire burning out in the rain](fire_rain.gif)

## The animation

1. A tall, flickering campfire on a dark, rainy night with light rain.
2. The rain steadily intensifies while the flame shrinks and sputters.
3. Steam puffs rise where the rain hits the dying fire.
4. The flame goes out — leaving smoldering logs, a wisp of smoke, faintly
   glowing embers, and heavy rain.

## Regenerating it

The GIF is drawn entirely procedurally with [Pillow](https://python-pillow.org/) —
no external image assets are needed.

```bash
pip install Pillow
python3 make_fire_rain.py   # writes fire_rain.gif (480x360, 90 frames)
```

Tweak the constants at the top of `make_fire_rain.py` (`W`, `H`, `FRAMES`,
`FPS`) to change the size or speed.
