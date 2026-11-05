"""Log-frequency spectrograms with bar lines, plus click detection, for checking stems by eye."""
import sys, os, numpy as np
from PIL import Image, ImageDraw
from scipy.signal import stft
from lib import load, SR

BARS = [0.8 + 2.4 * i for i in range(11)]


def spec_img(x, w=1500, h=220, fmin=25, fmax=20000, t0=0, t1=None):
    m = x.mean(1)
    if t1 is None: t1 = len(m) / SR
    m = m[int(t0 * SR):int(t1 * SR)]
    f, t, Z = stft(m, SR, nperseg=4096, noverlap=4096 - 256)
    A = 20 * np.log10(np.abs(Z) + 1e-9)
    ys = np.geomspace(fmin, fmax, h)
    idx = np.clip(np.searchsorted(f, ys), 0, len(f) - 1)
    A = A[idx][::-1]
    xs = np.linspace(0, A.shape[1] - 1, w).astype(int)
    A = A[:, xs]
    top = A.max()
    img = np.clip((A - (top - 90)) / 90, 0, 1)
    rgb = np.stack([img ** 0.7 * 255, img ** 1.6 * 230, (1 - img) * img * 3 * 140], -1).astype(np.uint8)
    im = Image.fromarray(rgb)
    d = ImageDraw.Draw(im)
    for b in BARS:
        if t0 <= b <= t1:
            X = int((b - t0) / (t1 - t0) * w); d.line([(X, 0), (X, h)], fill=(80, 160, 255))
    for fr in [100, 1000, 10000]:
        Y = int(h - 1 - np.log(fr / fmin) / np.log(fmax / fmin) * (h - 1)); d.line([(0, Y), (8, Y)], fill='white'); d.text((10, Y - 6), str(fr), fill='white')
    return im


def level_img(x, w=1500, h=70, t0=0, t1=None):
    m = np.abs(x).max(1)
    if t1 is None: t1 = len(m) / SR
    m = m[int(t0 * SR):int(t1 * SR)]
    hop = max(1, len(m) // w)
    pk = np.array([m[i * hop:(i + 1) * hop].max() if (i + 1) * hop <= len(m) else 0 for i in range(w)])
    db = 20 * np.log10(pk + 1e-9)
    im = Image.new('RGB', (w, h), (20, 20, 20)); d = ImageDraw.Draw(im)
    for i, v in enumerate(db):
        y = int(np.clip((-v) / 48 * h, 0, h)); d.line([(i, h), (i, y)], fill=(200, 200, 90) if v < -1 else (255, 60, 60))
    for b in BARS:
        if t0 <= b <= t1:
            X = int((b - t0) / (t1 - t0) * w); d.line([(X, 0), (X, h)], fill=(80, 160, 255))
    return im


def clicks(x, name):
    m = x.mean(1)
    d2 = np.abs(np.diff(m, 2))
    hp = np.convolve(d2, np.ones(64) / 64, 'same') + 1e-6
    ratio = d2 / hp
    loud = np.abs(m[1:-1]) > 0.01
    ev = np.where((ratio > 25) & loud)[0]
    if len(ev):
        print(f'{name}: possible clicks at', ' '.join(f'{i / SR:.3f}' for i in ev[:12]))


if __name__ == '__main__':
    out = sys.argv[1]; files = sys.argv[2:]
    t0 = float(os.environ.get('T0', 0)); t1 = os.environ.get('T1'); t1 = float(t1) if t1 else None
    rows = []
    for p in files:
        x = load(p)
        clicks(x, os.path.basename(p))
        lab = Image.new('RGB', (1500, 16), (0, 0, 0)); ImageDraw.Draw(lab).text((4, 2), os.path.basename(p) + f'  peak {20*np.log10(np.abs(x).max()+1e-9):.1f} dBFS', fill='yellow')
        rows += [lab, spec_img(x, t0=t0, t1=t1), level_img(x, t0=t0, t1=t1)]
    H = sum(r.size[1] for r in rows)
    sheet = Image.new('RGB', (1500, H)); y = 0
    for r in rows: sheet.paste(r, (0, y)); y += r.size[1]
    sheet.save(out)
