#!/usr/bin/env python3
"""原創背景音樂（程式合成，沒有版權問題）：輕快的木琴分解和弦＋輕節拍。
用法：python3 make-bgm.py <秒數> <輸出.wav>"""
import sys, wave
import numpy as np

SR = 44100
dur = float(sys.argv[1]); out = sys.argv[2]
bpm = 112; beat = 60 / bpm
n = int(SR * dur)
L = np.zeros(n); R = np.zeros(n)

def note(freq, t0, length, amp, pan=0.5, decay=6.0):
    i0 = int(t0 * SR); m = int(length * SR)
    if i0 >= n: return
    m = min(m, n - i0)
    t = np.arange(m) / SR
    env = np.exp(-decay * t) * np.minimum(1, t / 0.004)
    # 木琴感：基音＋4 倍泛音（很快消失）
    w = np.sin(2*np.pi*freq*t) + 0.25*np.sin(2*np.pi*freq*4*t)*np.exp(-30*t)
    s = amp * env * w
    L[i0:i0+m] += s * (1-pan); R[i0:i0+m] += s * pan

def hz(midi): return 440 * 2 ** ((midi - 69) / 12)

# C - Am - F - G，每個和弦一小節
chords = [[60, 64, 67, 72], [57, 60, 64, 69], [53, 57, 60, 65], [55, 59, 62, 67]]
bass = [48, 45, 41, 43]
pattern = [0, 2, 1, 3, 2, 1, 3, 2]  # 八分音符分解和弦
bar = 4 * beat
k = 0; t = 0.0
rng = np.random.default_rng(7)
while t < dur:
    c = chords[k % 4]
    for j, p in enumerate(pattern):
        note(hz(c[p] + 12), t + j * beat / 2, 0.9, 0.16, pan=0.35 + 0.3 * (j % 2), decay=5.5)
    note(hz(bass[k % 4]), t, bar, 0.22, pan=0.5, decay=1.6)
    for b in range(4):
        tb = t + b * beat
        # 輕的大鼓（第 1、3 拍）
        if b in (0, 2):
            i0 = int(tb * SR); m = min(int(0.25 * SR), max(0, n - i0))
            if m > 0:
                tt = np.arange(m) / SR
                kick = 0.35 * np.sin(2*np.pi*(55 + 70*np.exp(-25*tt))*tt) * np.exp(-14*tt)
                L[i0:i0+m] += kick; R[i0:i0+m] += kick
        # 沙鈴（反拍）
        i0 = int((tb + beat / 2) * SR); m = min(int(0.06 * SR), max(0, n - i0))
        if m > 0:
            tt = np.arange(m) / SR
            sh = rng.standard_normal(m); sh = np.diff(sh, prepend=0)  # 高頻一點
            sh = 0.05 * sh * np.exp(-60 * tt)
            L[i0:i0+m] += sh * 0.8; R[i0:i0+m] += sh * 1.2
    t += bar; k += 1

mix = np.stack([L, R], 1)
fade_in, fade_out = int(1.0 * SR), int(2.0 * SR)
mix[:fade_in] *= np.linspace(0, 1, fade_in)[:, None]
mix[-fade_out:] *= np.linspace(1, 0, fade_out)[:, None]
mix /= np.max(np.abs(mix)) + 1e-9
mix *= 0.8
pcm = (mix * 32767).astype(np.int16)
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('ok', out, dur)
