#!/usr/bin/env python3
"""make.fun entry: Sum up 21 November's world news in one image.

A program that draws a one-page newspaper front page for Saturday
21 November 2026 and writes it to /output/entry.png.

Standard library only: the picture is rasterised by hand into an RGB
buffer (rectangles, lines, circles, polygons and a 5x7 bitmap font
drawn below) and encoded as PNG with zlib. No network, no clock, no
randomness, so two runs write the same bytes.

Outside the grader's container, MAKEFUN_OUTPUT_DIR stands in for
/output:
    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import binascii
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- font
# A 5x7 bitmap font, one glyph per line: seven rows of five pixels,
# '#' is ink and '.' is empty. Row 0 is the top. Lowercase letters sit
# on the x-height (rows 2-6) with ascenders and descenders as drawn.
FONT = {
    ' ': (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    '!': ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    '"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
    '#': (".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."),
    '$': ("..#..", ".####.", "#.#.#.", ".###..", "..#.#.", ".####.", "..#.."),
    '%': ("##..#", "##.#..", "....#.", "...#..", "..#...", ".#.##.", "#..##"),
    '&': (".##..", "#..#.", "#..#.", ".#.#.", "#.#.#.", "#..#.", ".##.#"),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '(': ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ')': ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    '*': (".....", ".#.#.", "..#..", "#####", "..#..", ".#.#.", "....."),
    '+': (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    ',': (".....", ".....", ".....", ".....", "..#..", "..#..", ".#..."),
    '-': (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    '.': (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    '/': ("....#", "...#.", "...#.", "..#..", "..#..", ".#...", "#...."),
    '0': (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    '1': ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    '2': (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    '3': (".###.", "#...#", "....#", "..##.", "....#", "#...#", ".###."),
    '4': ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    '5': ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    '6': ("..##.", ".#...", "#....", "#.##.", "#...#", "#...#", ".###."),
    '7': ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    '8': (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    '9': (".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."),
    ':': (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ';': (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    '<': ("...#.", "..#..", ".#...", "#....", ".#...", "..#..", "...#."),
    '=': (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    '>': (".#...", "..#..", "...#.", "....#", "...#.", "..#..", ".#..."),
    '?': (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    '@': (".###.", "#...#", "#.###", "#.#.#", "#.##.", "#....", ".###."),
    'A': (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'B': ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    'C': (".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."),
    'D': ("###..", "#..#.", "#...#", "#...#", "#...#", "#..#.", "###.."),
    'E': ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    'F': ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    'G': (".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."),
    'H': ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'I': (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    'J': ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    'K': ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    'L': ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    'M': ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    'N': ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    'O': (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'P': ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    'Q': (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    'R': ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    'S': (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    'T': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    'U': ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'V': ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    'W': ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    'X': ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    'Y': ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    'Z': ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    '[': (".###.", ".#...", ".#...", ".#...", ".#...", ".#...", ".###."),
    '\\': ("#....", "#....", ".#...", ".#...", "..#..", "..#..", "...#."),
    ']': (".###.", "...#.", "...#.", "...#.", "...#.", "...#.", ".###."),
    '^': ("..#..", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    '_': (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
    '`': (".#...", "..#..", ".....", ".....", ".....", ".....", "....."),
    'a': (".....", ".....", ".####", "....#", ".####", "#...#", ".####"),
    'b': ("#....", "#....", "####.", "#...#", "#...#", "#...#", "####."),
    'c': (".....", ".....", ".###.", "#...#", "#....", "#...#", ".###."),
    'd': ("....#", "....#", ".####", "#...#", "#...#", "#...#", ".####"),
    'e': (".....", ".....", ".###.", "#...#", "#####", "#....", ".###."),
    'f': ("..##.", ".#..#", ".#...", "####.", ".#...", ".#...", ".#..."),
    'g': (".....", ".####", "#...#", "#...#", ".####", "....#", ".###."),
    'h': ("#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"),
    'i': ("..#..", ".....", ".##..", "..#..", "..#..", "..#..", ".###."),
    'j': ("...#.", ".....", "..##.", "...#.", "...#.", "#..#.", ".##.."),
    'k': ("#....", "#....", "#..#.", "#.#..", "##...", "#.#..", "#..#."),
    'l': (".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    'm': (".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"),
    'n': (".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"),
    'o': (".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."),
    'p': (".....", ".....", "####.", "#...#", "#...#", "####.", "#...."),
    'q': (".....", ".....", ".####", "#...#", "#...#", ".####", "....#"),
    'r': (".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."),
    's': (".....", ".....", ".####", "#....", ".###.", "....#", "####."),
    't': (".#...", ".#...", "####.", ".#...", ".#...", ".#...", "..##."),
    'u': (".....", ".....", "#...#", "#...#", "#...#", "#..##", ".##.#"),
    'v': (".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    'w': (".....", ".....", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."),
    'x': (".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"),
    'y': (".....", ".....", "#...#", "#...#", ".####", "....#", ".###."),
    'z': (".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"),
    '{': ("..##.", ".#...", ".#...", "###..", ".#...", ".#...", "..##."),
    '|': ("..#..", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    '}': (".##..", "...#.", "...#.", "..###", "...#.", "...#.", ".##.."),
    '~': (".....", ".....", ".##.#", "#.#.#", ".....", ".....", "....."),
}

# Punctuation the news text uses, mapped onto plain ASCII glyphs.
_NORMALIZE = {
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
    "\u2013": "-", "\u2014": "-", "\u2022": "*", "\u2026": "...",
    "\u00b7": "-", "\u00e9": "e", "\u00ed": "i", "\u00e1": "a",
    "\u00f3": "o", "\u00fa": "u", "\u00f1": "n",
}


def normalize(text):
    out = []
    for ch in text:
        if ch in FONT:
            out.append(ch)
        elif ch in _NORMALIZE:
            out.append(_NORMALIZE[ch])
        else:
            out.append("?")
    return "".join(out)


def text_width(text, scale):
    return len(text) * (5 * scale + scale) - scale


# ---------------------------------------------------------------- canvas
class Canvas:
    """An RGB pixel buffer with small drawing primitives."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(bytes(bg) * (w * h))

    def _off(self, x, y):
        return (y * self.w + x) * 3

    def px(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            o = self._off(x, y)
            self.buf[o:o + 3] = bytes(color)

    def fill(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            o = self._off(x0, yy)
            self.buf[o:o + len(row)] = row

    def hline(self, x, y, w, color, thick=1):
        self.fill(x, y, w, thick, color)

    def vline(self, x, y, h, color, thick=1):
        self.fill(x, y, thick, h, color)

    def rect(self, x, y, w, h, color, thick=1):
        self.fill(x, y, w, thick, color)
        self.fill(x, y + h - thick, w, thick, color)
        self.fill(x, y, thick, h, color)
        self.fill(x + w - thick, y, thick, h, color)

    def line(self, x0, y0, x1, y1, color, thick=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        half = thick // 2
        while True:
            self.fill(x0 - half, y0 - half, thick, thick, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color, filled=True):
        if filled:
            for yy in range(cy - r, cy + r + 1):
                dx = int((r * r - (yy - cy) ** 2) ** 0.5) if abs(yy - cy) <= r else 0
                self.fill(cx - dx, yy, 2 * dx + 1, 1, color)
        else:
            for a in range(360):
                import math
                t = a * math.pi / 180.0
                self.px(int(cx + r * math.cos(t)), int(cy + r * math.sin(t)), color)

    def poly(self, points, color):
        """Scanline fill of a simple polygon."""
        if len(points) < 3:
            return
        ys = [p[1] for p in points]
        for yy in range(min(ys), max(ys) + 1):
            xs = []
            n = len(points)
            for i in range(n):
                x0, y0 = points[i]
                x1, y1 = points[(i + 1) % n]
                if (y0 <= yy < y1) or (y1 <= yy < y0):
                    t = (yy - y0) / (y1 - y0)
                    xs.append(x0 + t * (x1 - x0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.fill(int(xs[i]), yy, max(1, int(xs[i + 1]) - int(xs[i])), 1, color)

    def glyph(self, x, y, ch, scale, color):
        rows = FONT.get(ch)
        if rows is None:
            return
        for ry, row in enumerate(rows):
            for rx, bit in enumerate(row):
                if bit == '#':
                    self.fill(x + rx * scale, y + ry * scale, scale, scale, color)

    def text(self, x, y, s, scale, color):
        s = normalize(s)
        cx = x
        for ch in s:
            self.glyph(cx, y, ch, scale, color)
            cx += 6 * scale
        return cx - x

    def text_center(self, cx, y, s, scale, color):
        s = normalize(s)
        self.text(cx - text_width(s, scale) // 2, y, s, scale, color)

    def wrap(self, s, max_w, scale):
        """Greedy word wrap; returns a list of lines."""
        s = normalize(s)
        words = s.split(" ")
        lines = []
        cur = ""
        for wd in words:
            trial = wd if not cur else cur + " " + wd
            if text_width(trial, scale) <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = wd
        if cur:
            lines.append(cur)
        return lines

    def para(self, x, y, w, s, scale, color, leading=None):
        """Draw wrapped text; returns the y just below the last line."""
        if leading is None:
            leading = 7 * scale + max(2, scale)
        cy = y
        for line in self.wrap(s, w, scale):
            self.text(x, cy, line, scale, color)
            cy += leading
        return cy


# ---------------------------------------------------------------- png
def _chunk(kind, data):
    return (struct.pack(">I", len(data)) + kind + data +
            struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF))


def write_png(path, canvas):
    w, h = canvas.w, canvas.h
    raw = bytearray()
    stride = w * 3
    for yy in range(h):
        raw.append(0)
        raw += canvas.buf[yy * stride:(yy + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) +
           _chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + _chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# ---------------------------------------------------------------- palette
PAPER = (247, 243, 234)
CARD = (255, 253, 248)
INK = (22, 22, 26)
NAVY = (16, 30, 58)
NAVY2 = (28, 48, 88)
RED = (176, 32, 32)
TEAL = (0, 104, 102)
AMBER = (168, 108, 0)
BLUE = (28, 84, 160)
BROWN = (122, 72, 32)
GRAY = (110, 108, 100)
LINE = (205, 198, 180)
SEA = (64, 116, 168)
SAND = (214, 196, 150)
GREEN = (46, 125, 50)
GOLD = (212, 160, 32)


def starburst(c, cx, cy, r, color, spikes=10):
    import math
    pts = []
    for i in range(spikes * 2):
        ang = math.pi * i / spikes - math.pi / 2
        rad = r if i % 2 == 0 else r * 0.42
        pts.append((int(cx + rad * math.cos(ang)), int(cy + rad * math.sin(ang))))
    c.poly(pts, color)


def arc(c, x0, y0, x1, y1, lift, color, thick=2, steps=24):
    """A curved missile arc from (x0,y0) to (x1,y1), peaking by lift."""
    px, py = x0, y0
    for i in range(1, steps + 1):
        t = i / steps
        x = int(x0 + (x1 - x0) * t)
        y = int(y0 + (y1 - y0) * t - 4 * lift * t * (1 - t))
        c.line(px, py, x, y, color, thick)
        px, py = x, y


def icon_gulf(c, x, y, w, h):
    c.fill(x, y, w, h, SEA)
    c.poly([(x, y + h), (x + int(w * 0.42), y + h), (x + int(w * 0.55), y + int(h * 0.45)),
            (x + int(w * 0.38), y + int(h * 0.18)), (x, y + int(h * 0.30))], SAND)
    c.poly([(x + w, y + h), (x + int(w * 0.72), y + h), (x + int(w * 0.62), y + int(h * 0.55)),
            (x + int(w * 0.80), y + int(h * 0.30)), (x + w, y + int(h * 0.42))], SAND)
    bx, by = x + int(w * 0.60), y + int(h * 0.62)
    starburst(c, bx, by, 22, GOLD)
    starburst(c, bx, by, 11, RED)
    arc(c, x + 12, y + h - 14, bx, by, 46, (255, 240, 200), 2)
    arc(c, x + 30, y + 16, bx, by, 30, (255, 240, 200), 2)
    c.text(x + 8, y + 6, "IRAN", 1, INK)
    c.text(x + w - 52, y + h - 14, "BAHRAIN", 1, (255, 255, 255))
    c.text(x + 8, y + h - 14, "HORMUZ", 1, (255, 255, 255))


def icon_climate(c, x, y, w, h):
    c.fill(x, y, w, h, (222, 240, 232))
    cx, cy = x + w // 2 - 18, y + h // 2 - 6
    c.circle(cx, cy, 20, GOLD)
    for dx, dy in ((0, -30), (21, -21), (30, 0), (21, 21), (0, 30), (-21, 21), (-30, 0), (-21, -21)):
        c.line(cx, cy, cx + dx, cy + dy, GOLD, 3)
    c.poly([(x, y + h), (x + w // 3, y + h - 26), (x + 2 * w // 3, y + h - 10), (x + w, y + h - 30),
            (x + w, y + h)], GREEN)
    c.fill(x + w - 26, y + 12, 8, h - 30, (255, 255, 255))
    c.rect(x + w - 26, y + 12, 8, h - 30, INK, 1)
    c.fill(x + w - 24, y + h - 26, 4, 12, RED)
    c.circle(x + w - 22, y + h - 14, 6, RED)


def icon_strike(c, x, y, w, h):
    c.fill(x, y, w, h, (232, 226, 216))
    c.fill(x + 12, y + h - 52, 30, 52, (90, 96, 110))
    c.fill(x + 48, y + h - 74, 34, 74, (70, 76, 92))
    c.fill(x + 88, y + h - 44, 28, 44, (104, 110, 124))
    for bx, by in ((x + 18, y + h - 46), (x + 28, y + h - 46), (x + 56, y + h - 66),
                   (x + 66, y + h - 66), (x + 56, y + h - 52), (x + 94, y + h - 38)):
        c.fill(bx, by, 5, 6, GOLD)
    starburst(c, x + w - 34, y + 26, 20, GOLD)
    starburst(c, x + w - 34, y + 26, 10, RED)
    c.line(x + w - 8, y + 6, x + w - 34, y + 26, RED, 2)


def icon_quake(c, x, y, w, h):
    c.fill(x, y, w, h, (238, 232, 220))
    c.poly([(x, y + h), (x + 26, y + h - 44), (x + 52, y + h)], BROWN)
    c.poly([(x + 38, y + h), (x + 74, y + h - 62), (x + 110, y + h)], (96, 56, 26))
    c.fill(x + 66, y + h - 62, 16, 8, (255, 255, 255))
    pts = [(x + 8, y + 22), (x + 22, y + 22), (x + 30, y + 12), (x + 38, y + 34),
           (x + 46, y + 16), (x + 54, y + 28), (x + 62, y + 20), (x + 76, y + 22),
           (x + 86, y + 14), (x + 96, y + 30), (x + 106, y + 22), (x + w - 8, y + 22)]
    for a, b in zip(pts, pts[1:]):
        c.line(a[0], a[1], b[0], b[1], RED, 2)
    c.text(x + w - 52, y + h - 16, "M6.7", 2, RED)


def icon_arrest(c, x, y, w, h):
    c.fill(x, y, w, h, (226, 230, 238))
    starburst(c, x + w // 2 - 14, y + h // 2, 30, GOLD, spikes=5)
    c.circle(x + w // 2 - 14, y + h // 2, 12, NAVY)
    c.text(x + w // 2 - 22, y + h // 2 - 5, "FBI", 1, (255, 255, 255))
    c.fill(x + w - 30, y + 10, 18, 10, RED)
    c.fill(x + w - 30, y + 24, 18, 10, BLUE)
    c.fill(x + w - 30, y + 38, 18, 10, RED)
    c.fill(x + w - 30, y + 52, 18, 10, BLUE)


def icon_markets(c, x, y, w, h):
    c.fill(x, y, w, h, (240, 236, 224))
    c.line(x + 10, y + 10, x + 10, y + h - 12, INK, 2)
    c.line(x + 10, y + h - 12, x + w - 10, y + h - 12, INK, 2)
    pts = [(x + 14, y + 20), (x + 32, y + 30), (x + 50, y + 26), (x + 68, y + 44),
           (x + 86, y + 40), (x + 104, y + 62), (x + w - 14, y + h - 20)]
    for a, b in zip(pts, pts[1:]):
        c.line(a[0], a[1], b[0], b[1], RED, 3)
    c.poly([(x + w - 14, y + h - 20), (x + w - 26, y + h - 26), (x + w - 22, y + h - 14)], RED)
    c.text(x + w - 58, y + 6, "-5.1%", 2, RED)


def icon_ship(c, x, y, w, h):
    c.fill(x, y, w, h, (214, 230, 242))
    for i in range(4):
        c.fill(x + 8 + i * 30, y + h - 18 - (i % 2) * 4, 22, 4, SEA)
    c.poly([(x + 14, y + h - 30), (x + w - 14, y + h - 30), (x + w - 30, y + h - 14),
            (x + 30, y + h - 14)], (60, 66, 78))
    c.fill(x + w // 2 - 8, y + h - 52, 22, 22, (200, 204, 210))
    c.circle(x + w // 2 + 16, y + h - 62, 10, (120, 120, 120))
    c.circle(x + w // 2 + 24, y + h - 72, 8, (140, 140, 140))
    starburst(c, x + w // 2 + 3, y + h - 46, 12, GOLD)
    starburst(c, x + w // 2 + 3, y + h - 46, 6, RED)


def panel(c, x, y, w, h, accent, kicker, headline, body, icon):
    c.fill(x, y, w, h, CARD)
    c.rect(x, y, w, h, LINE, 1)
    c.fill(x, y, w, 6, accent)
    c.text(x + 12, y + 14, kicker, 1, accent)
    cy = y + 30
    for line in c.wrap(headline, w - 24, 3):
        c.text(x + 12, cy, line, 3, INK)
        cy += 22
    cy += 4
    cy = c.para(x + 12, cy, w - 24, body, 2, (52, 52, 56), leading=15)
    icon(c, x + 12, y + h - 70, w - 24, 58)


# ---------------------------------------------------------------- stories
# Every item below is an event of Saturday 21 November 2026, as
# reported that day by the wire services and major outlets.
BRIEF = [
    ("APEC - Trump calls Putin 'my friend' in Shenzhen", NAVY2),
    ("UKRAINE - Zelensky calls Putin a killer", RED),
    ("POLAND - Russian missile lands on Polish soil", RED),
    ("GULF - Tanker strikes near Hormuz hit wartime high", RED),
    ("GULF - Iran says it downed a US drone near Qeshm", RED),
    ("USA - Vance declines to back Trump on Iran claim", NAVY2),
    ("CHINA - Chinese AI stocks shed $1.7 trillion", AMBER),
    ("CHINA - Nvidia halts H200 AI chip exports", AMBER),
    ("CRYPTO - Liquidations pass $2B; Bitcoin nears $62K", AMBER),
    ("CANADA - Strongest retail numbers since 2022", GREEN),
    ("NEPAL - PM Balendra Shah begins first India visit", TEAL),
    ("INDIA - Modi links culture to peace at SCO forum", TEAL),
    ("KASHMIR - India says last militant killed in raid", RED),
    ("USA - Indian jailed 19 years over Pannun plot", NAVY2),
    ("IRAQ - Blast at Basra power plant kills 4, hurts 30", RED),
    ("WEST BANK - Israel plans new city for 200,000", RED),
    ("MYANMAR - Myanmar rejects ICJ Rohingya ruling", TEAL),
    ("DENMARK - Russia accused of plot to kill rapper", RED),
    ("FRANCE - Police jailed over beating of Zecler", NAVY2),
    ("USA - Man convicted of starting Palisades fire", AMBER),
    ("USA - FBI probes apparent hack of crime database", NAVY2),
    ("SPACE - NASA halts Perseverance science over faults", BLUE),
    ("HEALTH - Mosquitoes cut child dengue 69% in Brazil", GREEN),
    ("S. AFRICA - ANC fights to hold key cities", TEAL),
    ("SPORT - Russell takes pole for Las Vegas GP", BLUE),
    ("SPORT - Alcaraz reaches ATP Finals championship", BLUE),
    ("SPORT - Wales beat All Blacks, first in 73 years", BLUE),
    ("SPORT - Ronaldo scores 986th goal, misses penalty", BLUE),
    ("SPORT - Real Madrid beat Celta 2-1, ninth win in row", BLUE),
    ("SPORT - Leeds thrash Chelsea 4-1 at Stamford Bridge", BLUE),
]

REGIONS = [
    ("MIDDLE EAST", RED), ("EUROPE", NAVY2), ("ASIA", TEAL),
    ("N. AMERICA", AMBER), ("S. AMERICA", GREEN), ("AFRICA", BROWN),
]


def draw(c):
    c.fill(0, 0, W, H, PAPER)

    # Masthead
    c.fill(0, 0, W, 92, NAVY)
    c.fill(0, 92, W, 3, GOLD)
    c.text_center(W // 2, 14, "THE WORLD IN ONE PICTURE", 4, (255, 255, 255))
    c.text_center(W // 2, 50, "SATURDAY 21 NOVEMBER 2026", 3, GOLD)
    c.text_center(W // 2, 78, "ONE DAY IN WORLD NEWS  -  37 STORIES  -  6 REGIONS", 1,
                  (200, 208, 224))

    # Lead story
    c.fill(24, 104, 976, 214, CARD)
    c.rect(24, 104, 976, 214, LINE, 1)
    c.fill(24, 104, 976, 6, RED)
    c.text(40, 118, "MIDDLE EAST  -  CONFLICT  -  LEAD STORY", 1, RED)
    c.text(40, 134, "IRAN STRIKES BAHRAIN", 5, INK)
    c.para(40, 180, 620,
           "Iran's Revolutionary Guards say they hit two US bases, at "
           "al-Riffa and Awali. Bahrain says the attack set a civilian "
           "industrial site ablaze; no one was hurt and air defences "
           "stopped the rest.", 2, (52, 52, 56), leading=17)
    c.para(40, 252, 620,
           "Tehran also says it downed a US drone near Qeshm Island. "
           "Tanker strikes near Hormuz reach a wartime high; oil flows "
           "fall 15%.", 2, (52, 52, 56), leading=17)
    icon_gulf(c, 676, 116, 308, 190)

    # First row of panels
    panel(c, 24, 342, 312, 208, TEAL, "CLIMATE - ANTALYA",
          "COP31 INTO OVERTIME",
          "UN climate talks run past deadline; a deal is said to be close.", icon_climate)
    panel(c, 356, 342, 312, 208, RED, "WAR - UKRAINE",
          "MISSILE HITS KRYVYI RIH",
          "A triple-tap strike kills a boy, 7, and a paramedic; 28 hurt.", icon_strike)
    panel(c, 688, 342, 312, 208, BROWN, "DISASTER - PERU",
          "DEEP QUAKE SHAKES PERU",
          "A magnitude 6.7 quake strikes central Peru, shaking the "
          "Andes.", icon_quake)

    # Second row of panels
    panel(c, 24, 562, 312, 208, NAVY2, "CRIME - MEXICO",
          "EL CHAPO ISIDRO CAPTURED",
          "Mexico captures FBI most-wanted cartel boss; 11 die in the "
          "violence.", icon_arrest)
    panel(c, 356, 562, 312, 208, AMBER, "MARKETS - NEW YORK",
          "NASDAQ ERASES 2026 GAINS",
          "AI and chip shares plunge; the S&P 500 slips into "
          "correction.", icon_markets)
    panel(c, 688, 562, 312, 208, BLUE, "WAR AT SEA - FINLAND",
          "RUSSIAN SHIP ABLAZE",
          "Cargo ship Sparta II burns in the Gulf of Finland after a "
          "strike.", icon_ship)

    # The day in brief
    c.text(24, 782, "THE DAY IN BRIEF", 3, INK)
    c.hline(24, 808, 976, INK, 2)
    cols = [BRIEF[i::3] for i in range(3)]
    for ci, col in enumerate(cols):
        x = 24 + ci * 332
        cy = 818
        for text, color in col:
            c.fill(x, cy + 1, 6, 6, color)
            c.text(x + 12, cy, text, 1, (40, 40, 44))
            cy += 14

    # Footer: what the day covered, and the sources.
    c.hline(24, 972, 976, LINE, 1)
    fx = 24
    for name, color in REGIONS:
        c.fill(fx, 984, 8, 8, color)
        fx += 12
        fx += c.text(fx, 982, name, 1, GRAY)
        fx += 16
    c.text_center(W // 2, 1002,
                  "ALL EVENTS OF SATURDAY 21 NOVEMBER 2026 - COMPILED FROM "
                  "WIRE REPORTS", 1, GRAY)


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    canvas = Canvas(W, H, PAPER)
    draw(canvas)
    path = os.path.join(outdir, "entry.png")
    size = write_png(path, canvas)
    print("wrote %s (%d bytes)" % (path, size))


if __name__ == "__main__":
    main()
