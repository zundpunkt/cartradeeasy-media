#!/usr/bin/env python3
"""Adds the right-edge shading to a 1080x1920 CarTradeEasy video and its cover.

Instagram and TikTok draw their like, comment, share and save buttons as white
outlines down the right edge of a video. On our cream backgrounds they vanish.
This lays a soft brown shadow (#55282F, the brand's --brand-d) under that rail.

Usage:  python3 tools/add-right-scrim.py IN.mp4 OUT.mp4 [IN-cover.jpg OUT-cover.jpg]
Needs:  ffmpeg, Pillow, numpy.  Audio is copied untouched.

Shape (set with Vin on Nov 12, 2026: "a slight dark gradient"):
  - starts at x=840 and is strongest at the right edge (60% opacity)
  - fades in between 25% and 45% of the height, holds to 90%, fades out by the bottom
"""
import subprocess, sys, tempfile, os
import numpy as np
from PIL import Image

W, H = 1080, 1920
COLOUR = (0x55, 0x28, 0x2F)
PEAK = 0.60

def smooth(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)

def scrim():
    x = np.arange(W)[None, :].repeat(H, 0).astype(float)
    y = np.arange(H)[:, None].repeat(W, 1).astype(float)
    ax = smooth((x - 840) / (W - 840))
    ay = np.where(y < 0.45 * H, smooth((y - 0.25 * H) / (0.20 * H)),
         np.where(y > 0.90 * H, 1 - smooth((y - 0.90 * H) / (0.10 * H)), 1.0))
    img = np.zeros((H, W, 4), np.uint8)
    img[..., 0], img[..., 1], img[..., 2] = COLOUR
    img[..., 3] = (PEAK * ax * ay * 255).round().astype(np.uint8)
    return Image.fromarray(img, "RGBA")

def main(a):
    if len(a) not in (2, 4):
        sys.exit(__doc__)
    s = scrim()
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "scrim.png"); s.save(p)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a[0], "-i", p, "-filter_complex",
                        "[0:v][1:v]overlay=0:0:format=auto,format=yuv420p", "-c:v", "libx264", "-preset", "slow",
                        "-crf", "17", "-profile:v", "high", "-movflags", "+faststart", "-c:a", "copy", a[1]], check=True)
    if len(a) == 4:
        c = Image.open(a[2]).convert("RGBA")
        if c.size != (W, H): sys.exit(f"cover is {c.size}, expected {(W, H)}")
        c.alpha_composite(s); c.convert("RGB").save(a[3], quality=92)

if __name__ == "__main__":
    main(sys.argv[1:])
