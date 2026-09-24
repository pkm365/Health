"""生成卡通视频的轻快背景音乐（C-G-Am-F 和弦进行 + 琶音旋律），输出 WAV。

用法：python3 music.py 输出.wav 时长秒数
"""
import sys
import wave

import numpy as np

SR = 44100
BPM = 116
BEAT = 60 / BPM


def note_freq(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def tone(freq, dur, kind="sine", attack=0.01, release=0.15):
    t = np.arange(int(SR * dur)) / SR
    if kind == "pluck":
        # 正弦 + 少量泛音，指数衰减，类似拨弦/木琴
        wave_ = np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(4 * np.pi * freq * t) + 0.1 * np.sin(6 * np.pi * freq * t)
        env = np.exp(-t * 6)
    elif kind == "tri":
        wave_ = 2 / np.pi * np.arcsin(np.sin(2 * np.pi * freq * t))
        env = np.exp(-t * 2.5)
    else:
        wave_ = np.sin(2 * np.pi * freq * t)
        env = np.ones_like(t)
    a = max(1, int(SR * attack))
    r = max(1, int(SR * release))
    env[:a] *= np.linspace(0, 1, a)
    env[-r:] *= np.linspace(1, 0, r)
    return wave_ * env


def add(buf, sig, start):
    i = int(start * SR)
    j = min(len(buf), i + len(sig))
    if i < len(buf):
        buf[i:j] += sig[: j - i]


def main(out, seconds):
    buf = np.zeros(int(SR * (seconds + 1)))
    # C, G, Am, F（MIDI 音高）
    chords = [[60, 64, 67], [55, 59, 62], [57, 60, 64], [53, 57, 60]]
    arp = [0, 1, 2, 1, 0, 2, 1, 2]
    bar = 4 * BEAT
    n_bars = int(seconds / bar) + 1
    for b in range(n_bars):
        chord = chords[b % 4]
        t0 = b * bar
        # 低音
        add(buf, 0.22 * tone(note_freq(chord[0] - 24), BEAT * 1.8, "tri"), t0)
        add(buf, 0.18 * tone(note_freq(chord[0] - 24), BEAT * 1.8, "tri"), t0 + 2 * BEAT)
        # 柔和的和弦铺底
        for n in chord:
            add(buf, 0.035 * tone(note_freq(n), bar, "sine", attack=0.2, release=0.4), t0)
        # 八分音符琶音，高一个八度
        for k, idx in enumerate(arp):
            n = chord[idx] + 12
            if b % 2 == 1 and k == 7:
                n += 2  # 每两小节加一个经过音
            add(buf, 0.12 * tone(note_freq(n), BEAT * 0.9, "pluck"), t0 + k * BEAT / 2)
        # 轻轻的节拍
        for k in range(4):
            click = np.random.default_rng(b * 4 + k).standard_normal(int(SR * 0.03)) * np.linspace(1, 0, int(SR * 0.03))
            add(buf, 0.03 * click, t0 + k * BEAT + BEAT / 2)

    buf = buf[: int(SR * seconds)]
    fade = int(SR * 1.5)
    buf[:int(SR * 0.3)] *= np.linspace(0, 1, int(SR * 0.3))
    buf[-fade:] *= np.linspace(1, 0, fade)
    buf = buf / np.max(np.abs(buf)) * 0.7
    data = (buf * 32767).astype("<i2")
    with wave.open(out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


if __name__ == "__main__":
    main(sys.argv[1], float(sys.argv[2]))
