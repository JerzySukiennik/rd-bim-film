"""Shared audio helpers: IO, resampling, sample instruments, filters, convolution reverb."""
import os, re, glob, subprocess, warnings
from fractions import Fraction
import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly, butter, sosfilt, fftconvolve

warnings.filterwarnings('ignore', category=wavfile.WavFileWarning)
SR = 48000
PROJ = os.path.expanduser('~/Downloads/Claude/Projects/RD-BIM-Film')
NP = os.path.join(PROJ, 'Niepotrzebne')
VSCO = os.path.join(NP, 'samples', 'vsco')
SFX = os.path.join(NP, 'sfx-raw', 'wav')
DUR = 25.0
N = int(DUR * SR)


def load(path, sr=SR):
    if not path.endswith('.wav'):
        tmp = os.path.join(NP, 'tmp_load.wav')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', path, '-ar', str(sr), tmp], check=True)
        path = tmp
    r, x = wavfile.read(path)
    if x.dtype == np.int16: x = x.astype(np.float32) / 32768
    elif x.dtype == np.int32: x = x.astype(np.float32) / 2147483648
    elif x.dtype == np.uint8: x = (x.astype(np.float32) - 128) / 128
    else: x = x.astype(np.float32)
    if x.ndim == 1: x = np.stack([x, x], 1)
    x = x[:, :2]
    if r != sr: x = rs(x, sr / r)
    return x


def save(path, x, sr=SR):
    y = np.clip(x, -1, 1)
    wavfile.write(path, sr, (y * 2147483647).astype(np.int32))


def rs(x, ratio):
    """Resample by ratio (output_len / input_len) with a polyphase FIR."""
    if abs(ratio - 1) < 1e-9: return x.copy()
    fr = Fraction(ratio).limit_denominator(1200)
    return resample_poly(x, fr.numerator, fr.denominator, axis=0).astype(np.float32)


def place(buf, x, t, gain=1.0, pan=0.0):
    """Mix stereo x into buf at time t (seconds), equal-power pan."""
    i = int(round(t * SR))
    if i >= len(buf): return
    a = max(0, -i); i = max(0, i)
    seg = x[a:a + len(buf) - i]
    if len(seg) == 0: return
    pl, pr = np.sqrt(0.5 * (1 - pan)) * 1.4142, np.sqrt(0.5 * (1 + pan)) * 1.4142
    buf[i:i + len(seg), 0] += seg[:, 0] * gain * pl
    buf[i:i + len(seg), 1] += seg[:, 1] * gain * pr


def fade(x, fin=0.0, fout=0.0, shape=2.0):
    y = x.copy()
    a, b = int(fin * SR), int(fout * SR)
    if a > 0: y[:a] *= (np.linspace(0, 1, a) ** shape)[:, None]
    if b > 0: y[-b:] *= (np.linspace(1, 0, b) ** shape)[:, None]
    return y


def env_curve(n, points):
    """Piecewise-linear gain curve over n samples from [(t_sec, gain), ...] relative to start."""
    ts = np.array([p[0] for p in points]) * SR
    gs = np.array([p[1] for p in points])
    return np.interp(np.arange(n), ts, gs).astype(np.float32)


def onset(x, rel_db=-45):
    m = np.abs(x).max(1)
    pk = m.max() + 1e-9
    idx = np.where(m > pk * 10 ** (rel_db / 20))[0]
    return int(idx[0]) if len(idx) else 0


def filt(x, kind, f, order=2):
    sos = butter(order, f, btype=kind, fs=SR, output='sos')
    return sosfilt(sos, x, axis=0).astype(np.float32)


def shelf(x, f, gain_db, kind='low'):
    """Simple shelving via parallel filtered band."""
    band = filt(x, 'lowpass' if kind == 'low' else 'highpass', f, 2)
    return x + band * (10 ** (gain_db / 20) - 1)


def peq(x, f, gain_db, q=1.0):
    bw = f / q
    lo, hi = max(20, f - bw / 2), min(SR / 2 - 100, f + bw / 2)
    band = filt(x, 'bandpass', [lo, hi], 2)
    return x + band * (10 ** (gain_db / 20) - 1)


def convolve_ir(x, ir, wet=1.0, predelay=0.0):
    pd = int(predelay * SR)
    out = np.zeros((len(x) + len(ir) + pd, 2), np.float32)
    for c in range(2):
        out[pd:pd + len(x) + len(ir) - 1, c] = fftconvolve(x[:, c], ir[:, c])
    return out[:len(x)] * wet


NOTE = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}


class Instrument:
    """VSCO multisample: files named ..._<Note><oct>_v<layer>... in Yamaha octave naming."""
    def __init__(self, folder, pat=r'_([A-G]#?)(-?\d)_v(\d)', trim_db=-42, lead=0.0):
        self.files = []
        for p in sorted(glob.glob(os.path.join(VSCO, folder, '*.wav'))):
            m = re.search(pat, os.path.basename(p))
            if not m: continue
            midi = (int(m.group(2)) + 2) * 12 + NOTE[m.group(1)]
            self.files.append((midi, int(m.group(3)), p))
        self.layers = sorted(set(v for _, v, _ in self.files))
        self.cache, self.raw = {}, {}
        self.trim_db, self.lead = trim_db, lead
        self.rr = 0

    def _raw(self, p):
        if p not in self.raw:
            x = load(p)
            o = max(0, onset(x, self.trim_db) - int(0.004 * SR))
            self.raw[p] = x[o:]
        return self.raw[p]

    def pick(self, midi, vel):
        layer = self.layers[min(len(self.layers) - 1, int(vel * len(self.layers) - 1e-6))]
        cands = [f for f in self.files if f[1] == layer] or self.files
        best = min(abs(c[0] - midi) for c in cands)
        near = [c for c in cands if abs(c[0] - midi) == best]
        self.rr += 1
        return near[self.rr % len(near)]

    def note(self, midi, vel, dur=None, release=0.3, attack=0.0):
        sm, _, p = self.pick(midi, vel)
        key = (p, midi)
        if key not in self.cache:
            x = self._raw(p)
            self.cache[key] = rs(x, 2 ** (-(midi - sm) / 12))
        y = self.cache[key]
        if dur is not None:
            n = min(len(y), int((dur + release) * SR))
            y = y[:n].copy()
            r = min(n, int(release * SR))
            if r > 0: y[n - r:] *= (np.linspace(1, 0, r) ** 2)[:, None]
        else:
            y = y.copy()
        if attack > 0: y = fade(y, fin=attack, shape=1.5)
        return y
