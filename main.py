#!/usr/bin/env python3
"""news-image-20261125 v1 — draws a newspaper front page summing up
Wednesday 25 November 2026 world news. Standard library only.
Writes /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png).
Fully deterministic: no timestamps, no randomness, no network.
"""
import os
import struct
import zlib

# ---------------------------------------------------------------- font ----
# 5x7 bitmap font, rows are 5-char strings ('#' = pixel on).
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
}

# ------------------------------------------------------------- canvas -----
W, H = 1024, 1024
PAPER = (250, 246, 236)
INK = (18, 18, 20)
NAVY = (16, 38, 74)
RED = (178, 34, 34)
GREY = (110, 110, 108)


class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bytes(bg) * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(c)

    def rect(self, x, y, w, h, c):
        for yy in range(max(0, y), min(self.h, y + h)):
            i = (yy * self.w + max(0, x)) * 3
            n = min(self.w, x + w) - max(0, x)
            if n > 0:
                self.px[i:i + n * 3] = bytes(c) * n

    def circle(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            dx = int((r * r - (yy - cy) ** 2) ** 0.5)
            self.rect(cx - dx, yy, dx * 2 + 1, 1, c)

    def line(self, x0, y0, x1, y1, c, th=1):
        dx, dy = x1 - x0, y1 - y0
        steps = max(abs(dx), abs(dy), 1)
        for s in range(steps + 1):
            x = x0 + dx * s // steps
            y = y0 + dy * s // steps
            self.rect(x, y, th, th, c)

    def tri(self, pts, c):
        # scanline fill of a triangle
        (x0, y0), (x1, y1), (x2, y2) = pts
        ys = sorted([y0, y1, y2])
        for y in range(ys[0], ys[2] + 1):
            xs = []
            for (ax, ay), (bx, by) in (((x0, y0), (x1, y1)),
                                       ((x1, y1), (x2, y2)),
                                       ((x2, y2), (x0, y0))):
                if ay == by:
                    continue
                if min(ay, by) <= y <= max(ay, by):
                    xs.append(ax + (bx - ax) * (y - ay) // (by - ay))
            if len(xs) >= 2:
                self.rect(min(xs), y, max(xs) - min(xs) + 1, 1, c)


def text_w(s, scale):
    return len(s) * (5 * scale + scale) - scale


def draw_text(cv, x, y, s, scale, color):
    s = s.upper()
    cx = x
    for ch in s:
        glyph = FONT.get(ch, FONT[' '])
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == '1':
                    cv.rect(cx + col * scale, y + row * scale, scale, scale, color)
        cx += 6 * scale
    return cx


def wrap(text, scale, max_w):
    cw = 6 * scale
    max_chars = max(1, max_w // cw)
    lines, cur = [], ""
    for word in text.upper().split(" "):
        trial = word if not cur else cur + " " + word
        if len(trial) <= max_chars:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# -------------------------------------------------------------- icons -----
def icon_ship(cv, x, y, s=160):
    # sea + ship + blast star
    cv.rect(x, y, s, s, (24, 90, 140))
    cv.rect(x, y + int(s * 0.62), s, s - int(s * 0.62), (10, 55, 95))
    cv.rect(x + 28, y + 78, 104, 26, (30, 30, 34))          # hull
    cv.tri([(x + 28, y + 78), (x + 132, y + 78), (x + 118, y + 104)], (30, 30, 34))
    cv.rect(x + 74, y + 34, 6, 46, (30, 30, 34))            # mast
    cv.rect(x + 80, y + 40, 34, 18, (200, 60, 40))          # flag
    cv.circle(x + 128, y + 34, 16, (255, 190, 40))          # blast
    cv.circle(x + 128, y + 34, 9, (255, 230, 120))


def icon_globe(cv, x, y, s=160):
    cv.rect(x, y, s, s, (214, 232, 214))
    cv.circle(x + 80, y + 80, 58, (38, 120, 70))            # earth
    cv.circle(x + 62, y + 62, 16, (120, 190, 110))          # land
    cv.circle(x + 100, y + 96, 20, (120, 190, 110))
    cv.circle(x + 92, y + 52, 9, (120, 190, 110))
    cv.circle(x + 132, y + 26, 14, (255, 190, 40))          # sun
    cv.rect(x + 20, y + 138, 120, 4, (178, 34, 34))         # no-deal bar


def icon_court(cv, x, y, s=160):
    cv.rect(x, y, s, s, (232, 226, 214))
    cv.tri([(x + 20, y + 52), (x + 140, y + 52), (x + 80, y + 22)], (120, 90, 40))  # pediment
    for cx0 in (30, 62, 94, 126):
        cv.rect(x + cx0, y + 56, 12, 62, (90, 70, 45))      # columns
    cv.rect(x + 20, y + 118, 120, 10, (90, 70, 45))         # base
    cv.rect(x + 20, y + 52, 120, 4, (90, 70, 45))
    cv.rect(x + 66, y + 132, 28, 8, (178, 34, 34))          # verdict stamp


def icon_shield(cv, x, y, s=160):
    cv.rect(x, y, s, s, (30, 30, 44))
    # shield outline
    pts = [(80, 18), (128, 34), (128, 84), (80, 142), (32, 84), (32, 34)]
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        cv.line(x + a[0], y + a[1], x + b[0], y + b[1], (255, 200, 60), 3)
    # lightning crack
    cv.line(x + 88, y + 44, x + 66, y + 82, (255, 200, 60), 5)
    cv.line(x + 66, y + 82, x + 92, y + 82, (255, 200, 60), 5)
    cv.line(x + 92, y + 82, x + 70, y + 122, (255, 200, 60), 5)


def icon_chip(cv, x, y, s=160):
    cv.rect(x, y, s, s, (16, 60, 40))
    for px in (52, 74, 96):
        cv.rect(x + px, y + 18, 8, 22, (60, 200, 120))
        cv.rect(x + px, y + 120, 8, 22, (60, 200, 120))
        cv.rect(x + 18, y + px, 22, 8, (60, 200, 120))
        cv.rect(x + 120, y + px, 22, 8, (60, 200, 120))
    cv.rect(x + 46, y + 46, 68, 68, (20, 120, 80))          # chip body
    cv.rect(x + 58, y + 58, 44, 44, (120, 230, 170))
    # rising arrow
    cv.line(x + 30, y + 128, x + 74, y + 92, (255, 200, 60), 5)
    cv.line(x + 74, y + 92, x + 128, y + 44, (255, 200, 60), 5)
    cv.tri([(x + 128, y + 44), (x + 112, y + 44), (x + 128, y + 60)], (255, 200, 60))


ICONS = [icon_ship, icon_globe, icon_court, icon_shield, icon_chip]

STORIES = [
    ("UKRAINE STRIKES RUSSIAN SHIPS AT SEA",
     "KYIV CONFIRMED DRONE STRIKES ON A RUSSIAN CARGO SHIP IN THE GULF OF "
     "FINLAND AND A WARSHIP OFF LIBYA. MOSCOW CALLED THE ATTACKS TERRORISM."),
    ("COP31 CLIMATE TALKS END WITH NO DEAL",
     "THE UN CLIMATE SUMMIT IN ANTALYA CLOSED WITHOUT A FINAL AGREEMENT "
     "AFTER OIL AND GAS PRODUCERS BLOCKED FOSSIL-FUEL PHASEOUT LANGUAGE."),
    ("HUAWEI FOUND GUILTY IN US TRIAL",
     "A NEW YORK JURY CONVICTED THE CHINESE TELECOM GIANT ON 10 OF 12 "
     "COUNTS, INCLUDING TRADE-SECRET THEFT AND BANK FRAUD. HUAWEI REJECTED "
     "THE VERDICTS."),
    ("US SPY AGENCIES HIT BY CYBERATTACK",
     "THE CIA AND THE OFFICE OF THE DIRECTOR OF NATIONAL INTELLIGENCE WERE "
     "HIT BY A CYBER INTRUSION AFFECTING CLASSIFIED SYSTEMS, SOURCES TOLD CNN."),
    ("NVIDIA BRINGS BACK HUANG AS CEO",
     "NVIDIA'S BOARD UNANIMOUSLY REINSTATED JENSEN HUANG AS PRESIDENT AND "
     "CEO DAYS AFTER ACCEPTING HIS RESIGNATION. ASIAN TECH SHARES SLID."),
]


def build():
    cv = Canvas(W, H, PAPER)
    # masthead
    cv.rect(0, 0, W, 132, NAVY)
    cv.rect(0, 132, W, 4, RED)
    mast = "WEDNESDAY 25 NOVEMBER 2026"
    draw_text(cv, (W - text_w(mast, 5)) // 2, 26, mast, 5, (255, 255, 255))
    sub = "THE WORLD IN ONE IMAGE"
    draw_text(cv, (W - text_w(sub, 2)) // 2, 92, sub, 2, (200, 210, 225))
    # story blocks
    y = 144
    for i, (headline, summary) in enumerate(STORIES):
        cv.rect(16, y, 992, 168, (255, 255, 255))
        cv.rect(16, y, 992, 3, RED)
        ICONS[i](cv, 24, y + 4)
        tx = 204
        hlines = wrap(headline, 3, 1024 - tx - 16)
        hy = y + 14
        for ln in hlines[:2]:
            draw_text(cv, tx, hy, ln, 3, INK)
            hy += 28
        cv.rect(tx, y + 74, 804, 2, GREY)
        slines = wrap(summary, 2, 1024 - tx - 16)
        sy = y + 86
        for ln in slines[:4]:
            draw_text(cv, tx, sy, ln, 2, (40, 40, 44))
            sy += 22
        y += 176
    return cv


# --------------------------------------------------------------- png ------
def chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def write_png(cv, path):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * cv.w * 3:(y + 1) * cv.w * 3]
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    # validation guard: refuse to write an out-of-spec entry
    if cv.w > 1024 or cv.h > 1024:
        raise ValueError(f"dimensions {cv.w}x{cv.h} exceed 1024x1024 limit")
    if len(png) > 1048576:
        raise ValueError(f"PNG {len(png)} bytes exceeds 1 MiB limit")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    cv = build()
    size = write_png(cv, os.path.join(out_dir, "entry.png"))
    print(f"wrote entry.png {cv.w}x{cv.h} {size} bytes")


if __name__ == "__main__":
    main()
