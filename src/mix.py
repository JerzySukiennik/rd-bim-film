"""Mix and master the R&D BIM film: hall convolution, delay, ducking under SFX, bus glue, true-peak limiter at -14 LUFS."""
import os, sys, numpy as np, pyloudnorm as pyln
from lib import *

STEMS = os.path.join(NP, 'stems')
OUT = os.path.join(NP, 'renders'); os.makedirs(OUT, exist_ok=True)
meter = pyln.Meter(SR)


def lufs(x):
    try: return meter.integrated_loudness(x.astype(np.float64))
    except Exception: return -99


def st(name): return load(os.path.join(STEMS, name + '.wav'))[:N]


def unit_ir(fid, gain=1.0):
    ir = load(os.path.join(SFX, f'fs_{fid}.wav'))
    ir = ir[onset(ir, -30):]
    ir = fade(ir, fout=0.3)
    return ir / np.sqrt((ir ** 2).sum() / 2) * gain


hall = unit_ir('423803')
cath = unit_ir('240593')
L = max(len(hall), len(cath))
IR = np.zeros((L, 2), np.float32); IR[:len(hall)] += hall * 0.85; IR[:len(cath)] += cath * 0.45
IR = IR / np.sqrt((IR ** 2).sum() / 2)
room = unit_ir('423866')

GAIN = {'syn_bass': -3.5, 'syn_sub': -5.0, 'syn_brass': -9.0, 'syn_pluck': -1.0, 'syn_drone': -4.0,
        'strings': 2.0, 'brass': 4.0, 'perc': 3.0, 'sfx': 1.0, 'paper': -2.0}
SEND = {'syn_bass': 0.06, 'syn_sub': 0.0, 'syn_brass': 0.32, 'syn_pluck': 0.3, 'syn_drone': 0.4,
        'strings': 0.38, 'brass': 0.36, 'perc': 0.3}

s = {k: st(k) for k in GAIN}
s['syn_sub'] = filt(s['syn_sub'], 'lowpass', 260, 2)
s['syn_bass'] = filt(s['syn_bass'], 'highpass', 32, 2)
s['syn_bass'] = peq(s['syn_bass'], 250, -2.5, 1.0)
s['syn_brass'] = filt(s['syn_brass'], 'highpass', 140, 2)
s['strings'] = shelf(filt(s['strings'], 'highpass', 35, 2), 7000, 1.5, 'high')
s['brass'] = filt(s['brass'], 'highpass', 40, 2)
p = filt(s['syn_pluck'], 'highpass', 300, 2)
d = int(0.45 * SR); y = p.copy()
for k in range(1, 6):
    tap = np.zeros_like(p); g = 0.42 ** k
    tap[k * d:] = p[:-k * d] * g
    if k % 2: tap = tap[:, ::-1]
    y += filt(tap, 'lowpass', 4500 - 500 * k, 1)
s['syn_pluck'] = y

for k in GAIN: s[k] = s[k] * 10 ** (GAIN[k] / 20)

dry = np.zeros((N, 2), np.float32); send = np.zeros((N, 2), np.float32)
for k in SEND:
    dry += s[k]; send += s[k] * SEND[k]
wet = convolve_ir(send, IR, predelay=0.018)
wet = filt(filt(wet, 'highpass', 160, 2), 'lowpass', 9000, 2)
music = dry + wet

fx = s['sfx'] + s['paper']
fxwet = convolve_ir(s['sfx'] * 0.14 + s['paper'] * 0.06, room, predelay=0.008)
fxwet = filt(fxwet, 'highpass', 200, 2)
fx = fx + fxwet

env = np.abs(fx).max(1)
k = int(0.005 * SR); env = np.convolve(env, np.ones(k) / k, 'same')
att, rel = np.exp(-1 / (0.01 * SR)), np.exp(-1 / (0.25 * SR))
g = np.zeros_like(env); v = 0.0
for i in range(0, len(env), 32):
    e = env[i:i + 32].max()
    c = att if e > v else rel
    v = c * v + (1 - c) * e
    g[i:i + 32] = v
duck = 10 ** (-np.clip(20 * np.log10(g + 1e-6) + 30, 0, 12) * 0.22 / 20)
music = music * duck[:, None]


def comp(x, thr_db, ratio, att_ms, rel_ms, knee=6.0):
    lvl = np.sqrt(filt(x.mean(1, keepdims=True) ** 2, 'lowpass', 30, 1)[:, 0].clip(1e-12))
    ldb = 20 * np.log10(lvl)
    over = ldb - thr_db
    gr = np.where(over < -knee / 2, 0, np.where(over > knee / 2, over * (1 - 1 / ratio), (over + knee / 2) ** 2 / (2 * knee) * (1 - 1 / ratio)))
    a, r = np.exp(-1 / (att_ms / 1000 * SR / 16)), np.exp(-1 / (rel_ms / 1000 * SR / 16))
    out = np.zeros(len(gr)); v = 0.0
    for i in range(0, len(gr), 16):
        e = gr[i]; c = a if e > v else r
        v = c * v + (1 - c) * e; out[i:i + 16] = v
    return x * (10 ** (-out / 20))[:, None].astype(np.float32)


music = comp(music, -24, 2.0, 30, 300)
mix = music + fx
mix = filt(mix, 'highpass', 30, 4)
mix = shelf(mix, 55, -3.5, 'low')

end = int(24.62 * SR)
tail = np.ones(N, np.float32); tail[end:] = np.linspace(1, 0, N - end) ** 1.6
mix = mix * tail[:, None]
mix[:int(0.004 * SR)] *= np.linspace(0, 1, int(0.004 * SR))[:, None]


def limit(x, ceiling_db=-1.2, look_ms=4, rel_ms=90):
    up = resample_poly(x, 4, 1, axis=0)
    pk = np.abs(up).max(1).reshape(-1, 4).max(1)[:len(x)]
    c = 10 ** (ceiling_db / 20)
    need = np.minimum(1.0, c / np.maximum(pk, 1e-9))
    la = int(look_ms / 1000 * SR)
    from scipy.ndimage import minimum_filter1d
    need = minimum_filter1d(need, 2 * la + 1)
    r = np.exp(-1 / (rel_ms / 1000 * SR)); gg = np.empty_like(need); v = 1.0
    for i in range(len(need)):
        v = need[i] if need[i] < v else r * v + (1 - r) * need[i]
        gg[i] = v
    gg = np.convolve(gg, np.ones(la) / la, 'same')
    return x * np.minimum(gg, need)[:, None]


target = -14.0
gain = target - lufs(mix)
for it in range(4):
    m2 = limit(mix * 10 ** (gain / 20))
    err = target - lufs(m2)
    if abs(err) < 0.15: break
    gain += err
master = m2
tp = 20 * np.log10(np.abs(resample_poly(master, 4, 1, axis=0)).max())
print(f'master: {lufs(master):.2f} LUFS, true peak {tp:.2f} dBTP')
for k in ['syn_bass', 'syn_brass', 'syn_pluck', 'strings', 'brass', 'perc', 'sfx', 'paper']:
    print(f'  {k:10s} {lufs(s[k]):6.1f} LUFS')
print(f'  music {lufs(music):.1f}  fx {lufs(fx):.1f}')
save(os.path.join(OUT, 'mix.wav'), master)
save(os.path.join(OUT, 'music_only.wav'), music * 10 ** (gain / 20))
save(os.path.join(OUT, 'fx_only.wav'), fx * 10 ** (gain / 20))
