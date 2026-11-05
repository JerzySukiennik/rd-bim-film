"""Download the VSCO 2 CE (CC0) samples this score uses."""
import json, os, re, sys, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
ROOT = os.path.expanduser('~/Downloads/Claude/Projects/RD-BIM-Film/Niepotrzebne/samples')
tree = json.load(open(os.path.join(ROOT, 'vsco_tree.json')))['tree']
SEL = [
    ('Strings/Cello Section/susvib', r'_v[13]_'), ('Strings/Viola Section/susvib', r'_v2_'),
    ('Strings/Violin Section/susVib', r'_v[12]'), ('Strings/Violin Section/Trem', r'_v1'),
    ('Strings/Solo Contrabass/SusNV', r'_v3_'), ('Strings/Cello Section/spic', r'_v2_'),
    ('Strings/Violin Section/Spic', r'_v2_'), ('Strings/Solo Contrabass/Spic', r'_v3_'),
    ('Brass/F Horn/sus', r'_v[23]_'), ('Brass/Tenor Trombone/sus', r'_v2_'), ('Brass/Tuba/sus', r'_v2_'),
    ('Brass/F Horn/stac', r'_v3_'), ('Brass/Tenor Trombone/stac', r'_v4_'),
    ('Percussion/Timpani', r'Hit_v[34]|Roll_v5|Roll_v4'),
    ('VSCO 1 Percussion/drums/bass', r'bdrum_(fff_1|ff_1|f_1|mp_1|roll1|roll_short_1|roll_long1)\.wav'),
    ('VSCO 1 Percussion/varMetal/Cymbals', r'crash_hit_(fff_loose|ff_loose|mp_loose)\.wav|softmall_(roll2_cresc|roll4_fff_long|ff|mp)|susp_FX_scrape_(1|2|continuous)'),
    ('VSCO 1 Percussion/varMetal/Gong', r'gong_(hit_ff|hit_mp|roll_medium_f|scrape_1|hit_pp)\.wav'),
]
jobs = []
for folder, pat in SEL:
    for e in tree:
        if e['type'] == 'blob' and e['path'].startswith(folder + '/') and e['path'].endswith('.wav') and re.search(pat, e['path']):
            jobs.append(e['path'])
def get(p):
    out = os.path.join(ROOT, 'vsco', p)
    if os.path.exists(out) and os.path.getsize(out) > 1000: return 0
    os.makedirs(os.path.dirname(out), exist_ok=True)
    u = 'https://raw.githubusercontent.com/sgossner/VSCO-2-CE/master/' + urllib.parse.quote(p)
    data = urllib.request.urlopen(u, timeout=120).read()
    open(out, 'wb').write(data); return len(data)
print(len(jobs), 'files')
with ThreadPoolExecutor(4) as ex:
    tot = sum(ex.map(get, jobs))
print('done MB', tot / 1e6)
