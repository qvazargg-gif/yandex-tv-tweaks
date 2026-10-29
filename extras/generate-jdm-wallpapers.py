# Генератор обоев (Python 3 + Pillow + numpy): python generate-jdm-wallpapers.py
"""JDM / drift night wallpapers, 1920x1080. All procedural: generic coupe silhouette (no real model or logo)."""
import math
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageFont

W, H = 1920, 1080
OUT = "jdm-wallpapers"
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"  # нужен шрифт с японскими иероглифами (Noto Sans CJK); на Windows: C:/Windows/Fonts/msgothic.ttc
GROUND = int(H * 0.55)
CAR_Y = GROUND + 95  # where the tyres touch the road

SIGNS = ["峠", "走り屋", "ドリフト", "夜", "湾岸", "速", "東京", "ラーメン", "居酒屋", "カラオケ",
         "駐車場", "整備", "改造", "限界", "首都高", "深夜"]


def hexc(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def vgrad(w, h, stops):
    ys = np.linspace(0, 1, h)
    out = np.zeros((h, w, 3), np.float32)
    for c in range(3):
        out[:, :, c] = np.interp(ys, [p for p, _ in stops], [col[c] for _, col in stops])[:, None]
    return out


def to_img(a):
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")


def add_glow(base, layer, radius=16, strength=1.0, sharp=True):
    blur = layer.filter(ImageFilter.GaussianBlur(radius))
    if strength != 1.0:
        blur = Image.eval(blur, lambda v: int(min(255, v * strength)))
    out = ImageChops.add(base, blur)
    return ImageChops.add(out, layer) if sharp else out


def noise(w, h, seed, octaves=5, base=4):
    rng = np.random.default_rng(seed)
    acc = np.zeros((h, w), np.float32)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        cells = base * (2 ** o)
        small = rng.random((max(2, cells * h // max(w, 1)), cells)).astype(np.float32)
        img = Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        acc += np.asarray(img, np.float32) / 255 * amp
        total += amp
        amp *= 0.5
    return acc / total


def font(size):
    return ImageFont.truetype(FONT, size, index=0)


# ---------------------------------------------------------------- backgrounds

def sky(pal, rng):
    img = to_img(vgrad(W, H, [(0, pal["sky0"]), (GROUND / H, pal["sky1"]), (1, (0, 0, 0))]))
    d = ImageDraw.Draw(img)
    for _ in range(160):
        x, y = rng.random() * W, rng.random() * GROUND * 0.5
        b = rng.randint(90, 200)
        d.point((x, y), fill=(b, b, b))
    return img


def bg_city(img, pal, rng):
    lights = Image.new("RGB", (W, H), 0)
    ld = ImageDraw.Draw(lights)
    d = ImageDraw.Draw(img)
    for depth, (col, hmin, hmax, lit) in enumerate([((16, 8, 28), 0.30, 0.55, 0.2),
                                                     ((10, 5, 18), 0.22, 0.45, 0.5),
                                                     ((5, 2, 10), 0.15, 0.35, 1.0)]):
        x = -30
        while x < W:
            bw = rng.randint(70, 190)
            top = GROUND - H * (hmin + (hmax - hmin) * rng.random())
            d.rectangle([x, top, x + bw, GROUND], fill=col)
            for wy in range(int(top) + 14, GROUND - 10, 16):
                for wx in range(x + 8, x + bw - 8, 14):
                    if rng.random() < 0.12 * lit:
                        ld.rectangle([wx, wy, wx + 6, wy + 8], fill=rng.choice(pal["win"]))
            # vertical neon sign on the nearer buildings
            if depth >= 1 and rng.random() < 0.55:
                word = rng.choice(SIGNS)
                fs = rng.randint(30, 46) if depth == 2 else rng.randint(22, 32)
                sx = x + rng.randint(6, max(7, bw - fs - 10))
                sy = top + rng.randint(10, 40)
                c = rng.choice(pal["neon"])
                hgt = len(word) * (fs + 4) + 16
                if sy + hgt < GROUND - 10:
                    ld.rectangle([sx - 6, sy - 6, sx + fs + 6, sy + hgt], outline=c, width=3)
                    f = font(fs)
                    for i, ch in enumerate(word):
                        ld.text((sx, sy + 4 + i * (fs + 4)), ch, font=f, fill=c)
            x += bw + rng.randint(0, 14)
    return add_glow(img, lights, 10, 1.1)


def bg_touge(img, pal, rng):
    d = ImageDraw.Draw(img)
    # moon
    moon = Image.new("RGB", (W, H), 0)
    mx, my, mr = rng.randint(250, W - 250), rng.randint(110, 220), 70
    ImageDraw.Draw(moon).ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=pal["moon"])
    img = add_glow(img, moon, 60, 0.6)
    d = ImageDraw.Draw(img)
    # mountain layers
    for i, (col, base, amp) in enumerate([((22, 14, 40), 0.30, 0.16), ((14, 8, 26), 0.42, 0.13), ((7, 4, 14), 0.52, 0.10)]):
        ph = [rng.random() * 6 for _ in range(3)]
        pts = [(0, GROUND)]
        for x in range(0, W + 10, 10):
            y = H * base - H * amp * (0.55 * math.sin(x * 0.003 + ph[0]) + 0.3 * math.sin(x * 0.0087 + ph[1])
                                      + 0.15 * math.sin(x * 0.021 + ph[2]))
            pts.append((x, y))
        pts.append((W, GROUND))
        d.polygon(pts, fill=col)
    # far city glow in the valley
    lights = Image.new("RGB", (W, H), 0)
    ld = ImageDraw.Draw(lights)
    for _ in range(700):
        x = rng.random() * W
        y = GROUND - 20 - rng.random() * 60
        ld.point((x, y), fill=rng.choice(pal["win"]))
    img = add_glow(img, lights, 4, 1.4)
    d = ImageDraw.Draw(img)
    # guardrail with posts and road lamps
    rail = Image.new("RGB", (W, H), 0)
    rd = ImageDraw.Draw(rail)
    ry = GROUND - 26
    d.line([(0, ry), (W, ry)], fill=(40, 40, 52), width=6)
    for x in range(0, W, 60):
        d.line([(x, ry), (x, GROUND)], fill=(30, 30, 40), width=4)
    for x in range(rng.randint(80, 200), W, 520):
        d.line([(x, GROUND), (x, GROUND - 260)], fill=(25, 25, 34), width=6)
        d.line([(x, GROUND - 260), (x + 50, GROUND - 270)], fill=(25, 25, 34), width=5)
        rd.ellipse([x + 40, GROUND - 278, x + 64, GROUND - 266], fill=pal["lamp"])
    return add_glow(img, rail, 30, 0.9)


def bg_bridge(img, pal, rng):
    img = bg_city(img, dict(pal, neon=pal["neon"][:1]), rng) if rng.random() < 0.0 else img
    d = ImageDraw.Draw(img)
    # distant skyline
    lights = Image.new("RGB", (W, H), 0)
    ld = ImageDraw.Draw(lights)
    x = 0
    while x < W:
        bw = rng.randint(30, 90)
        top = GROUND - 90 - rng.random() * 160
        d.rectangle([x, top, x + bw, GROUND - 70], fill=(12, 8, 22))
        for _ in range(int(bw * 0.4)):
            ld.point((x + rng.random() * bw, top + rng.random() * (GROUND - 70 - top)), fill=rng.choice(pal["win"]))
        x += bw + rng.randint(2, 20)
    # suspension bridge: towers + catenary cables with lights
    tower_x = [int(W * 0.18), int(W * 0.72)]
    deck = GROUND - 70
    for tx in tower_x:
        d.rectangle([tx - 14, deck - 330, tx + 14, deck], fill=(20, 16, 34))
        ld.rectangle([tx - 3, deck - 335, tx + 3, deck - 325], fill=(255, 60, 60))
    cable = Image.new("RGB", (W, H), 0)
    cd = ImageDraw.Draw(cable)
    span = [(-W, tower_x[0]), (tower_x[0], tower_x[1]), (tower_x[1], 2 * W)]
    for a, b in span:
        pts = []
        for i in range(81):
            f = i / 80
            x = a + (b - a) * f
            sag = 1 - (2 * f - 1) ** 2
            y = deck - 330 + 300 * sag if (a, b) == span[1] else deck - 330 + 300 * (f if a < 0 else 1 - f) * 0.9
            pts.append((x, y))
        cd.line(pts, fill=pal["neon"][0], width=3)
        for x, y in pts[::4]:
            cd.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 245, 220))
    d.rectangle([0, deck, W, deck + 14], fill=(18, 14, 28))
    img = add_glow(img, lights, 3, 1.2)
    img = add_glow(img, cable, 12, 0.9)
    return img


# ---------------------------------------------------------------- the car

def arch(cx, r, steps=14):
    return [(cx + r * math.cos(math.pi - math.pi * i / steps), 0.06 + r * 0.9 * math.sin(math.pi * i / steps))
            for i in range(steps + 1)]


def car_layer(pal, length, rng, facing_right=True, angle=-4.0, wing=True):
    """Returns (body RGBA, light RGB layer, wheel-rear position) at size ~length x length*0.45."""
    S = int(length)
    cw, ch = S + 40, int(S * 0.45) + 40
    body = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    lights = Image.new("RGB", (cw, ch), 0)
    bd, ld = ImageDraw.Draw(body), ImageDraw.Draw(lights)

    def P(x, y):  # normalized -> canvas (x right, y up from ground)
        return (20 + x * S, ch - 20 - y * S)

    rear_c, front_c, wr = 0.18, 0.80, 0.078
    outline = [(0.0, 0.07), (0.0, 0.15), (0.015, 0.18), (0.13, 0.19), (0.22, 0.197), (0.33, 0.252),
               (0.42, 0.27), (0.50, 0.27), (0.57, 0.258), (0.66, 0.205), (0.80, 0.188), (0.93, 0.165),
               (0.995, 0.13), (1.0, 0.08), (0.99, 0.06)]
    bottom = [(front_c + wr * 1.15, 0.065)] + arch(front_c, wr * 1.15)[::-1][1:-1][::-1]
    bottom = [(front_c + wr * 1.15, 0.065)]
    bottom = [(front_c + wr * 1.2, 0.06)]
    bottom += [p for p in reversed(arch(front_c, wr * 1.2))]
    bottom += [(rear_c + wr * 1.2, 0.055)]
    bottom += [p for p in reversed(arch(rear_c, wr * 1.2))]
    poly = outline + bottom
    pts = [P(x, y) for x, y in poly]
    bd.polygon(pts, fill=pal["body"] + (255,))

    # window
    win = [P(0.335, 0.212), P(0.37, 0.25), P(0.495, 0.262), P(0.555, 0.253), P(0.62, 0.208)]
    bd.polygon(win, fill=(12, 16, 30, 255))
    bd.line([P(0.49, 0.262), P(0.475, 0.212)], fill=pal["body"] + (255,), width=max(2, S // 160))
    ld.line([P(0.27, 0.075), P(0.70, 0.075)], fill=tuple(v // 2 for v in pal["rim"]), width=2)
    # body line + rim light
    ld.line([P(0.05, 0.15), P(0.95, 0.15)], fill=tuple(v // 3 for v in pal["rim"]), width=2)
    ld.line([P(x, y) for x, y in outline], fill=pal["rim"], width=max(3, S // 170))
    ld.line(win[1:4], fill=tuple(int(v * 0.7) for v in pal["rim"]), width=2)
    if wing:
        for x0 in (0.05, 0.10):
            bd.line([P(x0, 0.185), P(x0 - 0.008, 0.235)], fill=pal["body"] + (255,), width=max(3, S // 120))
        bd.polygon([P(-0.012, 0.232), P(0.14, 0.24), P(0.14, 0.252), P(-0.016, 0.245)], fill=pal["body"] + (255,))
        ld.line([P(-0.016, 0.245), P(0.14, 0.252)], fill=pal["rim"], width=3)
    # lights
    ld.polygon([P(0.925, 0.158), P(0.985, 0.14), P(0.99, 0.125), P(0.93, 0.142)], fill=(255, 250, 235))
    ld.rectangle([P(0.003, 0.168), P(0.03, 0.148)], fill=(255, 30, 40))
    # wheels
    for cx in (rear_c, front_c):
        x, y = P(cx, 0.072)
        r = wr * S
        bd.ellipse([x - r, y - r, x + r, y + r], fill=(6, 6, 8, 255))
        rr = r * 0.62
        bd.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(30, 30, 36, 255))
        for k in range(5):
            a = k * 2 * math.pi / 5 + rng.random()
            bd.line([(x, y), (x + rr * math.cos(a), y + rr * math.sin(a))], fill=(70, 70, 80, 255), width=max(2, S // 200))
        ld.ellipse([x - rr, y - rr, x + rr, y + rr], outline=tuple(v // 2 for v in pal["rim"]), width=2)

    rear_pos = P(rear_c, 0.03)
    body = body.rotate(angle, resample=Image.BICUBIC, center=rear_pos)
    lights = lights.rotate(angle, resample=Image.BICUBIC, center=rear_pos)
    if not facing_right:
        body = body.transpose(Image.FLIP_LEFT_RIGHT)
        lights = lights.transpose(Image.FLIP_LEFT_RIGHT)
        rear_pos = (cw - rear_pos[0], rear_pos[1])
    return body, lights, rear_pos, (cw, ch)


def smoke(img, cx, cy, toward_left, pal, seed, scale=1.0):
    """Tire smoke billowing back from the rear wheel, lit by the scene's neon."""
    w, h = int(900 * scale), int(520 * scale)
    n = noise(w, h, seed, 6, 3)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    # origin at the right-bottom (rear wheel) and spreading left/up
    ox, oy = (w * 0.92, h * 0.86) if toward_left else (w * 0.08, h * 0.86)
    dx = (xx - ox) / w
    dy = (yy - oy) / h
    along = -dx if toward_left else dx
    spread = np.clip(along, 0, 1)
    width = 0.12 + 0.55 * spread
    fall = np.exp(-((dy + spread * 0.35) ** 2) / (2 * width ** 2)) * np.exp(-((along - 0.35) ** 2) / 0.18)
    fall *= (along > -0.04)
    ex = np.minimum(xx / (w * 0.18), (w - 1 - xx) / (w * 0.18))
    ey = np.minimum(yy / (h * 0.25), (h - 1 - yy) / (h * 0.12))
    edge = np.clip(np.minimum(ex, ey), 0, 1) ** 1.5
    dens = np.clip(fall * (0.75 + 1.1 * (n - 0.35)), 0, 1) ** 1.1 * edge
    c1, c2 = np.array(pal["smoke1"], np.float32), np.array(pal["smoke2"], np.float32)
    mix = np.clip(yy / h, 0, 1)[..., None]
    col = c1 * (1 - mix) + c2 * mix
    alpha = (dens * 245).astype(np.uint8)
    rgba = np.dstack([np.clip(col, 0, 255).astype(np.uint8), alpha])
    sm = Image.fromarray(rgba, "RGBA").filter(ImageFilter.GaussianBlur(3))
    px = int(cx - ox)
    py = int(cy - oy)
    img.alpha_composite(sm, (px, py)) if img.mode == "RGBA" else img.paste(sm, (px, py), sm)


# ---------------------------------------------------------------- ground, streaks, composition

def ground_and_reflection(img, pal):
    top = img.crop((0, GROUND - (H - GROUND), W, GROUND)).transpose(Image.FLIP_TOP_BOTTOM)
    top = top.filter(ImageFilter.GaussianBlur(4))
    arr = np.asarray(top, np.float32)
    rows = arr.shape[0]
    out = np.empty_like(arr)
    for r in range(rows):
        shift = int(math.sin(r * 0.25) * (1 + r * 0.04))
        out[r] = np.roll(arr[r], shift, axis=0) * (0.42 - 0.32 * r / rows)
    asphalt = vgrad(W, H - GROUND, [(0, (14, 12, 20)), (1, (4, 3, 8))])
    grain = np.random.default_rng(1).random((H - GROUND, W, 1)).astype(np.float32) * 10
    ground = to_img(out + asphalt + grain)
    img.paste(ground, (0, GROUND))
    d = ImageDraw.Draw(img)
    # road markings
    for x in range(-40, W, 260):
        d.polygon([(x, GROUND + 38), (x + 140, GROUND + 38), (x + 150, GROUND + 46), (x + 10, GROUND + 46)],
                  fill=(90, 88, 96))
    return img


def streaks(img, pal, rng, y0, y1, n=40):
    layer = Image.new("RGB", (W, H), 0)
    d = ImageDraw.Draw(layer)
    for _ in range(n):
        y = rng.uniform(y0, y1)
        x = rng.uniform(-300, W)
        ln = rng.uniform(200, 900)
        c = (255, 40, 50) if rng.random() < 0.6 else (255, 240, 220)
        d.line([(x, y), (x + ln, y + rng.uniform(-4, 4))], fill=c, width=rng.choice([2, 2, 3]))
    return add_glow(img, layer, 7, 1.0)


def scene(name, kind, pal, seed, facing_right=True, angle=-5, car_x=0.58, car_len=0.47):
    rng = random.Random(seed)
    img = sky(pal, rng)
    img = {"city": bg_city, "touge": bg_touge, "bridge": bg_bridge}[kind](img, pal, rng)
    if kind == "bridge":
        img = streaks(img, pal, rng, GROUND - 66, GROUND - 58, 28)
    img = ground_and_reflection(img, pal)
    img = img.convert("RGBA")

    length = W * car_len
    body, lights, rear, (cw, ch) = car_layer(pal, length, rng, facing_right, angle if facing_right else -angle)
    ox = int(W * car_x - cw / 2)
    oy = int(CAR_Y - ch + 20)
    # reflection of the car on wet asphalt
    refl = body.transpose(Image.FLIP_TOP_BOTTOM)
    ra = np.asarray(refl).copy()
    ra[..., 3] = (ra[..., 3] * 0.35).astype(np.uint8)
    img.alpha_composite(Image.fromarray(ra, "RGBA"), (ox, oy + ch - 40))
    # smoke behind, car, smoke in front
    sx, sy = ox + rear[0], oy + rear[1]
    smoke(img, sx, sy, facing_right, pal, seed, 1.6)
    img.alpha_composite(body, (ox, oy))
    rgb = img.convert("RGB")
    lfull = Image.new("RGB", (W, H), 0)
    lfull.paste(lights, (ox, oy))
    rgb = add_glow(rgb, lfull, 14, 1.0)
    # headlight beam
    beam = Image.new("RGB", (W, H), 0)
    bdd = ImageDraw.Draw(beam)
    hx = ox + (cw - 30 if facing_right else 30)
    hy = oy + ch - 20 - 0.16 * length
    far = W * 0.6 * (1 if facing_right else -1)
    bdd.polygon([(hx, hy), (hx + far, hy - 140), (hx + far, hy + 120)], fill=(70, 66, 52))
    rgb = ImageChops.add(rgb, beam.filter(ImageFilter.GaussianBlur(40)))
    rgba = rgb.convert("RGBA")
    smoke(rgba, sx + (40 if facing_right else -40), sy + 10, facing_right, pal, seed + 99, 0.9)
    out = rgba.convert("RGB")
    # light vignette
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = 1 - 0.45 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / 2
    out = to_img(np.asarray(out, np.float32) * v[..., None])
    out.save(f"{OUT}/{name}.jpg", quality=90)


PALS = {
    "pink": dict(sky0=hexc("07020f"), sky1=hexc("3a0d4e"), win=[hexc("ffd25e"), hexc("ff5ea8"), hexc("7fe6ff")],
                 neon=[hexc("ff2bd6"), hexc("22e4ff"), hexc("ff5a5a")], rim=hexc("ff4fd8"), body=(10, 8, 14),
                 smoke1=hexc("c9a6ff"), smoke2=hexc("ff7ad1"), moon=hexc("ffe7f5"), lamp=hexc("ffb35a")),
    "teal": dict(sky0=hexc("02080c"), sky1=hexc("0d3a4a"), win=[hexc("ffffff"), hexc("7fe6ff"), hexc("ffb13a")],
                 neon=[hexc("22e4ff"), hexc("ffb13a"), hexc("ff2b5e")], rim=hexc("3ae8ff"), body=(8, 10, 14),
                 smoke1=hexc("a8e8ff"), smoke2=hexc("ffc28a"), moon=hexc("e8fbff"), lamp=hexc("ffa040")),
    "red": dict(sky0=hexc("0a0204"), sky1=hexc("4a0a14"), win=[hexc("ffd25e"), hexc("ff6a3a"), hexc("ffffff")],
                neon=[hexc("ff2b3a"), hexc("ffb13a"), hexc("ff2bd6")], rim=hexc("ff3a3a"), body=(12, 8, 8),
                smoke1=hexc("ffb0a0"), smoke2=hexc("ff6a4a"), moon=hexc("fff0e0"), lamp=hexc("ff8a3a")),
    "green": dict(sky0=hexc("02060a"), sky1=hexc("123a2a"), win=[hexc("b8ff8a"), hexc("ffffff"), hexc("7fe6ff")],
                  neon=[hexc("39ff88"), hexc("22e4ff"), hexc("b46bff")], rim=hexc("39ff88"), body=(8, 12, 10),
                  smoke1=hexc("b8ffd8"), smoke2=hexc("9ad8ff"), moon=hexc("eaffef"), lamp=hexc("ffd25e")),
}

if __name__ == "__main__":
    import os, sys
    os.makedirs(OUT, exist_ok=True)
    jobs = [
        ("01", "city", "pink", 1, True, -2, 0.58),
        ("02", "touge", "teal", 2, False, -2, 0.45),
        ("03", "bridge", "red", 3, True, -2, 0.55),
        ("04", "city", "teal", 4, False, -2, 0.42),
        ("05", "touge", "pink", 5, True, -2, 0.6),
        ("06", "bridge", "green", 6, False, -2, 0.5),
        ("07", "city", "red", 7, True, -2, 0.62),
        ("08", "touge", "green", 8, False, -2, 0.4),
        ("09", "bridge", "pink", 9, True, -2, 0.55),
        ("10", "city", "green", 10, False, -2, 0.45),
        ("11", "touge", "red", 11, True, -2, 0.58),
        ("12", "bridge", "teal", 12, False, -2, 0.5),
    ]
    only = sys.argv[1:]
    for name, kind, pal, seed, fr, ang, cx in jobs:
        if only and name not in only:
            continue
        scene(name, kind, PALS[pal], seed, fr, ang, cx)
    print("ok")
