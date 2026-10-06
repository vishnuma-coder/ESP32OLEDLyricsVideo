# ESP32 OLED Lyrics Video

A tiny, single-purpose ESP32 sketch: connect a 128x64 SSD1306 I2C OLED, upload
the firmware once, and the screen plays the video frames embedded in the
firmware. There are no sensors, buttons, audio, Wi-Fi, filesystem image, or
separate video upload step.

## Hardware

- Classic ESP32 DevKit (default PlatformIO target)
- 128x64 I2C OLED with SSD1306 controller, normally address `0x3C`
- Four wires and USB

| OLED | Classic ESP32 |
|---|---|
| VCC | 3V3 |
| GND | GND |
| SDA | GPIO 21 |
| SCL | GPIO 22 |

The default project target is a classic ESP32 DevKit. An ESP32-S3 DevKitC-1
target is included too; it uses GPIO 8/9 for I2C. Check your exact board's pin
labels and select the matching PlatformIO environment (`esp32dev` or
`esp32s3`). For another board, update its board ID and I2C pins. Confirm the
OLED controller is SSD1306; SH1106 screens require a different driver.

## Upload

1. Install VS Code and the PlatformIO IDE extension.
2. Open this folder and connect the ESP32 by USB.
3. Select the right environment (`esp32dev` or `esp32s3`) and click
   **PlatformIO: Upload**.

Without a generated video header, the sketch shows a small original lyric-style
demo. No other setup is needed.

## Replace the video

Install FFmpeg and Pillow on your computer. From this folder, run:

```powershell
python -m pip install Pillow
python tools\convert_video.py "C:\path\to\your-video.mp4"
```

The converter creates `src/video_frames.h`. Click **PlatformIO: Upload** again;
the frames are compiled into the firmware, so it is still just one upload.
The converter makes 128x64, 1-bit frames at 12 fps and accepts clips up to 30
seconds. It defaults to crisp black line art glowing on the OLED's dark
background. Use `--invert` to light up bright source areas or `--dither` to
preserve grayscale as a grainier pixel texture.

Portrait clips are center-cropped to fill the screen. If a video has bars around
its content, crop to the content panel, for example:

```powershell
python tools\convert_video.py "C:\path\to\clip.mp4" --crop 0 350 720 740
```

The generated `video_frames.h` is excluded from Git by design. The repository
does not redistribute downloaded songs, lyrics, or music videos; builders can
convert media they own or have permission to use. A public copy of your
Bethlehem clip should only be included if you have redistribution rights.

## Fixes

- Blank display: check 3.3 V, GND, SDA/SCL and confirm SSD1306. If the address is
  `0x3D`, update `OLED_ADDRESS` in `src/main.cpp`.
- Compile says the app is too large: shorten the clip with `--seconds 15`.
- Text is hard to read: choose a source with large lettering, crop away borders,
  and leave dithering off.
