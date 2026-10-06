#include <Arduino.h>
#include <Wire.h>
#include <string.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#ifndef OLED_SDA
// CHANGE THIS for your board's OLED SDA pin (or set OLED_SDA in platformio.ini).
#define OLED_SDA 21
#endif
#ifndef OLED_SCL
// CHANGE THIS for your board's OLED SCL pin (or set OLED_SCL in platformio.ini).
#define OLED_SCL 22
#endif

#if __has_include("video_frames.h")
#include "video_frames.h"
#define HAS_EMBEDDED_VIDEO 1
#else
#define HAS_EMBEDDED_VIDEO 0
#endif

namespace {
constexpr int WIDTH = 128;
constexpr int HEIGHT = 64;
// CHANGE THIS if your OLED uses address 0x3D instead of the common 0x3C.
constexpr uint8_t OLED_ADDRESS = 0x3C;
#if HAS_EMBEDDED_VIDEO
constexpr uint8_t FPS = VIDEO_FRAME_RATE;
#else
constexpr uint8_t FPS = 12;
#endif
constexpr uint32_t FRAME_MS = 1000 / FPS;
constexpr size_t FRAME_BYTES = WIDTH * HEIGHT / 8;

Adafruit_SSD1306 display(WIDTH, HEIGHT, &Wire, -1);
uint32_t lastFrameAt = 0;
size_t lastVideoFrame = static_cast<size_t>(-1);

void drawDemoLyrics(uint32_t now) {
  static const char *const lines[] = {
      "STARS ABOVE", "GUIDE US HOME", "NIGHT GLOWS", "FOLLOW LIGHT"};
  const uint8_t scene = (now / 2600) % 4;
  const uint8_t twinkle = (now / 180) % 4;

  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);
  display.setTextSize(1);
  display.setCursor(38, 8);
  display.print(F("BETHLEHEM"));

  display.drawLine(64, 21, 64, 27, SSD1306_WHITE);
  display.drawLine(61, 24, 67, 24, SSD1306_WHITE);
  display.drawPixel(20 + twinkle * 9, 19, SSD1306_WHITE);
  display.drawPixel(101 - twinkle * 6, 29, SSD1306_WHITE);
  display.drawPixel(27, 43 + (twinkle & 1) * 3, SSD1306_WHITE);
  display.drawPixel(108, 48 - (twinkle & 1) * 3, SSD1306_WHITE);

  const char *line = lines[scene];
  const int16_t textWidth = strlen(line) * 12;
  display.setTextSize(2);
  display.setCursor((WIDTH - textWidth) / 2, 39);
  display.print(line);
  display.display();
}

void drawVideo(uint32_t now) {
#if HAS_EMBEDDED_VIDEO
  const size_t frameIndex = ((now / FRAME_MS) % VIDEO_FRAME_COUNT);
  if (frameIndex == lastVideoFrame) return;
  display.clearDisplay();
  display.drawBitmap(0, 0, VIDEO_FRAMES + frameIndex * FRAME_BYTES,
                     WIDTH, HEIGHT, SSD1306_WHITE);
  display.display();
  lastVideoFrame = frameIndex;
#else
  drawDemoLyrics(now);
#endif
}
}  // namespace

void setup() {
  Wire.begin(OLED_SDA, OLED_SCL);
  Wire.setClock(400000);

  if (!display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDRESS)) {
    while (true) delay(1000);
  }
  display.clearDisplay();
  display.display();
  lastFrameAt = millis() - FRAME_MS;
}

void loop() {
  const uint32_t now = millis();
  if (now - lastFrameAt < FRAME_MS) return;
  lastFrameAt = now;
  drawVideo(now);
}
