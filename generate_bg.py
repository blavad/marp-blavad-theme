#!/usr/bin/env python3
"""
Generate Marp slide background images (bg-1.png, bg-2.png, bg-3.png)
from two theme colors (primary and secondary) et light/dark colors.

Usage:
  python generate_bg.py
  python generate_bg.py --primary "#ff2453" --secondary "#20abf3"
  python generate_bg.py --primary "255,36,83" --secondary "32,171,243"
  python generate_bg.py --primary "#7c3aed" --secondary "#0ea5e9" --output assets/img
  python generate_bg.py --primary "#7c3aed" --secondary "#0ea5e9" --light "#ffffff" --dark "#070219" --output assets/img
  python generate_bg.py --primary "124,58,237" --secondary "14,165,233" --light "255,255,255" --dark "7,2,25"
"""

import argparse
import os
import numpy as np
from PIL import Image, ImageFilter


def parse_color(color: str) -> tuple[int, int, int]:
    """Accept either hex '#rrggbb' or RGB '155,255,0' format."""
    color = color.strip()
    if "," in color:
        parts = [int(x.strip()) for x in color.split(",")]
        return tuple(parts)
    return hex_to_rgb(color)


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def radial_blob(size: tuple, center: tuple, radius: int, color: tuple, opacity: float = 0.6) -> Image.Image:
    """
    Draw a soft radial gradient blob on a transparent canvas.
    Falloff: smooth cosine from center (full opacity) to radius (transparent).
    """
    w, h = size
    cx, cy = center
    r, g, b = color

    y_grid, x_grid = np.ogrid[:h, :w]
    dist = np.sqrt((x_grid - cx) ** 2 + (y_grid - cy) ** 2)

    # Cosine falloff for a very smooth edge
    t = np.clip(dist / radius, 0.0, 1.0)
    alpha = ((np.cos(t * np.pi) + 1) / 2) * opacity

    canvas = np.zeros((h, w, 4), dtype=np.uint8)
    canvas[:, :, 0] = r
    canvas[:, :, 1] = g
    canvas[:, :, 2] = b
    canvas[:, :, 3] = (alpha * 255).astype(np.uint8)

    img = Image.fromarray(canvas, "RGBA")
    # Extra Gaussian blur for the soft halo look
    img = img.filter(ImageFilter.GaussianBlur(radius=radius // 6))
    return img


def composite(blobs: list, size: tuple, bg_color: tuple = (255, 255, 255)) -> Image.Image:
    """Alpha-composite a list of RGBA blobs onto a solid background."""
    base = Image.new("RGBA", size, (*bg_color, 255))
    for blob in blobs:
        base = Image.alpha_composite(base, blob)
    return base.convert("RGB")


def generate(
    primary: str,
    secondary: str,
    light: str = "#ffffff",
    dark: str = "#070219",
    size: tuple = (960, 540),
    output_dir: str = ".",
):
    w, h = size
    p = parse_color(primary)
    s = parse_color(secondary)
    light_rgb = parse_color(light)
    dark_rgb = parse_color(dark)

    # Each variant: list of (center_fx, center_fy, radius_fw, color, opacity)
    # Positions expressed as fractions of width/height
    variants = {
        "bg-1": [
            # Blue blob left-center, pink blob right-center
            (0.7, 0.70, 0.2, s, 0.55),
            (0.95, 0.60, 0.23, p, 0.55),
        ],
        "bg-2": [
            # Pink bottom-left corner, blue bottom-right corner
            (0.03, 0.97, 0.15, p, 0.55),
            (0.97, 0.97, 0.15, s, 0.55),
        ],
        "bg-3": [
            # Blue top-left corner, pink bottom-right area
            (0.03, 0.05, 0.17, s, 0.55),
            (0.9, 0.80, 0.18, p, 0.55),
        ],
        "bg-cover": [
            # Large blue blob centered below the slide, large pink blob centered above the slide
            (0.5, 1.1, 0.56, p, 0.75),
            (0.5, 1.2, 0.4, s, 0.75),
        ],
    }

    os.makedirs(output_dir, exist_ok=True)

    for name, specs in variants.items():
        blobs = []
        for fx, fy, fr, color, opacity in specs:
            cx = int(fx * w)
            cy = int(fy * h)
            radius = int(fr * w)
            blobs.append(radial_blob(size, (cx, cy), radius, color, opacity))

        bg = dark_rgb if name == "bg-cover" else light_rgb
        img = composite(blobs, size, bg)
        out_path = os.path.join(output_dir, f"{name}.png")
        img.save(out_path)
        print(f"  {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate soft-blob background PNGs for Marp themes.")
    parser.add_argument("--primary", default="#ff2453", help="Primary color   (default: #ff2453)")
    parser.add_argument("--secondary", default="#20abf3", help="Secondary color (default: #20abf3)")
    parser.add_argument("--light", default="#ffffff", help="Light color (default: #ffffff)")
    parser.add_argument("--dark", default="#070219", help="Dark color (default: #070219)")
    parser.add_argument("--width", type=int, default=960, help="Image width  (default: 960)")
    parser.add_argument("--height", type=int, default=540, help="Image height (default: 540)")
    parser.add_argument("--output", default="assets/img", help="Output directory (default: assets/img)")
    args = parser.parse_args()

    print(f"Primary:   {args.primary}")
    print(f"Secondary: {args.secondary}")
    print(f"Light:     {args.light}")
    print(f"Dark:      {args.dark}")
    print(f"Size:      {args.width}x{args.height}")
    print(f"Output:")
    generate(args.primary, args.secondary, args.light, args.dark, (args.width, args.height), args.output)
    print("Done.")


if __name__ == "__main__":
    main()
