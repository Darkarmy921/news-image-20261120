#!/usr/bin/env python3
"""ONE DAY ON EARTH — news-image-20261120.

Renders a 1024x1024 newspaper front page summing up the world's news
of Friday 20 November 2026 and writes it to /output/entry.png.

Standard library only. No network, no clock, no randomness: the same
run always writes the same bytes. Text is drawn from glyph bitmaps
baked into fontdata.py (DejaVu fonts, OFL) so no font file is needed
at render time.
"""

import base64
import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fontdata import FONTS  # noqa: E402

W, H = 1024, 1024

PAPER = (247, 243, 234)
INK = (20, 20, 20)
GREY = (138, 131, 120)
RED = (163, 18, 18)
RED_LT = (224, 88, 74)
BLUE = (28, 77, 143)
NAVY = (35, 56, 118)
GREEN = (30, 107, 58)
ORANGE = (178, 90, 16)
TEAL = (15, 107, 107)
WHITE = (255, 255, 255)

MARGIN = 28
CW = W - 2 * MARGIN  # 968


# ---------------------------------------------------------------- canvas

class Canvas:
    def __init__(self):
        self.buf = bytearray(PAPER * (W * H))

    def px(self, x, y, color):
        if 0 <= x < W and 0 <= y < H:
            i = (y * W + x) * 3
            self.buf[i], self.buf[i + 1], self.buf[i + 2] = color

    def rect(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(W, x + w), min(H, y + h)
        for yy in range(y0, y1):
            base = (yy * W + x0) * 3
            row = bytes(color) * (x1 - x0)
            self.buf[base:base + (x1 - x0) * 3] = row

    def hline(self, x, y, w, color, thick=1):
        self.rect(x, y, w, thick, color)

    def border(self, x, y, w, h, color, thick=1):
        self.rect(x, y, w, thick, color)
        self.rect(x, y + h - thick, w, thick, color)
        self.rect(x, y, thick, h, color)
        self.rect(x + w - thick, y, thick, h, color)


# ---------------------------------------------------------------- text

def _glyph(font, ch):
    g = font["glyphs"].get(ch)
    if g is None:
        g = font["glyphs"]["?"]
    return g


def text_width(font, text):
    return sum(_glyph(font, ch)[0] for ch in text)


def draw_text(cv, font, x, y, text, color):
    """Draw text with (x, y) the top-left of the anchor line."""
    cx = x
    for ch in text:
        adv, left, top, w, h, b64 = _glyph(font, ch)
        if w and h:
            raw = base64.b64decode(b64)
            rb = (w + 7) // 8
            for yy in range(h):
                for xx in range(w):
                    if raw[yy * rb + xx // 8] & (1 << (7 - xx % 8)):
                        cv.px(cx + left + xx, y + top + yy, color)
        cx += adv
    return cx


def draw_centred(cv, font, cx, y, text, color):
    draw_text(cv, font, cx - text_width(font, text) // 2, y, text, color)


def wrap(font, text, max_w):
    """Greedy word wrap; returns a list of lines."""
    lines, cur = [], ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if text_width(font, trial) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_block(cv, font, x, y, text, max_w, color, leading=None, max_lines=None):
    """Draw wrapped text; returns the y just below the last line."""
    if leading is None:
        leading = font["ascent"] + font["descent"] + 3
    lines = wrap(font, text, max_w)
    if max_lines is not None:
        lines = lines[:max_lines]
    for line in lines:
        draw_text(cv, font, x, y, line, color)
        y += leading
    return y


# ---------------------------------------------------------------- png

def encode_png(cv):
    raw = bytearray()
    stride = W * 3
    for y in range(H):
        raw.append(0)
        raw += cv.buf[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", comp) + chunk(b"IEND", b""))


# ---------------------------------------------------------------- content

F_SERIF54 = FONTS["serif_bold_54"]
F_SERIF22 = FONTS["serif_bold_22"]
F_SB16 = FONTS["sans_bold_16"]
F_SB15 = FONTS["sans_bold_15"]
F_S14 = FONTS["sans_14"]
F_S13 = FONTS["sans_13"]
F_S11 = FONTS["sans_11"]

LEADS = [
    ("THE SUMMIT",
     "Trump, Xi and Putin meet - and declare peace",
     "The first trilateral summit of the US, Chinese and Russian leaders "
     "ends with a 'peace declaration' - but no breakthrough."),
    ("THE VERDICT",
     "World Court: Myanmar committed genocide",
     "The Court rules Myanmar committed genocide against the Rohingya in "
     "2017. The verdict cannot be appealed."),
]

REGIONS = [
    ("NORTH AMERICA", BLUE,
     "US auctions deep-sea mining leases off Samoa",
     "Two leases covering nearly 32m acres fetch $6m - a US deep-sea "
     "first in 60 years.",
     ["Senate rejects Iran war-powers resolution, 51-48",
      "Trump posthumously pardons baseball legend Pete Rose",
      "Judge halts work on Trump's triumphal arch for two weeks"]),
    ("SOUTH AMERICA", GREEN,
     "US and Venezuela sign military deal",
     "Hegseth visits Caracas as US-Venezuela military ties are "
     "restored.",
     ["Braskem talks race to avert $11bn court restructuring",
      "Brazil's Senate approves Lula's $10bn fiscal package",
      "Bukele expected to seek a third term",
      "Guadalajara cartel founder Felix Gallardo dies at 80"]),
    ("EUROPE", NAVY,
     "Kyiv hit as Russian missile strike sets building ablaze",
     "Debris hits the Obolonskyi district in the early hours; blasts "
     "heard across Kyiv.",
     ["Europe ready for talks with Russia on ending the war",
      "German auto and steel face 24-hour strikes on Friday",
      "EU-UK talks 'going down to the wire', No 10 says",
      "Van Gogh sells for a record $190.4m"]),
    ("MIDDLE EAST", RED,
     "Israel completes Gaza ground operation",
     "The military says its operation beyond the Yellow Line is "
     "complete.",
     ["Iran widens attacks on Gulf, tankers",
      "Riyadh skyscraper reported damaged in Houthi attack",
      "'Just fireworks': voices from besieged Taiz, Yemen",
      "Saudis brace for Yemen campaign to run into 2027"]),
    ("AFRICA", ORANGE,
     "Ethiopia and Eritrea mass troops on the border",
     "Troops mass near Badme after reported clashes; war fears grow, "
     "monitors say.",
     ["Dozens missing as migrant boat sinks off Senegal",
      "US group wins Kenya's Mrima Hill mine over China",
      "Medieval cathedral unearthed in Sudan - bigger than the White House",
      "Africa demands more climate cash"]),
    ("ASIA-PACIFIC", TEAL,
     "Takaichi: Japan's Taiwan stance unchanged since 1972",
     "Chilly APEC reception for Japan's PM; no Xi meeting as the freeze "
     "drags on.",
     ["Takaichi holds first talks with Putin since 2022",
      "APEC adopts Shenzhen Outlook on trade, data and AI",
      "Cumin sodas take on cola giants in India"]),
]

BAND_HEADLINES = [
    "Anthropic's record IPO: $81.3bn raised; shares close up 17%",
    "Pancreatic cancer pill sees tumours vanish in trial",
    "California probes whether China got Nvidia AI chips",
    "F1 Las Vegas: qualifying on Friday, titles already decided",
    "Nike returns to Formula 1 as apparel partner from 2027",
]

CLIMATE_LINE = ("COP31, ANTALYA - FINAL DAY: DRAFT DEAL DROPS ANY "
                 "MENTION OF FOSSIL FUELS")

FOOTER_L = ("SOURCES: REUTERS - BBC - AP - CNN - WALL STREET JOURNAL - "
            "LE MONDE - UN NEWS - SKY SPORTS")
FOOTER_R = "35 STORIES - RENDERED 20 NOV 2026"


# ---------------------------------------------------------------- render

def render():
    cv = Canvas()

    # Masthead.
    cv.hline(MARGIN, 24, CW, INK, 1)
    draw_centred(cv, F_SERIF54, W // 2, 36, "ONE DAY ON EARTH", INK)
    draw_centred(cv, F_SB16, W // 2, 100,
                 "FRIDAY, 20 NOVEMBER 2026 - 35 STORIES FROM 7 REGIONS", INK)
    cv.hline(MARGIN, 126, CW, INK, 3)
    cv.hline(MARGIN, 131, CW, INK, 1)

    # Lead strip: two boxes.
    lead_y, lead_h, lead_w = 144, 124, (CW - 8) // 2
    for i, (kicker, head, deck) in enumerate(LEADS):
        x = MARGIN + i * (lead_w + 8)
        cv.border(x, lead_y, lead_w, lead_h, INK, 1)
        draw_text(cv, F_SB15, x + 12, lead_y + 10, kicker, RED)
        y = draw_block(cv, F_SERIF22, x + 12, lead_y + 34, head,
                       lead_w - 24, INK, leading=26, max_lines=2)
        draw_block(cv, F_S14, x + 12, y + 4, deck, lead_w - 24, INK,
                   leading=18, max_lines=2)

    # Region grid: 3 columns x 2 rows.
    col_w = (CW - 2 * 13) // 3  # 314
    row_y = [280, 568]
    row_h = 276
    for idx, (label, color, head, deck, shorts) in enumerate(REGIONS):
        col, row = idx % 3, idx // 3
        x = MARGIN + col * (col_w + 13)
        y = row_y[row]
        cv.border(x, y, col_w, row_h, INK, 1)
        cv.rect(x + 1, y + 1, col_w - 2, 28, color)
        draw_text(cv, F_SB15, x + 10, y + 8, label, WHITE)
        inner = x + 10
        iw = col_w - 20
        yy = draw_block(cv, F_SB16, inner, y + 40, head, iw, INK,
                        leading=20, max_lines=2)
        yy = draw_block(cv, F_S13, inner, yy + 4, deck, iw, INK,
                        leading=17, max_lines=3)
        yy += 6
        cv.hline(inner, yy, iw, GREY, 1)
        yy += 8
        for s in shorts:
            draw_text(cv, F_S13, inner, yy, "\u2022", INK)
            yy = draw_block(cv, F_S13, inner + 12, yy, s, iw - 12, INK,
                            leading=17, max_lines=2)
            yy += 5

    # Tech / Science / Sport band.
    bx, by, bw, bh = MARGIN, 856, CW, 116
    cv.rect(bx, by, bw, bh, INK)
    draw_text(cv, F_SB15, bx + 12, by + 10, "TECH, SCIENCE & SPORT", RED_LT)
    col2_w = (bw - 24 - 20) // 2
    y1 = by + 32
    y2 = by + 32
    for i, hl in enumerate(BAND_HEADLINES):
        if i < 3:
            y1 = draw_block(cv, F_S14, bx + 12, y1, hl, col2_w, WHITE,
                            leading=18, max_lines=1)
            y1 += 2
        else:
            y2 = draw_block(cv, F_S14, bx + 12 + col2_w + 20, y2, hl,
                            col2_w, WHITE, leading=18, max_lines=1)
            y2 += 2
    cv.hline(bx + 12, by + bh - 26, bw - 24, (90, 90, 90), 1)
    draw_text(cv, F_SB15, bx + 12, by + bh - 20, CLIMATE_LINE, (232, 200, 120))

    # Footer.
    draw_text(cv, F_S11, MARGIN, 988, FOOTER_L, GREY)
    draw_text(cv, F_S11, W - MARGIN - text_width(F_S11, FOOTER_R), 988,
              FOOTER_R, GREY)

    return encode_png(cv)


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    data = render()
    with open(os.path.join(outdir, "entry.png"), "wb") as f:
        f.write(data)
    print("wrote", os.path.join(outdir, "entry.png"), len(data), "bytes")


if __name__ == "__main__":
    main()
