"""Draw the sample cover images and topic banners used by the seed data and the topic pages.

    uv run --with pillow python scripts/draw_sample_art.py

Everything is generated (gradients and simple shapes), so there are no photo licences to
track. Pillow is needed only here, hence `--with` rather than a project dependency. The
output is committed; rerun this only to change the art. The same seed gives the same image.
"""

import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

BACKEND = Path(__file__).resolve().parent.parent
COVERS = BACKEND / "app" / "seed_covers"
BANNERS = BACKEND.parent / "frontend" / "public" / "topics"

COVER_SIZE = (1600, 840)  # The usual 1.91:1 of link previews
BANNER_SIZE = (2000, 500)
VARIANTS = 3
# Drawn at twice the size and scaled down: Pillow's shapes have no anti-aliasing otherwise
SCALE = 2

# topic: (gradient start, gradient end, glow)
PALETTES = {
    "ai": ("#1e1b4b", "#6d28d9", "#a78bfa"),
    "genai": ("#500724", "#ea580c", "#fb7185"),
    "machine-learning": ("#042f2e", "#1d4ed8", "#5eead4"),
    "data-engineering": ("#022c22", "#0e7490", "#34d399"),
    "software-engineering": ("#020617", "#1e40af", "#60a5fa"),
    "cloud-devops": ("#082f49", "#4338ca", "#7dd3fc"),
    "web-development": ("#431407", "#be185d", "#fbbf24"),
    "security": ("#022c1a", "#115e59", "#4ade80"),
    "lifestyle": ("#451a03", "#ea580c", "#fde68a"),
    "travel": ("#0c4a6e", "#0284c7", "#bae6fd"),
    "food": ("#450a0a", "#b91c1c", "#fdba74"),
    "health-wellness": ("#042f2e", "#0f766e", "#a7f3d0"),
    "personal-finance": ("#1a2e05", "#4d7c0f", "#fde047"),
    "books": ("#3b0764", "#9f1239", "#fecdd3"),
}


def rgb(hex_color: str, alpha: int = 255) -> tuple[int, int, int, int]:
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alpha)


WHITE = "#ffffff"


def background(size, start, end, glow, rnd: random.Random) -> Image.Image:
    """A diagonal gradient with a few soft, blurred glows."""
    w, h = size
    # Half a left-to-right gradient plus half a top-to-bottom one runs corner to corner.
    # (Rotating a single gradient would leave hard-edged corners.)
    across = Image.linear_gradient("L").rotate(90).resize(size).point(lambda v: v // 2)
    down = Image.linear_gradient("L").resize(size).point(lambda v: v // 2)
    if rnd.random() < 0.5:
        across = ImageOps.mirror(across)
    if rnd.random() < 0.5:
        down = ImageOps.flip(down)
    mask = ImageChops.add(across, down)
    image = Image.composite(
        Image.new("RGBA", size, rgb(end)), Image.new("RGBA", size, rgb(start)), mask
    )
    glows = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(glows)
    for color, alpha in ((glow, 110), (end, 140), (glow, 70)):
        r = rnd.uniform(0.25, 0.45) * w
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        draw.ellipse((x - r, y - r * 0.7, x + r, y + r * 0.7), fill=rgb(color, alpha))
    glows = glows.filter(ImageFilter.GaussianBlur(w / 12))
    return Image.alpha_composite(image, glows)


# --- Motifs: each draws onto a transparent layer of the full (scaled-up) size ---


def neural_net(draw, w, h, glow, rnd):
    layers = rnd.randint(4, 5)
    xs = [w * (0.14 + 0.72 * i / (layers - 1)) for i in range(layers)]
    columns = []
    for x in xs:
        count = rnd.randint(3, 6)
        gap = h * 0.62 / max(count - 1, 1)
        top = h / 2 - gap * (count - 1) / 2
        columns.append([(x, top + gap * j) for j in range(count)])
    for left, right in zip(columns, columns[1:], strict=False):
        for a in left:
            for b in right:
                draw.line((a, b), fill=rgb(WHITE, rnd.randint(25, 70)), width=int(w / 700))
    r = w / 70
    for column in columns:
        for x, y in column:
            lit = rnd.random() < 0.35
            draw.ellipse((x - r, y - r, x + r, y + r), fill=rgb(glow if lit else WHITE, 235))
            draw.ellipse(
                (x - r * 1.8, y - r * 1.8, x + r * 1.8, y + r * 1.8),
                outline=rgb(WHITE, 60),
                width=int(w / 900),
            )


def sparkle(draw, x, y, r, color):
    """The four-pointed star from the Lumen logo."""
    k = r * 0.22
    points = [(x, y - r), (x + k, y - k), (x + r, y), (x + k, y + k)]
    points += [(x, y + r), (x - k, y + k), (x - r, y), (x - k, y - k)]
    draw.polygon(points, fill=color)


def ribbons(draw, w, h, glow, rnd):
    phase, k = rnd.uniform(0, math.tau), rnd.uniform(1.6, 2.6)
    for i in range(14):
        points = []
        for step in range(121):
            t = step / 120
            y = h * (0.5 + 0.22 * math.sin(k * math.tau * t / 2 + phase + i * 0.18))
            y += h * 0.05 * math.sin(math.tau * t * 3 + i * 0.4) + (i - 7) * h * 0.018
            points.append((w * t, y))
        color = glow if i % 4 == 0 else WHITE
        draw.line(points, fill=rgb(color, 40 + i * 9), width=int(w / 400), joint="curve")
    for _ in range(5):
        x, y = rnd.uniform(0.1, 0.9) * w, rnd.uniform(0.12, 0.88) * h
        sparkle(draw, x, y, rnd.uniform(0.015, 0.035) * w, rgb(WHITE, 220))


def scatter(draw, w, h, glow, rnd):
    slope, bend = rnd.uniform(-0.3, 0.3), rnd.uniform(0.08, 0.16)

    def boundary(x: float) -> float:
        t = x / w - 0.5
        return h * (0.5 + slope * t + bend * math.sin(t * math.pi * 2))

    r = w / 230
    for _ in range(170):
        x = rnd.uniform(0.05, 0.95) * w
        above = rnd.random() < 0.5
        offset = abs(rnd.gauss(0, 0.16)) * h + h * 0.03
        y = boundary(x) + (-offset if above else offset)
        if not 0.04 * h < y < 0.96 * h:
            continue
        color = rgb(glow, 230) if above else rgb(WHITE, 190)
        draw.ellipse((x - r, y - r, x + r, y + r), fill=color)
    curve = [(x, boundary(x)) for x in range(0, w + 1, w // 120)]
    draw.line(curve, fill=rgb(WHITE, 230), width=int(w / 260), joint="curve")


def curve(a, b, steps=40):
    """An S-shaped path from a to b, like the edges in a pipeline diagram."""
    (x0, y0), (x1, y1) = a, b
    points = []
    for i in range(steps + 1):
        t = i / steps
        s = t * t * (3 - 2 * t)
        points.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * s))
    return points


def pipeline(draw, w, h, glow, rnd):
    columns = [rnd.randint(1, 2), rnd.randint(2, 3), rnd.randint(1, 3), 1]
    bw, bh = w * 0.13, h * 0.13
    boxes = []
    for i, count in enumerate(columns):
        x = w * (0.08 + 0.26 * i)
        gap = h * 0.26
        top = h / 2 - gap * (count - 1) / 2
        boxes.append([(x, top + gap * j) for j in range(count)])
    for left, right in zip(boxes, boxes[1:], strict=False):
        for x0, y0 in left:
            for x1, y1 in right:
                path = curve((x0 + bw, y0), (x1, y1))
                draw.line(path, fill=rgb(WHITE, 110), width=int(w / 450), joint="curve")
                for t in (0.3, 0.65):
                    px, py = path[int(t * (len(path) - 1))]
                    d = w / 260
                    draw.ellipse((px - d, py - d, px + d, py + d), fill=rgb(glow, 255))
    for column in boxes:
        for x, y in column:
            draw.rounded_rectangle(
                (x, y - bh / 2, x + bw, y + bh / 2),
                radius=bh / 4,
                fill=rgb("#0b1220", 170),
                outline=rgb(glow, 230),
                width=int(w / 500),
            )
            for row in range(3):
                ly = y - bh / 4 + row * bh / 4
                length = bw * rnd.uniform(0.35, 0.7)
                draw.line(
                    (x + bw * 0.14, ly, x + bw * 0.14 + length, ly),
                    fill=rgb(WHITE, 150 if row == 0 else 80),
                    width=int(h / 110),
                )


def window(draw, box, w, rnd, fill="#0b1220", alpha=200):
    """A rounded app window with the three dots in its title bar. Returns the content box."""
    x0, y0, x1, y1 = box
    bar = (y1 - y0) * 0.1
    draw.rounded_rectangle(box, radius=w / 90, fill=rgb(fill, alpha), outline=rgb(WHITE, 60))
    for i, color in enumerate(("#f87171", "#fbbf24", "#4ade80")):
        cx, cy, d = x0 + bar * (0.9 + i * 0.75), y0 + bar * 0.6, bar * 0.2
        draw.ellipse((cx - d, cy - d, cx + d, cy + d), fill=rgb(color, 230))
    return x0, y0 + bar * 1.3, x1, y1


def code_editor(draw, w, h, glow, rnd):
    x0, y0 = w * rnd.uniform(0.12, 0.22), h * 0.14
    left, top, right, bottom = window(draw, (x0, y0, x0 + w * 0.62, h * 0.86), w, rnd)
    colors = [glow, WHITE, "#f472b6", "#fbbf24", "#a78bfa"]
    indent, y, line_h = 0, top + h * 0.03, h * 0.052
    while y < bottom - line_h:
        x = left + w * 0.035 + indent * w * 0.03
        for _ in range(rnd.randint(1, 3)):
            length = w * rnd.uniform(0.03, 0.12)
            if x + length > right - w * 0.03:
                break
            draw.rounded_rectangle(
                (x, y, x + length, y + h * 0.018),
                radius=h / 100,
                fill=rgb(rnd.choice(colors), 200),
            )
            x += length + w * 0.012
        indent = max(0, min(3, indent + rnd.choice([-1, 0, 0, 1])))
        y += line_h


def cloud(draw, cx, cy, s, color):
    for dx, dy, r in ((-0.55, 0.1, 0.42), (0, -0.15, 0.58), (0.55, 0.08, 0.45), (0, 0.2, 0.45)):
        draw.ellipse(
            (cx + dx * s - r * s, cy + dy * s - r * s, cx + dx * s + r * s, cy + dy * s + r * s),
            fill=color,
        )


def infrastructure(draw, w, h, glow, rnd):
    cx, cy = w * rnd.uniform(0.35, 0.65), h * 0.3
    cloud(draw, cx, cy, w * 0.12, rgb(WHITE, 60))
    cloud(draw, w * rnd.uniform(0.1, 0.25), h * 0.2, w * 0.05, rgb(WHITE, 35))
    cloud(draw, w * rnd.uniform(0.78, 0.9), h * 0.28, w * 0.06, rgb(WHITE, 35))
    size, gap = w * 0.055, w * 0.02
    cols = 7
    start = w / 2 - (cols * size + (cols - 1) * gap) / 2
    for row in range(2):
        for col in range(cols):
            x, y = start + col * (size + gap), h * 0.6 + row * (size + gap)
            lit = rnd.random() < 0.45
            if row == 0:
                draw.line((x + size / 2, y, cx, cy + w * 0.07), fill=rgb(WHITE, 45), width=2)
            draw.rounded_rectangle(
                (x, y, x + size, y + size),
                radius=size / 6,
                fill=rgb(glow if lit else "#0b1220", 210 if lit else 150),
                outline=rgb(WHITE, 90),
                width=int(w / 800),
            )


def browsers(draw, w, h, glow, rnd):
    for i in range(3):
        x0 = w * (0.1 + i * 0.16 + rnd.uniform(-0.03, 0.03))
        y0 = h * (0.12 + i * 0.1)
        box = (x0, y0, x0 + w * 0.5, y0 + h * 0.62)
        left, top, right, bottom = window(draw, box, w, rnd, alpha=150 + i * 35)
        pad = w * 0.02
        draw.rounded_rectangle(
            (left + pad, top + pad * 0.5, right - pad, top + (bottom - top) * 0.35),
            radius=w / 150,
            fill=rgb(glow, 90 + i * 50),
        )
        cards = 3
        cw = (right - left - pad * (cards + 1)) / cards
        for c in range(cards):
            x = left + pad + c * (cw + pad)
            draw.rounded_rectangle(
                (x, top + (bottom - top) * 0.45, x + cw, bottom - pad),
                radius=w / 200,
                fill=rgb(WHITE, 30 + i * 20),
            )


def hexagon(cx, cy, r):
    return [
        (cx + r * math.cos(math.pi / 3 * k), cy + r * math.sin(math.pi / 3 * k)) for k in range(6)
    ]


def shield(draw, w, h, glow, rnd):
    r = w * 0.035
    for row in range(-1, int(h / (r * 1.5)) + 2):
        for col in range(-1, int(w / (r * 1.75)) + 2):
            cx = col * r * 1.75 + (r * 0.87 if row % 2 else 0)
            cy = row * r * 1.5
            lit = rnd.random() < 0.08
            draw.polygon(
                hexagon(cx, cy, r * 0.92),
                fill=rgb(glow, 90) if lit else None,
                outline=rgb(WHITE, 40),
            )
    cx, cy, s = w * rnd.uniform(0.4, 0.6), h * 0.5, h * 0.36
    outline = [
        (cx, cy - s),
        (cx + s * 0.8, cy - s * 0.7),
        (cx + s * 0.72, cy + s * 0.15),
        (cx, cy + s),
        (cx - s * 0.72, cy + s * 0.15),
        (cx - s * 0.8, cy - s * 0.7),
    ]
    draw.polygon(outline, fill=rgb("#0b1220", 190), outline=rgb(glow, 255), width=int(w / 250))
    # A keyhole in the middle
    k = s * 0.16
    draw.ellipse((cx - k, cy - k * 1.6, cx + k, cy + k * 0.4), fill=rgb(glow, 255))
    draw.polygon(
        [
            (cx - k * 0.5, cy),
            (cx + k * 0.5, cy),
            (cx + k * 0.8, cy + k * 2.2),
            (cx - k * 0.8, cy + k * 2.2),
        ],
        fill=rgb(glow, 255),
    )


def hills(draw, w, h, glow, rnd):
    """A sun rising over rolling hills, with a few birds."""
    cx, cy, r = w * rnd.uniform(0.55, 0.72), h * 0.52, h * 0.24
    for k, alpha in ((2.2, 30), (1.6, 55)):
        draw.ellipse((cx - r * k, cy - r * k, cx + r * k, cy + r * k), fill=rgb(glow, alpha))
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=rgb(glow, 240))
    for i, (base, alpha) in enumerate(((0.62, 90), (0.72, 150), (0.84, 215))):
        phase, amp = rnd.uniform(0, math.tau), h * rnd.uniform(0.04, 0.08)
        top = [
            (x, h * base + amp * math.sin(x / w * math.tau * (1.2 + i * 0.3) + phase))
            for x in range(0, w + 1, w // 100)
        ]
        draw.polygon([*top, (w, h), (0, h)], fill=rgb("#1c0a02", alpha))
    for _ in range(4):
        x, y, s = (
            rnd.uniform(0.12, 0.45) * w,
            rnd.uniform(0.15, 0.4) * h,
            w * rnd.uniform(0.012, 0.02),
        )
        draw.line(
            [(x - s, y - s * 0.5), (x, y), (x + s, y - s * 0.5)],
            fill=rgb(WHITE, 200),
            width=int(w / 500),
            joint="curve",
        )


def mountains(draw, w, h, glow, rnd):
    """Layered peaks, a dotted flight path and map pins."""
    for layer, alpha in ((0, 70), (1, 130), (2, 210)):
        x = -w * 0.1
        points = [(x, h)]
        while x < w * 1.1:
            peak = h * rnd.uniform(0.3, 0.5) + layer * h * 0.1
            span = w * rnd.uniform(0.12, 0.22)
            points += [(x + span / 2, peak), (x + span, h * (0.75 + layer * 0.05))]
            x += span
        points.append((w * 1.1, h))
        draw.polygon(points, fill=rgb("#062538", alpha))
    start, end = (w * 0.12, h * 0.55), (w * 0.86, h * 0.2)
    lift = h * 0.28
    for i in range(0, 60, 2):
        t = i / 60
        x = start[0] + (end[0] - start[0]) * t
        y = start[1] + (end[1] - start[1]) * t - lift * math.sin(math.pi * t)
        d = w / 400
        draw.ellipse((x - d, y - d, x + d, y + d), fill=rgb(WHITE, 220))
    # A paper plane at the end of the path
    px, py, s = end[0], end[1], w * 0.03
    draw.polygon(
        [(px + s, py - s * 0.3), (px - s, py - s * 0.2), (px - s * 0.4, py + s * 0.5)],
        fill=rgb(WHITE, 240),
    )
    for x, y in (start, (w * rnd.uniform(0.35, 0.6), h * rnd.uniform(0.6, 0.7))):
        r = w * 0.018
        draw.ellipse((x - r, y - r * 2.4, x + r, y - r * 0.4), fill=rgb(glow, 255))
        draw.polygon(
            [(x - r * 0.8, y - r * 1.1), (x + r * 0.8, y - r * 1.1), (x, y)], fill=rgb(glow, 255)
        )
        draw.ellipse((x - r * 0.4, y - r * 1.8, x + r * 0.4, y - r), fill=rgb("#062538", 255))


def table(draw, w, h, glow, rnd):
    """A meal seen from above: a plate, a bowl, cutlery and steam."""
    cx, cy, r = w * 0.5, h * 0.52, h * 0.3
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=rgb(WHITE, 225))
    draw.ellipse(
        (cx - r * 0.72, cy - r * 0.72, cx + r * 0.72, cy + r * 0.72),
        outline=rgb("#000000", 25),
        width=int(w / 400),
    )
    for _ in range(7):
        a, d = rnd.uniform(0, math.tau), rnd.uniform(0, r * 0.45)
        x, y, s = cx + math.cos(a) * d, cy + math.sin(a) * d, r * rnd.uniform(0.1, 0.2)
        color = rnd.choice([glow, "#16a34a", "#dc2626", "#f59e0b"])
        draw.ellipse((x - s, y - s, x + s, y + s), fill=rgb(color, 235))
    # A fork on the left and a knife on the right
    fx, kx, top, bottom = cx - r * 1.35, cx + r * 1.35, cy - r * 0.9, cy + r * 0.9
    line = int(w / 180)
    draw.line((fx, cy - r * 0.35, fx, bottom), fill=rgb(WHITE, 200), width=line)
    for dx in (-1, 0, 1):
        draw.line(
            (fx + dx * line * 1.4, top, fx + dx * line * 1.4, cy - r * 0.3),
            fill=rgb(WHITE, 200),
            width=line // 2,
        )
    draw.rounded_rectangle(
        (kx - line, top, kx + line * 0.8, bottom), radius=line, fill=rgb(WHITE, 200)
    )
    bx, by, br = w * rnd.uniform(0.8, 0.86), h * 0.26, h * 0.13
    draw.ellipse((bx - br, by - br, bx + br, by + br), fill=rgb(glow, 220))
    draw.ellipse(
        (bx - br * 0.72, by - br * 0.72, bx + br * 0.72, by + br * 0.72), fill=rgb("#7c2d12", 200)
    )
    for i in range(3):
        x = cx - r * 0.3 + i * r * 0.3
        wisp = [
            (x + math.sin(t / 8 + i) * w * 0.01, cy - r - h * 0.02 - t * h * 0.006)
            for t in range(0, 26)
        ]
        draw.line(wisp, fill=rgb(WHITE, 90), width=int(w / 450), joint="curve")


def heartbeat(draw, w, h, glow, rnd):
    """Calm breathing rings behind a heartbeat line."""
    cx, cy = w * rnd.uniform(0.4, 0.6), h * 0.5
    for i in range(6, 0, -1):
        r = h * 0.08 * i
        draw.ellipse(
            (cx - r, cy - r, cx + r, cy + r),
            outline=rgb(glow, 25 + (6 - i) * 18),
            width=int(w / 600),
        )
    points, x = [], 0.0
    while x <= w:
        beat = (x / w * 3 + rnd.uniform(-0.02, 0.02)) % 1
        y = cy
        if 0.45 < beat < 0.5:
            y -= h * 0.28
        elif 0.5 <= beat < 0.55:
            y += h * 0.16
        elif 0.35 < beat < 0.42:
            y -= h * 0.05
        points.append((x, y))
        x += w / 240
    draw.line(points, fill=rgb(glow, 250), width=int(w / 230), joint="curve")
    for _ in range(5):
        x, y, s = (
            rnd.uniform(0.08, 0.92) * w,
            rnd.uniform(0.1, 0.9) * h,
            w * rnd.uniform(0.02, 0.035),
        )
        draw.ellipse((x - s, y - s * 0.45, x + s, y + s * 0.45), fill=rgb(WHITE, 60))
        draw.line((x - s, y, x + s, y), fill=rgb(WHITE, 110), width=int(w / 800))


def savings(draw, w, h, glow, rnd):
    """Bars climbing to the right, a trend line and stacks of coins."""
    bars, bw = 7, w * 0.06
    left = w * 0.1
    tops = []
    value = h * 0.22
    for i in range(bars):
        value += h * rnd.uniform(0.02, 0.07)
        x = left + i * bw * 1.5
        top = h * 0.85 - value
        tops.append((x + bw / 2, top))
        draw.rounded_rectangle(
            (x, top, x + bw, h * 0.85), radius=bw / 5, fill=rgb(WHITE, 60 + i * 18)
        )
    draw.line(tops, fill=rgb(glow, 255), width=int(w / 300), joint="curve")
    for x, y in tops:
        d = w / 150
        draw.ellipse((x - d, y - d, x + d, y + d), fill=rgb(glow, 255))
    for stack in range(3):
        x = w * (0.78 + stack * 0.07)
        for c in range(rnd.randint(3, 7)):
            y = h * 0.85 - c * h * 0.035
            r = w * 0.028
            draw.ellipse(
                (x - r, y - r * 0.35, x + r, y + r * 0.35),
                fill=rgb(glow, 235),
                outline=rgb("#713f12", 200),
                width=int(w / 800),
            )


def bookshelf(draw, w, h, glow, rnd):
    """A shelf of book spines, one leaning, and a lamp's glow."""
    shelf = h * 0.8
    draw.rounded_rectangle(
        (w * 0.06, shelf, w * 0.94, shelf + h * 0.03), radius=h / 100, fill=rgb(WHITE, 120)
    )
    x = w * 0.1
    colors = [glow, WHITE, "#fbbf24", "#a78bfa", "#fda4af", "#5eead4"]
    while x < w * 0.7:
        bw, bh = w * rnd.uniform(0.03, 0.055), h * rnd.uniform(0.38, 0.6)
        if rnd.random() < 0.12:
            x += w * 0.04
            continue
        color = rgb(rnd.choice(colors), rnd.randint(150, 230))
        draw.rounded_rectangle((x, shelf - bh, x + bw, shelf), radius=w / 400, fill=color)
        for band in (0.15, 0.8):
            y = shelf - bh * band
            draw.line(
                (x + bw * 0.2, y, x + bw * 0.8, y), fill=rgb("#000000", 60), width=int(h / 150)
            )
        x += bw + w * 0.006
    # One book leaning back against the end of the row
    lean = [
        (x + w * 0.12, shelf),
        (x + w * 0.165, shelf),
        (x + w * 0.04, shelf - h * 0.44),
        (x + w * 0.002, shelf - h * 0.41),
    ]
    draw.polygon(lean, fill=rgb(glow, 220))


MOTIFS = {
    "ai": neural_net,
    "genai": ribbons,
    "machine-learning": scatter,
    "data-engineering": pipeline,
    "software-engineering": code_editor,
    "cloud-devops": infrastructure,
    "web-development": browsers,
    "security": shield,
    "lifestyle": hills,
    "travel": mountains,
    "food": table,
    "health-wellness": heartbeat,
    "personal-finance": savings,
    "books": bookshelf,
}


def draw(topic: str, size: tuple[int, int], seed: int) -> Image.Image:
    rnd = random.Random(f"{topic}-{seed}")
    start, end, glow = PALETTES[topic]
    big = (size[0] * SCALE, size[1] * SCALE)
    image = background(big, start, end, glow, rnd)
    # The motifs are designed for the cover's shape. On a wider image (a banner) the motif
    # keeps that shape and sits on the right, leaving the left calm for the page's text
    cover_ratio = COVER_SIZE[0] / COVER_SIZE[1]
    motif = (min(big[0], round(big[1] * cover_ratio)), big[1])
    layer = Image.new("RGBA", motif, (0, 0, 0, 0))
    MOTIFS[topic](ImageDraw.Draw(layer), motif[0], motif[1], glow, rnd)
    if motif[0] < big[0]:
        # Fade the motif in from the left, so patterns that fill it (hexagons, lines) don't
        # end in a hard edge halfway across the banner
        fade = Image.linear_gradient("L").rotate(90).resize(motif).point(lambda v: min(255, v * 3))
        layer.putalpha(ImageChops.multiply(layer.getchannel("A"), fade))
    image.alpha_composite(layer, (big[0] - motif[0], 0))
    return image.resize(size, Image.Resampling.LANCZOS).convert("RGB")


def main() -> None:
    COVERS.mkdir(parents=True, exist_ok=True)
    BANNERS.mkdir(parents=True, exist_ok=True)
    for topic in PALETTES:
        for n in range(1, VARIANTS + 1):
            draw(topic, COVER_SIZE, n).save(COVERS / f"{topic}-{n}.webp", quality=82)
        # A banner is wide and short, so the motif sits in a strip; the page puts text on it
        draw(topic, BANNER_SIZE, 0).save(BANNERS / f"{topic}.webp", quality=80)
    print(f"Wrote {len(PALETTES) * VARIANTS} covers to {COVERS} and banners to {BANNERS}")


if __name__ == "__main__":
    main()
