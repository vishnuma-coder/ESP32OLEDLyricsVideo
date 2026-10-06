#!/usr/bin/env python3
"""Embed a short video as monochrome frames in src/video_frames.h."""

import argparse
import pathlib
import shutil
import subprocess
import sys

# Match WIDTH/HEIGHT to the OLED. Keep FPS modest to limit firmware size.
WIDTH, HEIGHT, FPS = 128, 64, 12
FRAME_BYTES = WIDTH * HEIGHT // 8
# Clips are capped to keep embedded video from making firmware too large.
MAX_SECONDS = 30
# Raise/lower this to change which source pixels become lit in non-dither mode.
THRESHOLD = 150


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=pathlib.Path, help="video to embed in firmware")
    parser.add_argument("--output", type=pathlib.Path,
                        default=pathlib.Path("src/video_frames.h"),
                        help="generated C header")
    parser.add_argument("--seconds", type=int, default=MAX_SECONDS,
                        help="clip duration, 1..30 seconds")
    parser.add_argument("--dither", action="store_true",
                        help="preserve grayscale as a monochrome texture")
    parser.add_argument("--invert", action="store_true",
                        help="make bright source areas glow instead of dark art")
    parser.add_argument("--crop", nargs=4, type=int,
                        metavar=("X", "Y", "WIDTH", "HEIGHT"),
                        help="crop a content panel before scaling to 128x64")
    args = parser.parse_args()

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        parser.error("FFmpeg was not found on PATH")
    if not args.input.is_file():
        parser.error(f"video does not exist: {args.input}")
    if not 1 <= args.seconds <= MAX_SECONDS:
        parser.error("--seconds must be between 1 and 30")
    if args.crop and (args.crop[0] < 0 or args.crop[1] < 0 or
                      args.crop[2] <= 0 or args.crop[3] <= 0):
        parser.error("--crop needs non-negative X/Y and positive width/height")

    try:
        from PIL import Image
    except ImportError:
        parser.error("Pillow is required; install with: python -m pip install Pillow")

    if args.crop:
        x, y, crop_width, crop_height = args.crop
        vf = (f"fps={FPS},crop={crop_width}:{crop_height}:{x}:{y},"
              f"scale={WIDTH}:{HEIGHT},format=gray")
    else:
        vf = (f"fps={FPS},scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
              f"crop={WIDTH}:{HEIGHT},format=gray")
    command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-i", str(args.input),
               "-t", str(args.seconds), "-an", "-vf", vf, "-f", "rawvideo",
               "-pix_fmt", "gray", "pipe:1"]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    raw_path = args.output.with_suffix(args.output.suffix + ".raw.tmp")
    header_temp = args.output.with_suffix(args.output.suffix + ".tmp")
    count = 0
    try:
        with subprocess.Popen(command, stdout=subprocess.PIPE) as process, raw_path.open("wb") as raw:
            assert process.stdout is not None
            while True:
                pixels = process.stdout.read(WIDTH * HEIGHT)
                if not pixels:
                    break
                if len(pixels) != WIDTH * HEIGHT:
                    raise RuntimeError("FFmpeg returned a partial frame")
                image = Image.frombytes("L", (WIDTH, HEIGHT), pixels)
                if args.dither:
                    mono = image.convert("1", dither=Image.Dither.FLOYDSTEINBERG)
                    if not args.invert:
                        mono = mono.point(lambda value: 0 if value else 255, mode="1")
                else:
                    mono = image.point(
                        lambda value: 255 if (value >= THRESHOLD) == args.invert else 0,
                        mode="1",
                    )
                packed = mono.tobytes()
                if len(packed) != FRAME_BYTES:
                    raise RuntimeError(f"unexpected frame size: {len(packed)}")
                raw.write(packed)
                count += 1
            result = process.wait()
        if result:
            raise RuntimeError(f"FFmpeg exited with status {result}")
        if not count:
            raise RuntimeError("no frames decoded")

        with raw_path.open("rb") as raw, header_temp.open("w", encoding="ascii", newline="\n") as out:
            out.write("#pragma once\n#include <Arduino.h>\n#include <pgmspace.h>\n\n")
            out.write(f"#define VIDEO_FRAME_COUNT {count}UL\n")
            out.write(f"#define VIDEO_FRAME_RATE {FPS}U\n")
            out.write("static const uint8_t VIDEO_FRAMES[] PROGMEM = {\n")
            for _ in range(count * FRAME_BYTES // 16):
                chunk = raw.read(16)
                out.write("  " + ", ".join(f"0x{value:02X}" for value in chunk) + ",\n")
            out.write("};\n")
        header_temp.replace(args.output)
    except Exception:
        header_temp.unlink(missing_ok=True)
        raise
    finally:
        raw_path.unlink(missing_ok=True)

    print(f"Embedded {count} frames ({count / FPS:.2f}s, "
          f"{count * FRAME_BYTES:,} video bytes) in {args.output}.")
    print("Upload once with PlatformIO: Upload. No filesystem upload is needed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
