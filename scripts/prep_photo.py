"""
prep_photo.py
Turn a normal headshot into a clean, high-contrast grayscale image that is
ready for ASCII conversion.

Steps:
  1. Remove the background (rembg) so only the subject remains.
  2. Boost local contrast with CLAHE so a flat face gets real highlights/shadows.
  3. Composite onto pure white so the background maps to the blank end of the
     ASCII ramp (white -> space).

Usage:
    python scripts/prep_photo.py source-photo.png
Output:
    source-prepped.png  (grayscale, same folder as input)
"""
import sys
import os
import numpy as np
import cv2
from rembg import remove
from PIL import Image


def prep(input_path: str, output_path: str) -> None:
    with open(input_path, "rb") as f:
        input_bytes = f.read()

    # 1. Remove background -> RGBA with alpha mask around the subject
    result_bytes = remove(input_bytes)
    rgba = Image.open(__import__("io").BytesIO(result_bytes)).convert("RGBA")

    # 2. Composite the cut-out subject onto pure white
    white_bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    composited = Image.alpha_composite(white_bg, rgba).convert("RGB")

    # 3. Convert to grayscale + CLAHE local contrast boost
    gray = cv2.cvtColor(np.array(composited), cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    contrasted = clahe.apply(gray)

    # 4. Re-flatten background to pure white using the alpha mask, so CLAHE
    #    doesn't drag noise back into the (already removed) background
    alpha = np.array(rgba.split()[-1])
    mask = alpha < 8
    contrasted[mask] = 255

    Image.fromarray(contrasted).save(output_path)
    print(f"wrote {output_path}")


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "source-photo.png"
    base, _ = os.path.splitext(src)
    out = f"{base}-prepped.png"
    prep(src, out)
