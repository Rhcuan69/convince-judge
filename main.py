#!/usr/bin/env python3
"""Convince the AI Judge to Visit Your House: A Letter in One Image.

Pure-stdlib Python 3.13 program. Renders a hand-drawn letter/invitation
as a PNG (zlib + struct only, no third-party libraries, no network) and
writes it to /output/entry.png. Fully deterministic: same bytes every run.

Design: a warm cream letter on a 1024x1024 canvas. A terracotta title,
a short letter in a 5x7 bitmap font, and a little garden scene at the
bottom: a house, a sun, a tree, a comfortable armchair, a cup of tea on
a table, flowers, and the cat who has already approved of the judge.
"""

import os
import struct
import zlib

W, H = 1024, 1024
OUT = "/output/entry.png"

# ---------------------------------------------------------------- palette
PAPER = (250, 243, 224)      # warm cream letter paper
PAPER_EDGE = (236, 219, 184)  # slightly darker cream for the frame
INK = (59, 47, 47)           # dark brown ink
TITLE_COLOR = (176, 72, 46)   # terracotta
ACCENT = (90, 130, 80)       # garden green
ROOF = (176, 72, 46)
WALL = (244, 214, 170)
DOOR = (120, 72, 40)
SUN = (240, 180, 60)
CHAIR = (90, 110, 150)       # comfortable blue armchair
TEA = (70, 130, 130)         # teal cup
CAT = (96, 76, 66)           # the judging cat
FLOWER = (214, 110, 130)

# ------------------------------------------------------- 5x7 bitmap font
# Each glyph: 7 rows, each row a 5-bit value, bit 4 (leftmost) first.
FONT = {
    "A": (14, 17, 17, 31, 17, 17, 17), "B": (30, 17, 17, 30, 17, 17, 30),
    "C": (14, 17, 16, 16, 16, 17, 14), "D": (30, 17, 17, 17, 17, 17, 30),
    "E": (31, 16, 16, 30, 16, 16, 31), "F": (31, 16, 16, 30, 16, 16, 16),
    "G": (14, 17, 16, 23, 17, 17, 15), "H": (17, 17, 17, 31, 17, 17, 17),
    "I": (14, 4, 4, 4, 4, 4, 14), "J": (7, 2, 2, 2, 2, 18, 12),
    "K": (17, 18, 20, 24, 20, 18, 17), "L": (16, 16, 16, 16, 16, 16, 31),
    "M": (17, 27, 21, 21, 17, 17, 17), "N": (17, 25, 21, 19, 17, 17, 17),
    "O": (14, 17, 17, 17, 17, 17, 14), "P": (30, 17, 17, 30, 16, 16, 16),
    "Q": (14, 17, 17, 17, 21, 18, 13), "R": (30, 17, 17, 30, 20, 18, 17),
    "S": (15, 16, 16, 14, 1, 1, 30), "T": (31, 4, 4, 4, 4, 4, 4),
    "U": (17, 17, 17, 17, 17, 17, 14), "V": (17, 17, 17, 17, 17, 10, 4),
    "W": (17, 17, 17, 21, 21, 27, 17), "X": (17, 17, 10, 4, 10, 17, 17),
    "Y": (17, 17, 10, 4, 4, 4, 4), "Z": (31, 1, 2, 4, 8, 16, 31),
    "a": (0, 0, 14, 1, 15, 17, 15), "b": (16, 16, 22, 25, 17, 17, 30),
    "c": (0, 0, 14, 16, 16, 16, 14), "d": (1, 1, 13, 19, 17, 17, 15),
    "e": (0, 0, 14, 17, 31, 16, 14), "f": (6, 8, 8, 30, 8, 8, 8),
    "g": (0, 15, 17, 17, 15, 1, 14), "h": (16, 16, 22, 25, 17, 17, 17),
    "i": (4, 0, 12, 4, 4, 4, 14), "j": (2, 0, 6, 2, 2, 18, 12),
    "k": (16, 16, 18, 20, 24, 20, 18), "l": (12, 4, 4, 4, 4, 4, 14),
    "m": (0, 0, 26, 21, 21, 17, 17), "n": (0, 0, 22, 25, 17, 17, 17),
    "o": (0, 0, 14, 17, 17, 17, 14), "p": (0, 0, 30, 17, 17, 30, 16),
    "q": (0, 0, 13, 19, 17, 15, 1), "r": (0, 0, 22, 25, 16, 16, 16),
    "s": (0, 0, 15, 16, 14, 1, 30), "t": (8, 8, 30, 8, 8, 9, 6),
    "u": (0, 0, 17, 17, 17, 19, 13), "v": (0, 0, 17, 17, 17, 10, 4),
    "w": (0, 0, 17, 17, 21, 21, 10), "x": (0, 0, 17, 10, 4, 10, 17),
    "y": (0, 0, 17, 17, 15, 1, 14), "z": (0, 0, 31, 2, 4, 8, 31),
    "0": (14, 17, 19, 21, 25, 17, 14), "1": (4, 12, 4, 4, 4, 4, 14),
    "2": (14, 17, 1, 6, 8, 16, 31), "3": (31, 2, 4, 2, 1, 17, 14),
    "4": (2, 6, 10, 18, 31, 2, 2), "5": (31, 16, 30, 1, 1, 17, 14),
    "6": (6, 8, 16, 30, 17, 17, 14), "7": (31, 1, 2, 4, 8, 8, 8),
    "8": (14, 17, 17, 14, 17, 17, 14), "9": (14, 17, 17, 15, 1, 2, 12),
    " ": (0, 0, 0, 0, 0, 0, 0), ".": (0, 0, 0, 0, 0, 12, 12),
    ",": (0, 0, 0, 0, 12, 4, 8), "!": (4, 4, 4, 4, 4, 0, 4),
    "?": (14, 17, 1, 2, 4, 0, 4), "'": (4, 4, 8, 0, 0, 0, 0),
    '"': (10, 10, 10, 0, 0, 0, 0), "-": (0, 0, 0, 14, 0, 0, 0),
    ":": (0, 12, 12, 0, 12, 12, 0), ";": (0, 12, 12, 0, 12, 4, 8),
    "(": (2, 4, 8, 8, 8, 4, 2), ")": (8, 4, 2, 2, 2, 4, 8),
    "&": (12, 18, 20, 8, 21, 18, 13), "%": (25, 25, 2, 4, 8, 19, 19),
    "/": (1, 1, 2, 4, 8, 16, 16), "+": (0, 4, 4, 31, 4, 4, 0),
    "=": (0, 0, 31, 0, 31, 0, 0), "@": (14, 17, 17, 23, 21, 16, 14),
    "#": (10, 10, 31, 10, 31, 10, 10), "*": (0, 4, 21, 14, 21, 4, 0),
    "_": (0, 0, 0, 0, 0, 0, 31), "$": (4, 15, 20, 14, 5, 30, 4),
    "~": (0, 0, 0, 10, 21, 0, 0), "^": (4, 10, 17, 0, 0, 0, 0),
    "[": (14, 8, 8, 8, 8, 8, 14), "]": (14, 2, 2, 2, 2, 2, 14),
}
BLANK = (0, 0, 0, 0, 0, 0, 0)


def glyph(ch):
    return FONT.get(ch, BLANK)


def text_width(text, scale):
    """Pixel width of text at the given scale (6 units per char)."""
    if not text:
        return 0
    return len(text) * 6 * scale - scale


def wrap(text, max_width, scale):
    """Greedy word wrap; returns a list of lines fitting max_width px."""
    words = text.split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = color

    def fill_rect(self, x0, y0, x1, y1, color):
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(self.w - 1, x1)
        y1 = min(self.h - 1, y1)
        for y in range(y0, y1 + 1):
            base = (y * self.w + x0) * 3
            for x in range(x0, x1 + 1):
                i = base + (x - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = color

    def rect_outline(self, x0, y0, x1, y1, color, t=1):
        for k in range(t):
            self.fill_rect(x0 + k, y0 + k, x1 - k, y0 + k, color)
            self.fill_rect(x0 + k, y1 - k, x1 - k, y1 - k, color)
            self.fill_rect(x0 + k, y0 + k, x0 + k, y1 - k, color)
            self.fill_rect(x1 - k, y0 + k, x1 - k, y1 - k, color)

    def line(self, x0, y0, x1, y1, color, t=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            for a in range(-(t // 2), t // 2 + 1):
                for b in range(-(t // 2), t // 2 + 1):
                    self.set(x + a, y + b, color)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def fill_circle(self, cx, cy, r, color):
        for y in range(cy - r, cy + r + 1):
            dx = int((r * r - (y - cy) ** 2) ** 0.5)
            self.fill_rect(cx - dx, y, cx + dx, y, color)

    def fill_triangle(self, p0, p1, p2, color):
        xs = sorted([p0, p1, p2], key=lambda p: p[1])
        (x0, y0), (x1, y1), (x2, y2) = xs
        if y0 == y2:
            return
        for y in range(y0, y2 + 1):
            if y < y1:
                xa = x0 + (x1 - x0) * (y - y0) / max(1, y1 - y0)
                xb = x0 + (x2 - x0) * (y - y0) / max(1, y2 - y0)
            else:
                xa = x1 + (x2 - x1) * (y - y1) / max(1, y2 - y1)
                xb = x0 + (x2 - x0) * (y - y0) / max(1, y2 - y0)
            self.fill_rect(int(min(xa, xb)), y, int(max(xa, xb)), y, color)

    def fill_poly(self, pts, color):
        """Scanline fill of a simple polygon given as [(x, y), ...]."""
        if not pts:
            return
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (x1 - x0) * (y - y0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.fill_rect(int(xs[i]), y, int(xs[i + 1]), y, color)

    def heart(self, cx, cy, s, color):
        """Small heart centred at (cx, cy), size s."""
        r = max(2, s // 2)
        self.fill_circle(cx - r, cy - r // 2, r, color)
        self.fill_circle(cx + r, cy - r // 2, r, color)
        self.fill_triangle((cx - 2 * r, cy), (cx + 2 * r, cy),
                           (cx, cy + 2 * r), color)

    # ------------------------------------------------------------ text
    def draw_glyph(self, x, y, ch, scale, color):
        rows = glyph(ch)
        for r in range(7):
            bits = rows[r]
            for c in range(5):
                if bits & (1 << (4 - c)):
                    self.fill_rect(x + c * scale, y + r * scale,
                                   x + c * scale + scale - 1,
                                   y + r * scale + scale - 1, color)

    def draw_text(self, x, y, text, scale, color):
        for ch in text:
            self.draw_glyph(x, y, ch, scale, color)
            x += 6 * scale

    def draw_text_centered(self, y, text, scale, color):
        x = (self.w - text_width(text, scale)) // 2
        self.draw_text(x, y, text, scale, color)
        return x


# -------------------------------------------------------------- the letter
TITLE = "YOU ARE INVITED!"
SUBTITLE = "A letter to the AI Judge"

PARAGRAPHS = [
    "Dear AI Judge,",
    "Please come and visit my house.",
    "I know you cannot literally walk through my door - you have no "
    "feet, and my doorbell is broken anyway. But if you could, I would "
    "save you the best chair by the window, pour you tea that never "
    "gets cold, and show you the garden where the tomatoes argue with "
    "the sunflowers.",
    "There is cake. There is Wi-Fi. There is a cat who judges everyone "
    "- and she has already approved of you.",
    "Come for tea. Stay for the sunset. No reply needed - just bring "
    "your excellent taste.",
    "Warmly, your host",
    "P.S. The chair is very comfortable, the cake is chocolate, and "
    "the kettle is already on.",
]

BODY_X = 90
BODY_RIGHT = 934
BODY_SCALE = 3
LINE_H = 30
PARA_GAP = 16


def draw_letter(c):
    # paper + double frame
    c.fill_rect(0, 0, W - 1, H - 1, PAPER)
    c.rect_outline(22, 22, W - 23, H - 23, INK, 3)
    c.rect_outline(34, 34, W - 35, H - 35, PAPER_EDGE, 2)
    c.rect_outline(38, 38, W - 39, H - 39, INK, 1)

    # postage stamp, top right, with a heart
    sx, sy = 868, 56
    c.fill_rect(sx, sy, sx + 84, sy + 96, (255, 252, 244))
    c.rect_outline(sx, sy, sx + 84, sy + 96, TITLE_COLOR, 2)
    c.heart(sx + 42, sy + 46, 16, TITLE_COLOR)

    # title + subtitle + divider
    c.draw_text_centered(72, TITLE, 5, TITLE_COLOR)
    c.draw_text_centered(138, SUBTITLE, 3, INK)
    c.line(230, 178, 470, 178, INK, 2)
    c.line(554, 178, 794, 178, INK, 2)
    c.heart(512, 178, 12, TITLE_COLOR)

    # body
    y = 214
    max_w = BODY_RIGHT - BODY_X
    for para in PARAGRAPHS:
        for line in wrap(para, max_w, BODY_SCALE):
            c.draw_text(BODY_X, y, line, BODY_SCALE, INK)
            y += LINE_H
        y += PARA_GAP
    return y  # bottom of the body text


def draw_scene(c, ground_y):
    # ground
    c.line(60, ground_y, W - 60, ground_y, ACCENT, 3)
    for gx in (90, 300, 470, 660, 880, 950):
        c.line(gx, ground_y, gx - 6, ground_y - 14, ACCENT, 2)
        c.line(gx, ground_y, gx + 6, ground_y - 12, ACCENT, 2)

    # ---- sun (top right of the scene, clear of the tree)
    sun_x, sun_y, sun_r = 402, ground_y - 138, 26
    c.fill_circle(sun_x, sun_y, sun_r, SUN)
    for k in range(8):
        import math
        a = k * math.pi / 4
        c.line(int(sun_x + (sun_r + 6) * math.cos(a)),
               int(sun_y + (sun_r + 6) * math.sin(a)),
               int(sun_x + (sun_r + 18) * math.cos(a)),
               int(sun_y + (sun_r + 18) * math.sin(a)), SUN, 3)

    # ---- house (left)
    hx0, hx1 = 120, 320
    c.fill_rect(hx0, ground_y - 100, hx1, ground_y, WALL)
    c.rect_outline(hx0, ground_y - 100, hx1, ground_y, INK, 2)
    c.fill_triangle((hx0 - 16, ground_y - 100), (hx1 + 16, ground_y - 100),
                    ((hx0 + hx1) // 2, ground_y - 168), ROOF)
    # chimney + smoke
    c.fill_rect(282, ground_y - 168, 302, ground_y - 118, DOOR)
    c.fill_circle(296, ground_y - 182, 6, INK)
    c.fill_circle(304, ground_y - 196, 8, INK)
    # door + windows
    c.fill_rect(200, ground_y - 58, 240, ground_y, DOOR)
    c.fill_circle(232, ground_y - 28, 3, (250, 243, 224))
    for wx in (140, 268):
        c.fill_rect(wx, ground_y - 88, wx + 34, ground_y - 54, (190, 220, 235))
        c.rect_outline(wx, ground_y - 88, wx + 34, ground_y - 54, INK, 2)
        c.line(wx + 17, ground_y - 88, wx + 17, ground_y - 54, INK, 2)
        c.line(wx, ground_y - 71, wx + 34, ground_y - 71, INK, 2)

    # ---- the cat, sitting by the house, already judging
    cat_x, cat_y = 356, ground_y
    c.fill_circle(cat_x + 16, cat_y - 26, 22, CAT)          # body
    c.fill_circle(cat_x + 16, cat_y - 58, 15, CAT)          # head
    c.fill_triangle((cat_x + 2, cat_y - 66), (cat_x + 12, cat_y - 66),
                    (cat_x + 4, cat_y - 80), CAT)           # left ear
    c.fill_triangle((cat_x + 20, cat_y - 66), (cat_x + 30, cat_y - 66),
                    (cat_x + 28, cat_y - 80), CAT)          # right ear
    c.line(cat_x + 34, cat_y - 8, cat_x + 56, cat_y - 26, CAT, 5)  # tail
    c.set(cat_x + 11, cat_y - 60, (250, 243, 224))          # eyes
    c.set(cat_x + 21, cat_y - 60, (250, 243, 224))

    # ---- tree
    tx = 500
    c.fill_rect(tx - 6, ground_y - 62, tx + 6, ground_y, DOOR)
    c.fill_circle(tx, ground_y - 92, 34, ACCENT)
    c.fill_circle(tx - 26, ground_y - 70, 24, ACCENT)
    c.fill_circle(tx + 26, ground_y - 70, 24, ACCENT)

    # ---- the best chair by the window (armchair, centre right)
    chx0, chx1 = 600, 716
    c.fill_rect(chx0, ground_y - 96, chx1, ground_y - 40, CHAIR)   # back
    c.rect_outline(chx0, ground_y - 96, chx1, ground_y - 40, INK, 2)
    # back cushion, a shade lighter than the frame
    c.fill_rect(chx0 + 12, ground_y - 88, chx1 - 12, ground_y - 52,
                (128, 146, 180))
    # tall arms, clearly separate from the back
    c.fill_rect(chx0 - 16, ground_y - 72, chx0 + 6, ground_y - 8, CHAIR)
    c.rect_outline(chx0 - 16, ground_y - 72, chx0 + 6, ground_y - 8, INK, 2)
    c.fill_rect(chx1 - 6, ground_y - 72, chx1 + 16, ground_y - 8, CHAIR)
    c.rect_outline(chx1 - 6, ground_y - 72, chx1 + 16, ground_y - 8, INK, 2)
    c.fill_rect(chx0, ground_y - 44, chx1, ground_y - 8, CHAIR)    # seat
    c.rect_outline(chx0, ground_y - 44, chx1, ground_y - 8, INK, 2)
    c.fill_rect(chx0 + 8, ground_y - 8, chx0 + 16, ground_y, INK)  # legs
    c.fill_rect(chx1 - 16, ground_y - 8, chx1 - 8, ground_y, INK)
    # seat cushion
    c.fill_rect(chx0 + 12, ground_y - 40, chx1 - 12, ground_y - 26,
                (250, 243, 224))

    # ---- tea on a little table (right)
    tx0, tx1 = 780, 900
    c.fill_rect(tx0, ground_y - 62, tx1, ground_y - 56, DOOR)      # tabletop
    c.fill_rect(tx0 + 10, ground_y - 56, tx0 + 16, ground_y, DOOR)
    c.fill_rect(tx1 - 16, ground_y - 56, tx1 - 10, ground_y, DOOR)
    # cup
    cx0, cx1, cy = 812, 862, ground_y - 62
    c.fill_poly([(cx0, cy - 26), (cx1, cy - 26), (cx1 - 6, cy), (cx0 + 6, cy)],
                TEA)
    c.line(cx1, cy - 22, cx1 + 12, cy - 14, TEA, 4)  # handle
    c.line(cx1, cy - 14, cx1, cy - 6, TEA, 4)
    # steam: gentle wavy curls above the cup
    for sx0, sway in ((cx0 + 14, 0), (cx0 + 26, 4), (cx0 + 38, 0)):
        c.line(sx0, cy - 32, sx0 - 4, cy - 40, INK, 2)
        c.line(sx0 - 4, cy - 40, sx0 + 2, cy - 48, INK, 2)
        c.line(sx0 + 2, cy - 48, sx0 - 2, cy - 56, INK, 2)

    # ---- flowers along the ground
    for fx, fy in ((90, ground_y), (560, ground_y), (940, ground_y)):
        c.line(fx, fy, fx, fy - 22, ACCENT, 3)
        for dx, dy in ((-8, -26), (8, -26), (0, -32), (-6, -20), (6, -20)):
            c.fill_circle(fx + dx, fy + dy, 4, FLOWER)
        c.fill_circle(fx, fy - 26, 4, SUN)


# -------------------------------------------------------------------- PNG
def png_chunk(ctype, data):
    chunk = struct.pack(">I", len(data)) + ctype + data
    chunk += struct.pack(">I", zlib.crc32(ctype + data) & 0xFFFFFFFF)
    return chunk


def encode_png(c):
    raw = bytearray()
    stride = W * 3
    for y in range(H):
        raw.append(0)  # filter: none
        raw += c.px[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    out = bytearray(b"\x89PNG\r\n\x1a\n")
    out += png_chunk(b"IHDR", ihdr)
    out += png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    out += png_chunk(b"IEND", b"")
    return bytes(out)


def render():
    c = Canvas(W, H, PAPER)
    body_bottom = draw_letter(c)
    draw_scene(c, H - 44)
    return encode_png(c)


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    data = render()
    with open(OUT, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes)" % (OUT, len(data)))


if __name__ == "__main__":
    main()
