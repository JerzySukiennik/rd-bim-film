# R&D BIM film: sound design and score

New soundtrack for the 25 s R&D BIM promo ("Jeden model. Cały projekt."). The old AI audio is replaced with an original score in the style of Tron: Legacy (100 BPM, D minor) played by sampled real orchestra plus analog-style synths, and sound effects cut from real recordings. Every chapter of the edit (01 Model BIM, 02 Przekroje 3D, 03 Rysunki, 04 Koordynacja, end card) lands on a downbeat; effects are placed to the frame.

## Pipeline

- `src/synth.c`: synth voices (PolyBLEP saws, saturating ladder filter, analog drift), rendered at 96 kHz and decimated with a polyphase FIR.
- `src/score.py`: the score; renders synth, strings, brass and percussion stems.
- `src/sfx.py`: sound design from real recordings (split-flap counter, blade, paper, cloth whooshes, wood blocks tuned to D-F-A, door latch).
- `src/mix.py`: hall convolution (real IRs), ping-pong delay, ducking under SFX, bus compression, true-peak limiter at -14 LUFS.
- `src/lib.py`, `src/viz.py`, `src/analyze.py`: helpers, spectrogram checks, event analysis. `src/fetch_vsco.py`, `src/fs.py`, `src/fsget.py`: sample download.

Rebuild: `clang -O3 -o Niepotrzebne/synth src/synth.c -lm`, then `python3 src/score.py && python3 src/sfx.py && python3 src/mix.py` (run inside `src/`).

## Credits

Orchestral samples: Versilian Studios VSCO 2 Community Edition (CC0), https://github.com/sgossner/VSCO-2-CE

Recordings from Freesound, all CC0:
- "Wood block hit" by thomasjaunism (CC0), https://freesound.org/people/thomasjaunism/sounds/218460/
- "FrogBlock01.wav" by Jagadamba (CC0), https://freesound.org/people/Jagadamba/sounds/219161/
- "notredamenyc2014impulseresponse_01.flac" by pushkin (CC0), https://freesound.org/people/pushkin/sounds/240593/
- "Split Flap Display" by ngruber (CC0), https://freesound.org/people/ngruber/sounds/261244/
- "flipping through pages" by vladnegrila (CC0), https://freesound.org/people/vladnegrila/sounds/339963/
- "Analog Stopwatch Winding" by Kinoton (CC0), https://freesound.org/people/Kinoton/sounds/353108/
- "A relay switch being activated." by bassmosphere (CC0), https://freesound.org/people/bassmosphere/sounds/384698/
- "Shirt Whoosh 2.wav" by saturdaysoundguy (CC0), https://freesound.org/people/saturdaysoundguy/sounds/391447/
- "Drop Stack of Paper-whoomp.wav" by DAVESTALKER (CC0), https://freesound.org/people/DAVESTALKER/sounds/416416/
- "IR Estonia Nordea Hall.wav" by johnnyguitar01 (CC0), https://freesound.org/people/johnnyguitar01/sounds/423803/
- "IR Liverpool Philharmonic Hall.wav" by johnnyguitar01 (CC0), https://freesound.org/people/johnnyguitar01/sounds/423866/
- "Sword_Sounds_01.wav" by N-RAZM (CC0), https://freesound.org/people/N-RAZM/sounds/431222/
- "Jacket/Cloth Rustle 3" by brandondelehoy (CC0), https://freesound.org/people/brandondelehoy/sounds/494789/
- "Lock Unlock Wooden Door" by plumaudio (CC0), https://freesound.org/people/plumaudio/sounds/513819/
- "wood hit" by Ian_G (CC0), https://freesound.org/people/Ian_G/sounds/547414/
- "Tally Counter.WAV" by revdrmr (CC0), https://freesound.org/people/revdrmr/sounds/664698/
- "PaperSheets" by TimOut789 (CC0), https://freesound.org/people/TimOut789/sounds/751868/
