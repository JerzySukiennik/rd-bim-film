"""Score for the R&D BIM film: 100 BPM, D minor, every chapter of the edit lands on a downbeat. Renders music stems."""
import os, subprocess, numpy as np
from lib import *

STEMS = os.path.join(NP, 'stems'); os.makedirs(STEMS, exist_ok=True)


def T(bar, beat=0.0, six=0.0):
    return 0.8 + 2.4 * bar + 0.6 * beat + 0.15 * six


ROOT = {'D': 38, 'Bb': 34, 'C': 36, 'F': 41, 'A': 33}
ARP = {'D': [62, 65, 69, 74], 'F': [65, 69, 72, 77], 'Bb': [62, 65, 70, 74], 'C': [64, 67, 72, 76], 'A': [64, 69, 73, 76]}


def chord_at(t):
    seq = [(T(1), 'D'), (T(3), 'Bb'), (T(4), 'C'), (T(5), 'D'), (T(6), 'F'), (T(7), 'Bb'), (T(8), 'C'), (T(8, 2), 'A'), (T(9), 'D')]
    c = 'D'
    for s, n in seq:
        if t >= s - 1e-6: c = n
    return c


def curve(t, pts):
    return float(np.interp(t, [p[0] for p in pts], [p[1] for p in pts]))


syn = {'bass': [], 'brass': [], 'pluck': [], 'sub': [], 'drone': []}


def S(patch, t, dur, midi, vel, cut, env, pan=0.0):
    syn[patch].append(f"{patch} {t:.5f} {dur:.5f} {midi:.3f} {vel:.4f} {cut:.2f} {env:.3f} {pan:.3f}")


BASS_CUT = [(T(1), 170), (T(3), 420), (T(5) - 0.01, 640), (T(5), 360), (T(7) - 0.01, 620), (T(7), 820), (T(8, 2), 1150), (T(9), 1300)]
BASS_VEL = [(T(1), 0.5), (T(3), 0.72), (T(5) - 0.01, 0.74), (T(5), 0.55), (T(7) - 0.01, 0.68), (T(7), 0.9), (T(9), 1.0)]
PAT_V = [1.0, 0.6, 0.86, 0.64]
k = 0
t = T(1)
while t < T(9) - 1e-6:
    c = chord_at(t + 1e-4)
    pos = k % 4
    m = ROOT[c] + (12 if pos == 2 else 0)
    v = PAT_V[pos] * curve(t, BASS_VEL)
    if T(8, 2) <= t: v *= curve(t, [(T(8, 2), 0.95), (T(9), 1.12)])
    S('bass', t, 0.098, m, v, curve(t, BASS_CUT), 2.4 if pos != 0 else 2.9, 0.0)
    k += 1; t = T(1) + k * 0.15
S('bass', T(9), 0.55, 38, 1.0, 1500, 2.2)
k = 0; t = T(9, 1)
while t < T(9, 3) - 1e-6:
    pos = k % 4
    S('bass', t, 0.095, 38 + (12 if pos == 2 else 0), PAT_V[pos] * curve(t, [(T(9, 1), 0.35), (T(9, 3), 0.85)]), curve(t, [(T(9, 1), 220), (T(9, 3), 700)]), 2.5)
    k += 1; t = T(9, 1) + k * 0.15
S('bass', T(9, 3), 0.75, 38, 1.0, 950, 2.4)

for t0, m, v, d in [(0.2, 26, 0.55, 1.3), (T(0, 3), 26, 0.75, 0.7), (T(3), 22, 0.5, 0.8), (T(5), 26, 0.45, 0.9),
                    (T(7), 22, 0.7, 0.9), (T(9), 26, 1.0, 1.5), (T(9, 3), 26, 0.95, 0.9)]:
    S('sub', t0, d, m, v, 0, 1)

for m, p in [(38, 0.0), (45, -0.3), (50, 0.3)]:
    S('drone', 0.0, 2.9, m, 0.42, 260, 1.4, p)

for m, p in [(50, -0.4), (53, 0.0), (57, 0.4)]:
    S('brass', 0.18, 1.75, m, 0.38, 380, 1.9, p)

BR = [(T(3), 2.35, [62, 65, 70], 0.3), (T(4), 2.35, [64, 67, 72], 0.34),
      (T(7), 2.35, [62, 65, 70, 74], 0.62), (T(8), 1.15, [64, 67, 72, 76], 0.7), (T(8, 2), 1.15, [64, 69, 73, 76], 0.8),
      (T(9), 0.5, [62, 65, 69, 74], 0.95), (T(9, 3), 0.75, [62, 69, 74], 0.9)]
for t0, d, ms, v in BR:
    for j, m in enumerate(ms):
        S('brass', t0, d, m, v, 520 + 200 * v, 2.3, (j / (len(ms) - 1) - 0.5) * 0.9)

k = 0; t = T(5)
APAT = [0, 1, 2, 3, 2, 1, 2, 3]
while t < T(9) - 1e-6:
    c = chord_at(t + 1e-4)
    m = ARP[c][APAT[k % 8]]
    v = curve(t, [(T(5), 0.26), (T(7), 0.3), (T(8, 2), 0.36), (T(9), 0.42)]) * (1.0 if k % 4 == 0 else 0.8)
    S('pluck', t, 0.07, m, v, curve(t, [(T(5), 700), (T(7), 1000), (T(9), 1600)]), 3.0, 0.35 if k % 2 else -0.35)
    k += 1; t = T(5) + k * 0.15
k = 0; t = T(9, 1)
while t < T(9, 3) - 1e-6:
    m = ARP['D'][APAT[k % 8]]
    S('pluck', t, 0.07, m, curve(t, [(T(9, 1), 0.12), (T(9, 3), 0.38)]), 900, 3.0, 0.35 if k % 2 else -0.35)
    k += 1; t = T(9, 1) + k * 0.15

synth_bin = os.path.join(NP, 'synth')
for patch, lines in syn.items():
    nf = os.path.join(NP, f'notes_{patch}.txt'); raw = os.path.join(NP, f'syn_{patch}.f32')
    open(nf, 'w').write('\n'.join(lines) + '\n')
    subprocess.run(['nice', '-n', '10', synth_bin, nf, raw, str(DUR + 0.5)], check=True)
    x = np.fromfile(raw, np.float32).reshape(-1, 2)
    x = resample_poly(x, 1, 2, axis=0).astype(np.float32)[:N]
    save(os.path.join(STEMS, f'syn_{patch}.wav'), x * 0.5)
    os.remove(raw)
    print(patch, len(lines), 'notes peak', float(np.abs(x).max()))

cb = Instrument('Strings/Solo Contrabass/SusNV')
vc = Instrument('Strings/Cello Section/susvib')
vcs = Instrument('Strings/Cello Section/spic', pat=r'_([A-G]#?)(-?\d)_v(\d)')
va = Instrument('Strings/Viola Section/susvib')
vn = Instrument('Strings/Violin Section/susVib', pat=r'_([A-G]#?)(-?\d)_v(\d)')
vnt = Instrument('Strings/Violin Section/Trem', pat=r'_([A-G]#?)(-?\d)_v(\d)')
hn = Instrument('Brass/F Horn/sus')
hns = Instrument('Brass/F Horn/stac')
tb = Instrument('Brass/Tenor Trombone/sus')
tbs = Instrument('Brass/Tenor Trombone/stac')
tu = Instrument('Brass/Tuba/sus')

strings = np.zeros((N, 2), np.float32)
brass = np.zeros((N, 2), np.float32)
LEAD = 0.035


def sus(buf, inst, t0, dur, midi, vel, pan, gain=1.0, attack=0.0, release=0.45, swell=None):
    y = inst.note(midi, vel, dur=dur, release=release, attack=attack)
    if swell is not None:
        y = y * env_curve(len(y), swell)[:, None]
    place(buf, y, t0 - LEAD, gain, pan)


B = lambda b, beat=0: T(b, beat)
bars = [(1, 2, 'D'), (3, 1, 'Bb'), (4, 1, 'C'), (5, 1, 'D'), (6, 1, 'F'), (7, 1, 'Bb')]
CB = {'D': 38, 'Bb': 34, 'C': 36, 'F': 41, 'A': 33}
VC = {'D': 50, 'Bb': 46, 'C': 48, 'F': 48, 'A': 45}
dyn = {1: 0.62, 2: 0.66, 3: 0.68, 4: 0.7, 5: 0.66, 6: 0.72, 7: 0.88, 8: 0.95}

sus(strings, cb, 0.15, 3.05, 38, 0.9, -0.15, 0.7, attack=1.4, release=0.3)
sus(strings, vc, 0.15, 3.05, 50, 0.3, 0.1, 0.55, attack=1.6, release=0.3)
for b0, nb, c in bars:
    d = 2.4 * nb
    sus(strings, cb, B(b0), d, CB[c], 0.9, -0.15, dyn[b0])
    sus(strings, vc, B(b0), d, VC[c], dyn[b0], 0.1, dyn[b0] * 0.9)
for c, t0, d in [('C', B(8), 1.2), ('A', B(8, 2), 1.2)]:
    sus(strings, cb, t0, d, CB[c], 0.9, -0.15, 1.0)
    sus(strings, vc, t0, d, VC[c], 0.95, 0.1, 0.95)
sus(strings, cb, B(9), 0.55, 38, 0.9, -0.15, 1.1, release=0.6)
sus(strings, vc, B(9), 0.55, 50, 0.95, 0.1, 1.0, release=0.6)
sus(strings, vc, B(9), 0.55, 38, 0.95, -0.1, 0.6, release=0.6)
sus(strings, cb, B(9, 1), 1.2, 38, 0.9, -0.15, 0.5, swell=[(0, 0.2), (1.2, 1.0), (1.6, 0)])
sus(strings, vc, B(9, 1), 1.2, 50, 0.6, 0.1, 0.5, swell=[(0, 0.15), (1.2, 1.0), (1.6, 0)])
sus(strings, cb, B(9, 3), 0.75, 38, 0.9, -0.15, 1.1, release=0.5)
sus(strings, vc, B(9, 3), 0.75, 50, 0.95, 0.1, 1.0, release=0.5)

VA = [(2, 1, 57), (3, 1, 53), (4, 1, 55), (5, 1, 57), (6, 1, 57), (7, 1, 58)]
for b0, nb, m in VA:
    sus(strings, va, B(b0), 2.4 * nb, m, dyn[b0], -0.35, dyn[b0] * 0.8, attack=0.25 if b0 == 2 else 0.0)
sus(strings, va, B(8), 1.2, 60, 0.95, -0.35, 0.85); sus(strings, va, B(8, 2), 1.2, 61, 0.95, -0.35, 0.9)
sus(strings, va, B(9), 0.55, 62, 0.95, -0.35, 0.95, release=0.6)
sus(strings, va, B(9, 3), 0.75, 57, 0.95, -0.35, 0.85, release=0.5)

V2 = [(3, 62), (4, 64), (5, 65), (6, 65), (7, 65)]
for b0, m in V2:
    sus(strings, vn, B(b0), 2.4, m, dyn[b0], -0.55, dyn[b0] * 0.7, attack=0.3 if b0 == 3 else 0.0)
sus(strings, vn, B(8), 2.4, 64, 0.95, -0.55, 0.8)
sus(strings, vn, B(9), 0.55, 69, 0.95, -0.55, 0.9, release=0.6)
sus(strings, vn, B(9, 3), 0.75, 69, 0.95, -0.55, 0.8, release=0.5)
V1 = [(5, 69), (6, 72), (7, 74)]
for b0, m in V1:
    sus(strings, vn, B(b0), 2.4, m, dyn[b0], 0.5, dyn[b0] * 0.62, attack=0.4 if b0 == 5 else 0.0)
sus(strings, vnt, B(8), 2.4, 76, 0.95, 0.5, 0.7, swell=[(0, 0.5), (1.2, 0.7), (2.4, 1.2)])
sus(strings, vn, B(9), 0.55, 74, 0.95, 0.5, 0.75, release=0.6)
sus(strings, vn, B(9), 0.55, 81, 0.95, 0.35, 0.55, release=0.6)
sus(strings, vn, B(9, 3), 0.75, 74, 0.95, 0.5, 0.7, release=0.5)
sus(strings, vn, B(9, 3), 0.75, 86, 0.95, 0.35, 0.45, release=0.5)

for b0, nb in [(3, 2), (7, 2)]:
    for k in range(16 * nb):
        t0 = T(b0) + k * 0.15
        c = chord_at(t0 + 1e-4)
        m = VC[c] + (12 if k % 4 == 2 else 0)
        v = [1.0, 0.55, 0.8, 0.6][k % 4] * (0.55 if b0 == 3 else 0.8)
        y = vcs.note(m, 0.99, dur=0.16, release=0.08)
        place(strings, y, t0 - 0.008, v, 0.2)

HN = [(2, 1, [50, 53, 57], 0.28), (3, 1, [50, 53, 58], 0.4), (4, 1, [52, 55, 60], 0.42), (5, 1, [50, 53, 57], 0.4),
      (6, 1, [48, 53, 57], 0.45), (7, 1, [50, 53, 58], 0.85)]
for b0, nb, ms, v in HN:
    for j, m in enumerate(ms):
        sus(brass, hn, B(b0), 2.4 * nb, m, v, -0.25 + 0.25 * j, v, attack=0.35 if b0 == 2 else 0.05)
for t0, d, ms, v in [(B(8), 1.2, [52, 55, 60], 0.9), (B(8, 2), 1.2, [52, 57, 61], 0.98)]:
    for j, m in enumerate(ms):
        sus(brass, hn, t0, d, m, v, -0.25 + 0.25 * j, v)
for j, m in enumerate([50, 53, 57, 62]):
    sus(brass, hn, B(9), 0.55, m, 0.99, -0.3 + 0.2 * j, 1.0, release=0.7)
for j, m in enumerate([50, 57, 62]):
    sus(brass, hn, B(9, 3), 0.75, m, 0.99, -0.25 + 0.25 * j, 1.0, release=0.6)
for t0, d, ms, v in [(B(7), 2.4, [46, 50], 0.7), (B(8), 1.2, [48, 52], 0.85), (B(8, 2), 1.2, [45, 49], 0.95), (B(9), 0.55, [45, 50], 1.0), (B(9, 3), 0.75, [45, 50], 0.95)]:
    for j, m in enumerate(ms):
        sus(brass, tb, t0, d, m, v, 0.3 - 0.2 * j, v * 0.85, release=0.6)
for t0, d, m, v in [(B(7), 2.4, 34, 0.75), (B(8), 1.2, 36, 0.85), (B(8, 2), 1.2, 33, 0.95), (B(9), 0.55, 38, 1.0), (B(9, 3), 0.75, 38, 1.0)]:
    sus(brass, tu, t0, d, m, v, 0.0, v * 0.8, release=0.6)
for t0, ms, low, g in [(B(3), [46, 50, 53], 34, 0.7), (B(7), [46, 50, 53], 34, 0.9), (B(9), [50, 53, 57], 38, 1.0), (B(9, 3), [50, 57], 38, 1.0)]:
    for j, m in enumerate(ms):
        place(brass, hns.note(m, 0.99), t0 - 0.012, g * 0.8, -0.3 + 0.3 * j)
    place(brass, tbs.note(low, 0.99), t0 - 0.012, g * 0.7, 0.2)

save(os.path.join(STEMS, 'strings.wav'), strings * 0.25)
save(os.path.join(STEMS, 'brass.wav'), brass * 0.25)
print('strings peak', float(np.abs(strings).max() * 0.25), 'brass peak', float(np.abs(brass).max() * 0.25))

TIMP = {'Timpani1': 41.5, 'Timpani2': 46.8, 'Timpani3': 49.5, 'Timpani4': 52.4, 'Timpani5': 54.6}
_tc = {}


def timp(midi, roll=False, rr=1):
    best = min(TIMP, key=lambda k: abs(TIMP[k] - midi) + (0.4 if TIMP[k] < midi else 0))
    kind = 'Roll_v5' if roll else 'Hit_v3' if best == 'Timpani1' else 'Hit_v4'
    p = os.path.join(VSCO, 'Percussion', 'Timpani', 'Rolls' if roll else '', f'{best}_{kind}_rr{1 if roll else rr}_Sum.wav')
    if best == 'Timpani5' and roll: p = p.replace('Roll_v5', 'Roll_v4')
    key = (p, midi)
    if key not in _tc:
        x = load(p); o = max(0, onset(x, -40) - int(0.003 * SR)); x = x[o:]
        _tc[key] = rs(x, 2 ** (-(midi - TIMP[best]) / 12))
    return _tc[key].copy()


perc = np.zeros((N, 2), np.float32)
TH = [(0.2, 38, 0.35), (T(0, 3), 38, 0.75), (T(1), 38, 0.4), (T(2), 38, 0.42), (T(3), 46, 0.9), (T(4), 48, 0.6),
      (T(5), 50, 0.75), (T(6), 41, 0.6), (T(7), 46, 1.0), (T(7, 2), 46, 0.55), (T(7, 3.5), 41, 0.45),
      (T(8), 48, 0.9), (T(9), 38, 1.15), (T(9), 50, 0.8), (T(9, 3), 38, 1.05), (T(9, 3), 50, 0.6)]
for i, (t0, m, g) in enumerate(TH):
    place(perc, timp(m, rr=1 + i % 2), t0, g, -0.2)
for t_end, m, ln, g in [(T(3), 45, 0.8, 0.65), (T(5), 45, 0.75, 0.6), (T(7), 41, 0.8, 0.7), (T(9), 45, 1.2, 1.0)]:
    y = timp(m, roll=True)[:int(ln * SR)]
    y = y * env_curve(len(y), [(0, 0.03), (ln * 0.5, 0.28), (ln * 0.85, 0.7), (ln, 1.0)])[:, None]
    y = fade(y, fout=0.012, shape=1)
    place(perc, y, t_end - ln, g, -0.2)

pdir = os.path.join(VSCO, 'VSCO 1 Percussion')
bd = {k: load(os.path.join(pdir, 'drums', 'bass', f'bdrum_{k}_1.wav')) for k in ['fff', 'ff', 'f', 'mp']}
for k in bd: bd[k] = bd[k][max(0, onset(bd[k], -40) - 100):]
for t0, k, g in [(T(0, 3), 'mp', 0.7), (T(3), 'f', 0.65), (T(5), 'mp', 0.5), (T(7), 'ff', 0.85), (T(7, 2), 'mp', 0.45),
                 (T(8), 'f', 0.6), (T(9), 'fff', 1.0), (T(9, 3), 'ff', 0.95)]:
    place(perc, bd[k], t0, g, 0.0)
roll = load(os.path.join(pdir, 'drums', 'bass', 'bdrum_roll1.wav'))
roll = roll[onset(roll, -40):][:int(1.2 * SR)]
roll = roll * env_curve(len(roll), [(0, 0.0), (0.6, 0.3), (1.2, 1.0)])[:, None]
place(perc, fade(roll, fout=0.01, shape=1), T(9) - 1.2, 0.7, 0.0)

cy = os.path.join(pdir, 'varMetal', 'Cymbals')
crash = load(os.path.join(cy, 'clash', 'crash_hit_fff_loose.wav')); crash = crash[max(0, onset(crash, -40) - 50):]
susp = load(os.path.join(cy, 'susp', 'susp_hit_softmall_ff.wav')); susp = susp[max(0, onset(susp, -40) - 50):]
sroll = load(os.path.join(cy, 'susp', 'susp_hit_softmall_roll2_cresc.wav'))
place(perc, crash, T(9), 0.55, 0.25)
place(perc, susp, T(7), 0.35, -0.3)
place(perc, susp, T(9, 3), 0.4, 0.3)
for t_end, ln, g, pan in [(2.08, 1.5, 0.5, -0.2), (T(5), 1.3, 0.45, 0.25), (T(9), 2.2, 0.5, -0.25)]:
    r = susp[:int(4.0 * SR)][::-1]
    r = r[-int(ln * SR):]
    r = fade(r, fin=ln * 0.4, shape=2)
    place(perc, fade(r, fout=0.01, shape=1), t_end - ln, g, pan)
pk = np.abs(sroll).max(1); pki = int(np.argmax(pk))
sr2 = sroll[:pki + int(0.02 * SR)]
sr2 = fade(sr2[-int(1.6 * SR):], fin=0.4, fout=0.015, shape=1.5)
place(perc, sr2, T(9) - len(sr2) / SR + 0.01, 0.45, 0.3)
gong = load(os.path.join(pdir, 'varMetal', 'Gong', 'gong_hit_ff.wav')); gong = gong[max(0, onset(gong, -40) - 50):]
gmp = load(os.path.join(pdir, 'varMetal', 'Gong', 'gong_hit_mp.wav')); gmp = gmp[max(0, onset(gmp, -40) - 50):]
place(perc, gong, T(9), 0.45, 0.0)
place(perc, gmp, T(9, 3), 0.3, 0.0)
save(os.path.join(STEMS, 'perc.wav'), perc * 0.3)
print('perc peak', float(np.abs(perc).max() * 0.3))
