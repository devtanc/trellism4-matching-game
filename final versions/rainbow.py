import time

def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        return 0, 0, 0
    if pos < 85:
        return int(255 - pos*3), int(pos*3), 0
    if pos < 170:
        pos -= 85
        return 0, int(255 - pos*3), int(pos*3)
    pos -= 170
    return int(pos * 3), 0, int(255 - (pos*3))

def cycle_sequence(seq):
    while True:
        for elem in seq:
            yield elem

def rainbow_lamp(seq, trellis):
    g = cycle_sequence(seq)
    while True:
        trellis.pixels.fill(wheel(next(g)))
        yield

def splash(trellis):
    rainbow = rainbow_lamp(range(0, 256, 8), trellis)
    for _ in range(64):
        next(rainbow)
        time.sleep(0.005)