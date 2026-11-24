"""Synthesize the short's original music and ambience as a stereo WAV."""
from array import array
from math import cos, exp, pi, sin
import random
import sys
import wave

rate = 32000
duration = 28
length = duration * rate
left = array("f", [0]) * length
right = array("f", [0]) * length


def note(start, pitch, gain, pan=0, bell=False):
    omega = 2 * pi * (440 * 2 ** ((pitch - 69) / 12)) / rate
    start = round(start * rate)
    for i in range(min(rate * 3, length - start)):
        t = i / rate
        attack = min(1, t / (.008 if bell else .034))
        decay = exp(-t * (2.9 if bell else 1.95))
        partial = sin(omega * i)
        partial += (.42 if bell else .27) * sin(omega * (2.01 if bell else 2) * i) * exp(-t * 3)
        partial += .11 * sin(omega * (3.99 if bell else 3) * i) * exp(-t * 6)
        sample = partial * gain * attack * decay
        left[start + i] += sample * (1 - pan * .46)
        right[start + i] += sample * (1 + pan * .46)
        delay = 4232
        if start + i + delay < length:
            left[start + i + delay] += sample * (.15 + pan * .07)
            right[start + i + delay] += sample * (.12 - pan * .05)


chords = [
    (.35, [50,57,65]), (3.8,[46,53,62]), (6.8,[48,55,64]), (9.3,[53,60,69]),
    (12.05,[45,52,60]), (15.4,[46,53,62]), (17.3,[50,57,64]),
    (20.25,[53,60,69]), (23.1,[46,53,65]), (25.3,[53,60,65])
]
for start, notes in chords:
    for i, pitch in enumerate(notes):
        note(start + i * .20, pitch, .047 if i == 0 else .034, i * .23 - .30)

melody = [
    (1.1,74),(1.85,72),(2.4,69),(3.05,65),(4.65,69),(5.38,72),(6.14,74),
    (7.1,76),(8.18,74),(8.7,77),(9.25,79),(9.78,81),(10.4,77),(11.02,74),
    (13.4,69),(14.65,65),(16.65,67),(17.4,69),(18.18,72),(19,74),(19.68,76),
    (20.45,77),(21.24,76),(22,72),(22.72,69),(23.65,70),(24.36,72),(25.35,77)
]
for i, (start, pitch) in enumerate(melody):
    note(start, pitch, .064 if not 11.75 < start < 16.65 else .037,
         .18 * cos(i), bell=start < 11.75 or start >= 16.65)

rng = random.Random(420)
ambience = array("h")
wind = 0
for i in range(length):
    t = i / rate
    noise = rng.uniform(-1, 1)
    wind = wind * .987 + noise * .013
    rain = max(0, min(1, (t - 11.75) * 2.6, (20.25 - t) * 2.6))
    fade = min(1, t * 5, (duration - t) / 1.35)
    background = (wind * .050 + .030 * noise * rain) * fade
    for channel in (left, right):
        value = max(-1, min(1, channel[i] * fade + background))
        ambience.append(round(value * 32767))
if sys.byteorder != "little":
    ambience.byteswap()
with wave.open(sys.argv[1], "wb") as output:
    output.setparams((2, 2, rate, 0, "NONE", "not compressed"))
    output.writeframes(ambience.tobytes())
