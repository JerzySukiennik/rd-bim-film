/* Analog-style synth voices for the R&D BIM film score: PolyBLEP oscillators, saturating ladder filter, 2x oversampling. */
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define SR 48000.0
#define OS 2
#define FS (SR * OS)
#define PI 3.14159265358979323846

typedef struct { char patch[16]; double t, dur, midi, vel, cut, env, pan; } Note;

static unsigned long long rng = 0x9E3779B97F4A7C15ULL;
static double frand(void) { rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17; return (double)(rng >> 11) / 9007199254740992.0; }

static inline double ftanh(double x) {
    if (x > 4.0) return 1.0; if (x < -4.0) return -1.0;
    double x2 = x * x; return x * (27.0 + x2) / (27.0 + 9.0 * x2);
}
static inline double blep(double t, double dt) {
    if (t < dt) { t /= dt; return t + t - t * t - 1.0; }
    if (t > 1.0 - dt) { t = (t - 1.0) / dt; return t * t + t + t + 1.0; }
    return 0.0;
}
static inline double saw(double ph, double dt) { return 2.0 * ph - 1.0 - blep(ph, dt); }
static inline double sqr(double ph, double dt, double pw) {
    double v = ph < pw ? 1.0 : -1.0;
    v += blep(ph, dt);
    double p2 = ph - pw; if (p2 < 0) p2 += 1.0;
    v -= blep(p2, dt);
    return v;
}

typedef struct { double y1, y2, y3, y4; } Ladder;
static inline double ladder(Ladder *l, double in, double fc, double res, double drive) {
    if (fc > FS * 0.45) fc = FS * 0.45; if (fc < 20) fc = 20;
    double g = 1.0 - exp(-2.0 * PI * fc / FS);
    double x = ftanh(drive * in - 4.0 * res * l->y4);
    l->y1 += g * (x - ftanh(l->y1));
    l->y2 += g * (ftanh(l->y1) - ftanh(l->y2));
    l->y3 += g * (ftanh(l->y2) - ftanh(l->y3));
    l->y4 += g * (ftanh(l->y3) - ftanh(l->y4));
    return l->y4 * (1.0 + res * 1.6);
}

static double env_adsr(double t, double gate, double a, double d, double s, double r) {
    double v;
    if (t < a) v = t / a;
    else if (t < a + d) v = 1.0 - (1.0 - s) * (1.0 - exp(-5.0 * (t - a) / d)) / (1.0 - exp(-5.0));
    else v = s;
    if (t > gate) {
        double tg = gate, vg;
        if (tg < a) vg = tg / a;
        else if (tg < a + d) vg = 1.0 - (1.0 - s) * (1.0 - exp(-5.0 * (tg - a) / d)) / (1.0 - exp(-5.0));
        else vg = s;
        v = vg * exp(-(t - gate) / (r / 4.6));
    }
    return v;
}

static double hz(double m) { return 440.0 * pow(2.0, (m - 69.0) / 12.0); }

static void render(Note *n, float *L, float *R, long total) {
    int uni = 1; double det[7] = {0}, upan[7] = {0};
    double A = 0.002, D = 0.1, S = 0.0, Rl = 0.03, fa = 0.001, fd = 0.09, fs_ = 0.0, res = 0.25, drive = 1.6, subl = 0.0, tail = 0.05;
    int kind = 0;
    if (!strcmp(n->patch, "bass")) { uni = 2; det[0] = -5; det[1] = 5; upan[0] = -0.35; upan[1] = 0.35; A = 0.0015; D = 0.25; S = 0.75; Rl = 0.035; fa = 0.001; fd = 0.11; fs_ = 0.0; res = 0.32; drive = 1.8; subl = 0.45; tail = 0.06; }
    else if (!strcmp(n->patch, "brass")) { uni = 6; double dd[6] = {-16, -9, -3, 3, 9, 16}; for (int i = 0; i < 6; i++) { det[i] = dd[i]; upan[i] = (i - 2.5) / 2.5 * 0.8; } A = 0.07; D = 0.6; S = 0.8; Rl = 0.7; fa = 0.14; fd = 1.1; fs_ = 0.35; res = 0.12; drive = 1.2; tail = 1.4; kind = 1; }
    else if (!strcmp(n->patch, "pluck")) { uni = 2; det[0] = -7; det[1] = 7; upan[0] = -0.6; upan[1] = 0.6; A = 0.001; D = 0.35; S = 0.0; Rl = 0.08; fa = 0.0005; fd = 0.16; fs_ = 0.0; res = 0.38; drive = 1.4; tail = 0.45; kind = 2; }
    else if (!strcmp(n->patch, "sub")) { kind = 3; A = 0.004; Rl = 0.25; tail = 3.0 * n->dur; }
    else if (!strcmp(n->patch, "drone")) { uni = 4; double dd[4] = {-8, -3, 3, 8}; for (int i = 0; i < 4; i++) { det[i] = dd[i]; upan[i] = (i - 1.5) / 1.5 * 0.9; } A = 1.2; D = 1.0; S = 1.0; Rl = 1.5; fa = 1.6; fd = 2.0; fs_ = 0.6; res = 0.18; drive = 1.1; tail = 2.5; kind = 1; }
    long i0 = (long)(n->t * FS), len = (long)((n->dur + tail) * FS);
    double ph[8], dr[8], drv[8];
    for (int u = 0; u < 8; u++) { ph[u] = frand(); dr[u] = 0; drv[u] = 0; }
    double subph = 0;
    Ladder fl = {0}, fr = {0};
    double base = n->cut, amt = n->env;
    double vib = 0, vibph = frand();
    double hpL = 0, hpR = 0;
    for (long k = 0; k < len; k++) {
        long idx = i0 + k; if (idx < 0) continue; if (idx >= total) break;
        double t = (double)k / FS;
        double ae = env_adsr(t, n->dur, A, D, S, Rl);
        if (t > n->dur + tail - 0.005) ae *= fmax(0.0, (n->dur + tail - t) / 0.005);
        double fe = env_adsr(t, n->dur, fa, fd, fs_, Rl * 1.5);
        double sl = 0, sr = 0;
        if (kind == 3) {
            double glide = 12.0 * exp(-t / 0.05) * (n->env > 0 ? 1 : 0);
            subph += hz(n->midi + glide) / FS; if (subph >= 1) subph -= 1;
            double s = sin(2 * PI * subph); s = ftanh(1.6 * s) / ftanh(1.6);
            double e = (t < A ? t / A : 1.0) * exp(-fmax(0.0, t - A) / fmax(0.02, n->dur));
            double left = n->dur + tail - t; if (left < 0.15) e *= left / 0.15;
            sl = sr = s * e * n->vel;
            L[idx] += (float)(sl * (1 - n->pan)); R[idx] += (float)(sr * (1 + n->pan));
            continue;
        }
        if (kind == 1 && t > 0.35) { vibph += 4.8 / FS; vib = sin(2 * PI * vibph) * 5.0 * fmin(1.0, (t - 0.35) / 0.6); }
        for (int u = 0; u < uni; u++) {
            drv[u] += (frand() - 0.5) * 0.02; drv[u] *= 0.9995; dr[u] += (drv[u] - dr[u]) * 0.001;
            double f = hz(n->midi + (det[u] + vib + dr[u] * 30.0) / 100.0);
            double dt = f / FS;
            ph[u] += dt; if (ph[u] >= 1.0) ph[u] -= 1.0;
            double v = (kind == 2 && u == 1) ? sqr(ph[u], dt, 0.5) * 0.7 : saw(ph[u], dt);
            double pl = 0.5 * (1.0 - upan[u]), pr = 0.5 * (1.0 + upan[u]);
            sl += v * pl; sr += v * pr;
        }
        sl /= sqrt((double)uni) * 0.75; sr /= sqrt((double)uni) * 0.75;
        if (subl > 0) {
            double f = hz(n->midi - 12.0); double dt = f / FS;
            subph += dt; if (subph >= 1.0) subph -= 1.0;
            double s = sqr(subph, dt, 0.5) * subl; sl += s; sr += s;
        }
        double fc = base * pow(2.0, amt * fe) * (0.6 + 0.4 * n->vel);
        double ol = ladder(&fl, sl * 0.5, fc, res, drive);
        double orr = ladder(&fr, sr * 0.5, fc * 1.01, res, drive);
        hpL += 0.0015 * (ol - hpL); hpR += 0.0015 * (orr - hpR);
        ol -= hpL; orr -= hpR;
        double g = ae * n->vel;
        double pL = sqrt(0.5 * (1.0 - n->pan)), pR = sqrt(0.5 * (1.0 + n->pan));
        L[idx] += (float)(ol * g * pL * 1.414);
        R[idx] += (float)(orr * g * pR * 1.414);
    }
}

int main(int argc, char **argv) {
    if (argc < 4) { fprintf(stderr, "usage: synth notes.txt out.f32 seconds (writes 96 kHz stereo float32)\n"); return 1; }
    FILE *f = fopen(argv[1], "r"); if (!f) return 1;
    double secs = atof(argv[3]); long total = (long)(secs * FS);
    float *L = calloc(total, sizeof(float)), *R = calloc(total, sizeof(float));
    Note n; char line[512]; int count = 0;
    while (fgets(line, sizeof line, f)) {
        if (line[0] == '#' || strlen(line) < 5) continue;
        n.pan = 0;
        int got = sscanf(line, "%15s %lf %lf %lf %lf %lf %lf %lf", n.patch, &n.t, &n.dur, &n.midi, &n.vel, &n.cut, &n.env, &n.pan);
        if (got < 7) continue;
        render(&n, L, R, total); count++;
    }
    fclose(f);
    FILE *o = fopen(argv[2], "wb");
    for (long i = 0; i < total; i++) { fwrite(&L[i], 4, 1, o); fwrite(&R[i], 4, 1, o); }
    fclose(o);
    fprintf(stderr, "rendered %d notes\n", count);
    return 0;
}
