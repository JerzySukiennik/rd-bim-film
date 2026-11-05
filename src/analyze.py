"""Print onset/event structure of each recording to pick slices without listening."""
import sys, numpy as np, glob, os, json
from scipy.io import wavfile
def load(p):
    sr, x = wavfile.read(p); x = x.astype(np.float32) / 32768
    return sr, (x.mean(1) if x.ndim > 1 else x)
for p in sys.argv[1:]:
    sr, x = load(p); hop = 240
    n = len(x) // hop
    fr = x[:n * hop].reshape(n, hop)
    rms = np.sqrt((fr ** 2).mean(1) + 1e-12); db = 20 * np.log10(rms)
    spec = np.abs(np.fft.rfft(fr * np.hanning(hop), axis=1)); f = np.fft.rfftfreq(hop, 1 / sr)
    cen = (spec * f).sum(1) / (spec.sum(1) + 1e-9)
    floor = np.percentile(db, 20); peak = db.max()
    thr = max(floor + 12, peak - 40)
    ev = []; i = 0
    while i < n:
        if db[i] > thr:
            j = i
            while j < n and db[j] > thr - 6: j += 1
            k = i + int(np.argmax(db[i:j]))
            ev.append((i * hop / sr, (j - i) * hop / sr, db[k], cen[i:j].mean()))
            i = j + 2
        else: i += 1
    name = os.path.basename(p)
    print(f"## {name} dur={len(x)/sr:.2f}s peak={peak:.1f}dB floor={floor:.1f}dB events={len(ev)}")
    print('   ' + ' '.join(f"[{t:.2f}+{d:.2f} {l:.0f}dB {c/1000:.1f}k]" for t, d, l, c in ev[:40]))
