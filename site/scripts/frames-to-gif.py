"""Join screenshots/lab-frames/*.png into screenshots/lab-preparations.gif (review only; git-ignored).

Usage (from site/): python scripts/frames-to-gif.py [--width 960] [--ms 100]
"""
import argparse
from pathlib import Path

from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("--width", type=int, default=960)
ap.add_argument("--ms", type=int, default=100, help="duration per frame")
a = ap.parse_args()

frames = sorted(Path("screenshots/lab-frames").glob("*.png"))
if not frames:
    raise SystemExit("no frames: run `npx tsx scripts/lab-recording.ts` first")
imgs = []
for f in frames:
    im = Image.open(f).convert("RGB")
    h = round(im.height * a.width / im.width)
    imgs.append(im.resize((a.width, h), Image.LANCZOS).quantize(colors=128, method=Image.Quantize.MEDIANCUT))
out = Path("screenshots/lab-preparations.gif")
imgs[0].save(out, save_all=True, append_images=imgs[1:], duration=a.ms, loop=0, optimize=True)
print(out, len(imgs), "frames", round(out.stat().st_size / 1e6, 1), "MB")
