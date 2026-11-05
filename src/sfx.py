"""Sound design for the R&D BIM film: real recordings (Freesound CC0, VSCO 2 CE) cut and placed frame-accurately."""
import os, numpy as np
from lib import *

STEMS = os.path.join(NP, 'stems')
_src = {}


def src(fid):
    if fid not in _src: _src[fid] = load(os.path.join(SFX, f'fs_{fid}.wav'))
    return _src[fid]


def cut(fid, a, b, pitch=0.0, rev=False, hp=None, lp=None, fin=0.004, fout=0.03):
    x = src(fid)[int(a * SR):int(b * SR)].copy()
    if hp: x = filt(x, 'highpass', hp, 2)
    if lp: x = filt(x, 'lowpass', lp, 2)
    if pitch: x = rs(x, 2 ** (-pitch / 12))
    if rev: x = x[::-1].copy()
    return fade(x, fin=fin, fout=fout, shape=1.5)


def peak_of(x):
    e = np.abs(x).max(1)
    k = int(0.01 * SR)
    sm = np.convolve(e, np.ones(k) / k, 'same')
    return int(np.argmax(sm))


sfx = np.zeros((N, 2), np.float32)
paper = np.zeros((N, 2), np.float32)


def put(buf, x, t, db=0.0, pan=0.0, anchor='start', pan_to=None):
    g = 10 ** (db / 20)
    if anchor == 'peak': t = t - peak_of(x) / SR
    if pan_to is None:
        place(buf, x, t, g, pan); return
    p = np.linspace(pan, pan_to, len(x))
    y = np.stack([x[:, 0] * np.sqrt(0.5 * (1 - p)) * 1.4142, x[:, 1] * np.sqrt(0.5 * (1 + p)) * 1.4142], 1)
    place(buf, y, t, g, 0.0)


put(sfx, cut('391447', 3.45, 4.10, pitch=-1, hp=90), 2.24, -3, -0.5, 'peak', pan_to=0.4)
put(sfx, cut('494789', 0.0, 0.65, pitch=-4, hp=90), 2.18, -9, 0.3, 'peak', pan_to=-0.3)
put(sfx, cut('218460', 0.0, 0.28, pitch=-6, lp=5000), 2.6, -9, 0.0)
put(sfx, cut('547414', 0.12, 0.42, pitch=-8, lp=3500), 2.6, -12, 0.0)
put(sfx, cut('494789', 0.05, 0.45, pitch=3, rev=True, hp=200), 2.9, -14, 0.0, 'peak')

flap_src = src('261244').mean(1)
hop = 96; n = len(flap_src) // hop
db = 20 * np.log10(np.sqrt((flap_src[:n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12))
ons = []
for i in range(2, n - 2):
    if db[i] - db[i - 2] > 9 and db[i] > -30 and db[i] >= db[i - 1] and (not ons or i - ons[-1] > 10): ons.append(i)
flaps = []
for a, b in zip(ons[:-1], ons[1:]):
    if 8.0 < a * hop / SR < 70.0 and (b - a) * hop / SR > 0.05:
        s = a * hop - int(0.002 * SR)
        x = src('261244')[s:s + int(0.045 * SR)]
        flaps.append(fade(filt(x, 'highpass', 400, 2), fin=0.001, fout=0.015, shape=1.5))
rng = np.random.default_rng(7)
ts, te, P = 3.52, 7.1, 2.7
ticks, acc = [], 0.0
dt = 1 / SR * 48
for k in range(int((te - ts) / dt)):
    t = ts + k * dt
    u = (t - ts) / (te - ts)
    acc += 46.0 * (1 - u) ** 1.05 * dt
    if acc >= 1.0:
        acc -= 1.0; ticks.append(t)
for i, t in enumerate(ticks):
    u = (t - ts) / (te - ts)
    g = -15 - 4 * u - 3 * max(0.0, 1 - (t - ts) / 0.15)
    f = flaps[rng.integers(len(flaps))]
    f = filt(rs(f, 2 ** (-rng.uniform(-0.7, 0.7) / 12)), 'lowpass', 6500, 2)
    put(sfx, f, t + rng.uniform(-0.002, 0.002), g, rng.uniform(-0.3, 0.3))
put(sfx, cut('384698', 0.03, 0.19, hp=300), 7.1, -11, 0.1)
put(sfx, flaps[3], 7.1, -13, -0.1)
print('counter ticks', len(ticks))

put(sfx, cut('431222', 3.96, 4.6, hp=350), 8.2, -12, 0.15)
put(sfx, cut('391447', 8.62, 9.25, hp=120), 8.24, -11, 0.4, 'peak', pan_to=-0.4)
put(sfx, cut('391447', 6.88, 7.45, pitch=-3, hp=90), 9.95, -12, 0.5, 'peak', pan_to=-0.5)
for i, t in enumerate([10.53, 10.57, 10.61, 10.65, 10.69, 10.73, 10.77]):
    put(sfx, cut('353108', 5.97, 6.08, pitch=5 - i, hp=800), t, -20 + i * 0.4, 0.45)

put(sfx, cut('391447', 0.40, 1.10, pitch=-3, hp=80), 12.62, -8, -0.3, 'peak', pan_to=0.3)
put(sfx, cut('391447', 3.45, 4.10, pitch=1, hp=150), 12.72, -15, 0.3, 'peak', pan_to=-0.2)
put(paper, cut('751868', 10.6, 11.5, hp=120), 13.97, -9, -0.1, 'peak')
put(paper, cut('751868', 14.9, 15.85, hp=120), 15.2, -11, 0.15, 'peak')
put(paper, cut('751868', 16.4, 17.15, hp=120), 16.33, -12, -0.15, 'peak')
rf = cut('339963', 0.30, 1.25, hp=150, fout=0.12)
rf = rf * env_curve(len(rf), [(0, 0.5), (0.3, 1.0), (0.95, 0.8)])[:, None]
put(paper, rf[:int(0.58 * SR)], 16.36, -7, 0.1)
put(paper, fade(rf[int(0.58 * SR):], fout=0.06), 16.36 + 0.58, -12, 0.1)
put(paper, cut('416416', 0.0, 0.45, hp=70), 16.9, -9, 0.0)
put(sfx, cut('391447', 4.90, 5.45, hp=120), 17.55, -16, 0.0, 'peak')

for i, t in enumerate([18.07, 18.20, 18.30, 18.43]):
    put(sfx, cut('664698', 3.12, 3.22, pitch=-2 + i * 1.5, hp=600), t, -18, -0.45)
for t, pitch, db_, pan, seg in [(18.42, -5, -11, -0.4, (8.62, 9.25)), (18.58, -3, -13, 0.4, (3.45, 4.10)),
                                (18.74, -1, -15, -0.2, (6.88, 7.45)), (18.88, 1, -17, 0.25, (4.90, 5.45))]:
    put(sfx, cut('391447', *seg, pitch=pitch, hp=110), t, db_, pan, 'peak', pan_to=pan * -0.3)
scr = load(os.path.join(VSCO, 'VSCO 1 Percussion', 'varMetal', 'Cymbals', 'susp', 'susp_FX_scrape_1.wav'))
scr = fade(filt(scr[onset(scr, -40):][:int(1.0 * SR)], 'highpass', 1800, 2), fin=0.15, fout=0.4)
put(sfx, scr, 18.3, -20, 0.2)
put(sfx, cut('391447', 0.40, 1.10, pitch=-2, rev=True, hp=90), 20.98, -11, 0.4, 'peak', pan_to=-0.1)
put(sfx, cut('494789', 0.0, 0.65, pitch=-2, rev=True, hp=120), 20.95, -15, -0.4, 'peak')
put(sfx, cut('513819', 16.5, 16.95, hp=60), 21.02, -6, 0.0, 'peak')
put(sfx, cut('218460', 0.0, 0.28, pitch=-12, lp=2500), 21.02, -13, 0.0)

put(sfx, cut('391447', 3.45, 4.10, hp=100), 22.39, -6, 0.5, 'peak', pan_to=-0.5)
put(sfx, cut('391447', 6.88, 7.45, pitch=-2, rev=True, hp=100), 23.03, -12, 0.0, 'peak')
put(sfx, cut('219161', 0.0, 0.27, pitch=1.4), 23.33, -11, -0.35)
put(sfx, cut('219161', 0.0, 0.27, pitch=4.4), 23.40, -12, 0.0)
put(sfx, cut('218460', 0.0, 0.28, pitch=3.9), 23.50, -11, 0.3)
put(sfx, cut('547414', 0.12, 0.42, pitch=-5, lp=4000), 23.505, -15, 0.0)
put(sfx, cut('218460', 0.0, 0.28, pitch=1.0), 23.56, -19, 0.15)
put(sfx, cut('391447', 8.62, 9.25, pitch=2, hp=200), 24.1, -15, -0.3, 'peak', pan_to=0.3)

save(os.path.join(STEMS, 'sfx.wav'), sfx)
save(os.path.join(STEMS, 'paper.wav'), paper)
print('sfx peak', float(np.abs(sfx).max()), 'paper peak', float(np.abs(paper).max()))
