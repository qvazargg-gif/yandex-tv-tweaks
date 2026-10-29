# Генератор обоев (Python 3 + Pillow + numpy): python generate-synthwave-wallpapers.py
"""Procedural 'gamer' wallpapers, 1920x1080: synthwave, neon city, space, pixel art, outrun road."""
import math
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

W, H = 1920, 1080
OUT = "synthwave-wallpapers"


def hexc(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def vgrad(w, h, stops):
    """Vertical gradient from list of (pos 0..1, (r,g,b))."""
    ys = np.linspace(0, 1, h)
    out = np.zeros((h, w, 3), np.float32)
    for c in range(3):
        xp = [p for p, _ in stops]
        fp = [col[c] for _, col in stops]
        out[:, :, c] = np.interp(ys, xp, fp)[:, None]
    return out


def to_img(a):
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")


def glow(base, layer, radius=18, strength=1.0):
    """Additively blend a blurred copy plus the sharp layer (neon look)."""
    blur = layer.filter(ImageFilter.GaussianBlur(radius))
    if strength != 1.0:
        blur = Image.eval(blur, lambda v: int(min(255, v * strength)))
    out = ImageChops.add(base, blur)
    out = ImageChops.add(out, layer)
    return out


def noise(w, h, seed, octaves=5, base=4):
    rng = np.random.default_rng(seed)
    acc = np.zeros((h, w), np.float32)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        cells = base * (2 ** o)
        small = rng.random((max(2, cells * h // w), cells)).astype(np.float32)
        img = Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        acc += np.asarray(img, np.float32) / 255 * amp
        total += amp
        amp *= 0.5
    return acc / total


def stars(img, rng, n, ymax, big=0.08):
    d = ImageDraw.Draw(img)
    for _ in range(n):
        x, y = rng.random() * W, rng.random() * ymax
        b = int(120 + rng.random() * 135)
        if rng.random() < big:
            r = 1.8 + rng.random() * 1.5
            d.ellipse([x - r, y - r, x + r, y + r], fill=(b, b, b))
        else:
            d.point((x, y), fill=(b, b, b))


# ---------------------------------------------------------------- synthwave sunset

def synthwave(name, pal, seed):
    rng = random.Random(seed)
    hz = int(H * 0.62)
    sky = vgrad(W, H, [(0, pal["top"]), (hz / H, pal["hz"]), (hz / H + 0.001, (6, 0, 14)), (1, (3, 0, 8))])
    img = to_img(sky)
    stars(img, rng, 400, hz * 0.8)

    # sun with stripes
    sun = Image.new("RGB", (W, H), 0)
    sr = int(H * 0.25)
    cx, cy = W // 2, hz - int(sr * 0.3)
    sg = vgrad(2 * sr, 2 * sr, [(0, pal["sun1"]), (1, pal["sun2"])])
    sunimg = to_img(sg)
    mask = Image.new("L", (2 * sr, 2 * sr), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([0, 0, 2 * sr - 1, 2 * sr - 1], fill=255)
    for k in range(8):
        y = int(sr * 0.45 + k * sr * 0.12)
        th = int(4 + k * 3.5)
        md.rectangle([0, y, 2 * sr, y + th], fill=0)
    sun.paste(sunimg, (cx - sr, cy - sr), mask)
    sun = sun.crop((0, 0, W, hz)).resize((W, hz))
    full = Image.new("RGB", (W, H), 0)
    full.paste(sun, (0, 0))
    img = glow(img, full, 60, 0.45)

    # mountains
    d = ImageDraw.Draw(img)
    lines = Image.new("RGB", (W, H), 0)
    ld = ImageDraw.Draw(lines)
    for side in (0, 1):
        pts = [(0 if side == 0 else W, hz)]
        n = 12
        for i in range(n + 1):
            f = i / n
            x = (f * W * 0.42) if side == 0 else (W - f * W * 0.42)
            edge = 1 - f
            hgt = H * (0.04 + 0.2 * edge) * (0.5 + 0.5 * rng.random())
            pts.append((x, hz - (hgt if i % 2 == 0 else hgt * 0.4)))
        pts.append((W * 0.42 if side == 0 else W * 0.58, hz))
        d.polygon(pts, fill=(8, 2, 20))
        ld.line(pts, fill=pal["line"], width=3)
    img = glow(img, lines, 10)

    # grid
    grid = Image.new("RGB", (W, H), 0)
    gd = ImageDraw.Draw(grid)
    depth = H - hz
    for k in range(1, 40):
        z = k * 0.55
        y = hz + depth * 0.6 / z
        if y > H:
            continue
        a = min(1.0, (y - hz) / depth * 3)
        c = tuple(int(v * a) for v in pal["grid"])
        gd.line([(0, y), (W, y)], fill=c, width=2)
    for i in range(-30, 31):
        gd.line([(cx + i * 6, hz), (cx + i * W * 0.09, H)], fill=pal["grid"], width=2)
    gd.line([(0, hz), (W, hz)], fill=pal["grid"], width=3)
    img = glow(img, grid, 8)
    img.save(f"{OUT}/{name}.jpg", quality=90)


# ---------------------------------------------------------------- neon city

def city(name, pal, seed):
    rng = random.Random(seed)
    water = int(H * 0.74)
    sky = vgrad(W, H, [(0, pal["top"]), (0.74, pal["hz"]), (1, pal["top"])])
    img = to_img(sky)
    stars(img, rng, 250, H * 0.45)

    # big neon ring / moon
    ring = Image.new("RGB", (W, H), 0)
    rd = ImageDraw.Draw(ring)
    mx, my, mr = int(W * (0.25 + 0.5 * rng.random())), int(H * 0.28), int(H * 0.16)
    rd.ellipse([mx - mr, my - mr, mx + mr, my + mr], outline=pal["moon"], width=6)
    img = glow(img, ring, 40)

    layers = [(0.42, (14, 6, 32), 0.25), (0.30, (9, 3, 22), 0.5), (0.18, (4, 1, 12), 0.9)]
    for top_frac, col, lit in layers:
        bimg = Image.new("RGB", (W, H), 0)
        lights = Image.new("RGB", (W, H), 0)
        bd, ldd = ImageDraw.Draw(img), ImageDraw.Draw(lights)
        x = -20
        while x < W:
            bw = rng.randint(50, 150)
            bh = H * top_frac * (0.45 + rng.random())
            y0 = water - bh
            bd.rectangle([x, y0, x + bw, water], fill=col)
            # windows
            for wy in range(int(y0) + 12, water - 8, 14):
                for wx in range(x + 8, x + bw - 8, 12):
                    if rng.random() < 0.18 * lit:
                        c = rng.choice(pal["windows"])
                        ldd.rectangle([wx, wy, wx + 5, wy + 7], fill=c)
            # neon roof edge
            if rng.random() < 0.35 * lit + 0.1:
                ldd.line([(x, y0), (x + bw, y0)], fill=rng.choice(pal["neon"]), width=3)
            if rng.random() < 0.15 * lit:  # antenna
                ax = x + bw // 2
                bd.line([(ax, y0), (ax, y0 - 40)], fill=col, width=3)
                ldd.ellipse([ax - 4, y0 - 46, ax + 4, y0 - 38], fill=(255, 40, 60))
            x += bw + rng.randint(0, 12)
        img = glow(img, lights, 6)

    # reflection in water
    top = img.crop((0, water - (H - water), W, water)).transpose(Image.FLIP_TOP_BOTTOM)
    arr = np.asarray(top, np.float32)
    rows = arr.shape[0]
    out = np.empty_like(arr)
    for r in range(rows):
        shift = int(math.sin(r * 0.35) * (2 + r * 0.05))
        out[r] = np.roll(arr[r], shift, axis=0) * (0.55 - 0.4 * r / rows)
    refl = to_img(out)
    img.paste(refl, (0, water))
    d = ImageDraw.Draw(img)
    d.line([(0, water), (W, water)], fill=tuple(v // 2 for v in pal["neon"][0]), width=2)
    img.save(f"{OUT}/{name}.jpg", quality=90)


# ---------------------------------------------------------------- space

def space(name, pal, seed):
    rng = random.Random(seed)
    n1 = noise(W, H, seed, 6, 3)
    n2 = noise(W, H, seed + 7, 6, 3)
    neb = np.zeros((H, W, 3), np.float32)
    a = np.clip((n1 - 0.45) * 3.0, 0, 1) ** 1.6
    b = np.clip((n2 - 0.5) * 3.0, 0, 1) ** 1.6
    for c in range(3):
        neb[:, :, c] = 6 + a * pal["c1"][c] * 0.8 + b * pal["c2"][c] * 0.7
    img = to_img(neb)
    stars(img, rng, 1600, H, big=0.03)
    # a few bright stars with glow
    bright = Image.new("RGB", (W, H), 0)
    bd = ImageDraw.Draw(bright)
    for _ in range(14):
        x, y = rng.random() * W, rng.random() * H
        bd.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 255, 255))
        bd.line([(x - 18, y), (x + 18, y)], fill=(200, 200, 255), width=1)
        bd.line([(x, y - 18), (x, y + 18)], fill=(200, 200, 255), width=1)
    img = glow(img, bright, 8)

    # planet with shading and ring
    pr = int(H * 0.3)
    px, py = int(W * (0.68 if seed % 2 else 0.3)), int(H * 0.58)
    yy, xx = np.mgrid[-pr:pr, -pr:pr].astype(np.float32)
    dist = np.sqrt(xx ** 2 + yy ** 2) / pr
    inside = dist < 1
    nz = np.sqrt(np.clip(1 - dist ** 2, 0, 1))
    light = np.clip((-xx / pr * 0.6 - yy / pr * 0.5 + nz * 0.6), 0, 1)
    bands = 0.75 + 0.25 * np.sin(yy / pr * 18 + noise(2 * pr, 2 * pr, seed + 3, 3, 3) * 6)
    planet = np.zeros((2 * pr, 2 * pr, 3), np.float32)
    for c in range(3):
        planet[:, :, c] = pal["planet"][c] * light * bands
    pim = to_img(planet)
    mask = Image.fromarray((inside * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5))
    # ring behind and in front
    ring = Image.new("RGB", (W, H), 0)
    rd = ImageDraw.Draw(ring)
    rx, ry = pr * 1.9, pr * 0.42
    for i in range(10):
        rr = 1 + i * 0.035
        c = tuple(int(v * (0.5 + 0.05 * i)) for v in pal["ring"])
        rd.ellipse([px - rx * rr, py - ry * rr, px + rx * rr, py + ry * rr], outline=c, width=3)
    ring = ring.rotate(-14, center=(px, py))
    img = ImageChops.add(img, ring)
    img.paste(pim, (px - pr, py - pr), mask)
    # front half of ring over the planet
    front = ring.copy()
    fm = Image.new("L", (W, H), 0)
    ImageDraw.Draw(fm).rectangle([0, py, W, H], fill=255)
    fm = fm.rotate(-14, center=(px, py))
    img = Image.composite(ImageChops.add(img, front), img, fm)
    # atmosphere glow
    atm = Image.new("RGB", (W, H), 0)
    ImageDraw.Draw(atm).ellipse([px - pr, py - pr, px + pr, py + pr], outline=pal["planet"], width=4)
    img = glow(img, atm, 25, 0.8)
    img.save(f"{OUT}/{name}.jpg", quality=90)


# ---------------------------------------------------------------- pixel art

def pixel(name, pal, seed):
    rng = random.Random(seed)
    w, h = 320, 180
    sky = vgrad(w, h, [(0, pal["sky"][0]), (0.55, pal["sky"][1]), (0.75, pal["sky"][2])])
    sky = (np.round(sky / 24) * 24)  # banded, like an old palette
    img = to_img(sky)
    d = ImageDraw.Draw(img)
    for _ in range(90):
        x, y = rng.randrange(w), rng.randrange(int(h * 0.5))
        d.point((x, y), fill=(255, 255, 230) if rng.random() < 0.7 else (180, 200, 255))
    mx, my = rng.randrange(60, 260), rng.randrange(20, 50)
    d.ellipse([mx - 13, my - 13, mx + 13, my + 13], fill=pal["moon"])
    d.ellipse([mx - 5, my - 6, mx, my - 1], fill=tuple(int(v * 0.85) for v in pal["moon"]))
    d.ellipse([mx + 3, my + 2, mx + 7, my + 6], fill=tuple(int(v * 0.85) for v in pal["moon"]))
    for li, (col, base, amp) in enumerate(pal["layers"]):
        ph = [rng.random() * 6 for _ in range(4)]
        pts = [(0, h)]
        for x in range(0, w + 1, 2):
            y = base * h
            y -= amp * h * (0.5 * math.sin(x * 0.02 + ph[0]) + 0.3 * math.sin(x * 0.051 + ph[1])
                            + 0.2 * math.sin(x * 0.13 + ph[2]))
            pts.append((x, int(y)))
        pts.append((w, h))
        d.polygon(pts, fill=col)
        # pine trees on the nearest layers
        if li >= len(pal["layers"]) - 2:
            for _ in range(28):
                tx = rng.randrange(w)
                ty = int(base * h + 6)
                th = rng.randrange(8, 16)
                for k in range(th):
                    half = (k * 5) // th
                    d.line([(tx - half, ty - th + k), (tx + half, ty - th + k)], fill=col)
    # lake + glow strip
    lake_y = int(h * 0.86)
    d.rectangle([0, lake_y, w, h], fill=pal["sky"][0])
    for y in range(lake_y + 2, h, 3):
        x = rng.randrange(w)
        d.line([(x, y), (x + rng.randrange(6, 20), y)], fill=pal["sky"][2])
    big = img.resize((W, H), Image.NEAREST)
    big.save(f"{OUT}/{name}.jpg", quality=92)


# ---------------------------------------------------------------- outrun road

def outrun(name, pal, seed):
    rng = random.Random(seed)
    hz = int(H * 0.56)
    img = to_img(vgrad(W, H, [(0, pal["top"]), (hz / H, pal["hz"]), (hz / H + 0.001, (10, 4, 18)), (1, (2, 0, 6))]))
    stars(img, rng, 350, hz * 0.7)
    # sun
    sunl = Image.new("RGB", (W, H), 0)
    sr = int(H * 0.2)
    cx = W // 2
    sd = ImageDraw.Draw(sunl)
    sd.ellipse([cx - sr, hz - sr * 1.4, cx + sr, hz + sr * 0.6], fill=pal["sun"])
    sunl = sunl.crop((0, 0, W, hz))
    full = Image.new("RGB", (W, H), 0)
    full.paste(sunl, (0, 0))
    img = glow(img, full, 70, 0.5)
    d = ImageDraw.Draw(img)
    # hills
    for side in (-1, 1):
        pts = [(cx + side * W * 0.12, hz)]
        for i in range(10):
            x = cx + side * (W * 0.12 + i * W * 0.045)
            pts.append((x, hz - H * 0.03 - H * 0.08 * (i / 9) * (0.6 + 0.4 * rng.random())))
        pts.append((cx + side * W * 0.6, hz))
        d.polygon(pts, fill=(12, 3, 26))
    # road
    road = [(cx - 6, hz), (cx + 6, hz), (cx + W * 0.42, H), (cx - W * 0.42, H)]
    d.polygon(road, fill=(14, 6, 24))
    neon = Image.new("RGB", (W, H), 0)
    nd = ImageDraw.Draw(neon)
    nd.line([road[0], road[3]], fill=pal["edge"], width=4)
    nd.line([road[1], road[2]], fill=pal["edge"], width=4)
    depth = H - hz
    for k in range(1, 26):
        z0, z1 = k * 0.9, k * 0.9 + 0.45
        y0, y1 = hz + depth * 0.5 / z0, hz + depth * 0.5 / z1
        if y0 > H:
            continue
        wd0 = (y0 - hz) / depth * 22 + 1.5
        nd.polygon([(cx - wd0, y0), (cx + wd0, y0), (cx + wd0 * 0.8, y1), (cx - wd0 * 0.8, y1)], fill=pal["dash"])
    # side poles with lights
    for k in range(1, 14):
        z = k * 1.3
        y = hz + depth * 0.5 / z
        if y > H:
            continue
        s = (y - hz) / depth
        for side in (-1, 1):
            x = cx + side * (W * 0.45 * s + 20)
            ph = 160 * s + 6
            nd.line([(x, y), (x, y - ph)], fill=tuple(v // 3 for v in pal["edge"]), width=max(1, int(4 * s)))
            r = 4 + 12 * s
            nd.ellipse([x - r, y - ph - r, x + r, y - ph + r], fill=pal["lamp"])
    img = glow(img, neon, 12)
    img.save(f"{OUT}/{name}.jpg", quality=90)


if __name__ == "__main__":
    import os
    os.makedirs(OUT, exist_ok=True)
    synthwave("01", dict(top=hexc("0b0221"), hz=hexc("b5179e"), sun1=hexc("ffe45e"), sun2=hexc("ff2e88"),
                         line=hexc("22e4ff"), grid=hexc("ff2bd6")), 1)
    city("02", dict(top=hexc("05020f"), hz=hexc("3a0d5c"), moon=hexc("ff2bd6"),
                    windows=[hexc("ffd25e"), hexc("22e4ff"), hexc("ff5ea8")],
                    neon=[hexc("22e4ff"), hexc("ff2bd6"), hexc("8aff5e")]), 2)
    space("03", dict(c1=hexc("6a2bff"), c2=hexc("ff2b8a"), planet=hexc("ffa86b"), ring=hexc("ffd9a8")), 3)
    outrun("04", dict(top=hexc("10021f"), hz=hexc("ff5a3a"), sun=hexc("ffcf4a"), edge=hexc("ff2bd6"),
                      dash=hexc("ffffff"), lamp=hexc("22e4ff")), 4)
    pixel("05", dict(sky=[hexc("140a2e"), hexc("4b1e6e"), hexc("d4577a")], moon=hexc("fff1c4"),
                     layers=[(hexc("3a1856"), 0.62, 0.12), (hexc("26103d"), 0.72, 0.08), (hexc("150826"), 0.82, 0.05)]), 5)
    synthwave("06", dict(top=hexc("02110b"), hz=hexc("3b0a6b"), sun1=hexc("b8ff3a"), sun2=hexc("9b2bff"),
                         line=hexc("b46bff"), grid=hexc("39ff88")), 6)
    city("07", dict(top=hexc("020812"), hz=hexc("0d3a5c"), moon=hexc("22e4ff"),
                    windows=[hexc("ffffff"), hexc("22e4ff"), hexc("ffb13a")],
                    neon=[hexc("ff2b5e"), hexc("22e4ff"), hexc("ffd23a")]), 7)
    space("08", dict(c1=hexc("1fa3ff"), c2=hexc("2bffc8"), planet=hexc("9ad0ff"), ring=hexc("c8e6ff")), 8)
    outrun("09", dict(top=hexc("01061a"), hz=hexc("2b5bff"), sun=hexc("ff2bd6"), edge=hexc("22e4ff"),
                      dash=hexc("ffe45e"), lamp=hexc("ff2bd6")), 9)
    pixel("10", dict(sky=[hexc("071a24"), hexc("1e5a6e"), hexc("f2a65a")], moon=hexc("ffe9a8"),
                     layers=[(hexc("1d3b4a"), 0.6, 0.13), (hexc("122a36"), 0.71, 0.09), (hexc("08161e"), 0.82, 0.05)]), 10)
    synthwave("11", dict(top=hexc("140208"), hz=hexc("8a1a05"), sun1=hexc("ffd23a"), sun2=hexc("ff3a3a"),
                         line=hexc("ffb13a"), grid=hexc("ff7a1a")), 11)
    city("12", dict(top=hexc("0a0205"), hz=hexc("5c0d1e"), moon=hexc("ff5a2a"),
                    windows=[hexc("ffd25e"), hexc("ff5ea8"), hexc("ffffff")],
                    neon=[hexc("ff2b5e"), hexc("ffb13a"), hexc("22e4ff")]), 12)
    print("ok")
