"""
NeoTrellis M4 Express Memory Game

Adafruit invests time and resources providing this open source code.
Please support Adafruit and open source hardware by purchasing
products from Adafruit!

Written by Dave Astels for Adafruit Industries
Copyright (c) 2018 Adafruit Industries
Licensed under the MIT license.

All text above must be included in any redistribution.
"""

# pylint: disable=stop-iteration-return

import time
import random
import rainbow
import audio_engine
import adafruit_trellism4

WINNING_PAIRS = 16
COLORS = [0xFF0000, 0xFFFF00, 0x00FF00, 0x00FFFF, 0x0000FF, 0xFF00FF]

state = audio_engine.DEMO

trellis = adafruit_trellism4.TrellisM4Express(rotation=0)
trellis.pixels.brightness = 0.2
trellis.pixels.fill(0)

demo_mode_enabled = True
pixel_colors = [None] * 32
previously_pressed = set([])
first_pixel = None
key_pressed = None
mixer = None

engine = audio_engine.AudioEngine()
audio = engine.initialize_audio()
mixer = engine.initialize_mixer()
audio.play(mixer)

def index_of(coord):
    x, y = coord
    return y * 8 + x

def assign_colors():
    unassigned = [(x, y) for x in range(8) for y in range(4)]
    while unassigned:
        first_of_pair = random.choice(unassigned)
        unassigned.remove(first_of_pair)
        second_of_pair = random.choice(unassigned)
        unassigned.remove(second_of_pair)
        random_color = random.choice(COLORS)
        pixel_colors[index_of(first_of_pair)] = random_color
        pixel_colors[index_of(second_of_pair)] = random_color

def handle_key(key, _found_pairs, _first_pixel):
    if key is None:
        return _found_pairs, _first_pixel
    key_color = pixel_colors[index_of(key)]
    if key_color is not None:
        trellis.pixels[key] = pixel_colors[index_of(key)]
        time.sleep(0.4)
        if _first_pixel and _first_pixel != key:
            if key_color == pixel_colors[index_of(_first_pixel)]:
                pixel_colors[index_of(_first_pixel)] = None
                pixel_colors[index_of(key)] = None
                if not demo_mode_enabled:
                    print("Match found!!")
                    engine.play_correct_sound(mixer)
                for _ in range(2):
                    trellis.pixels[_first_pixel] = 0xFFFFFF
                    trellis.pixels[key] = 0xFFFFFF
                    time.sleep(0.05)
                    trellis.pixels[_first_pixel] = 0x000000
                    trellis.pixels[key] = 0x000000
                    time.sleep(0.05)
                trellis.pixels[_first_pixel] = 0x444444
                trellis.pixels[key] = 0x444444
                return _found_pairs + 1, None
            else:
                trellis.pixels[_first_pixel] = 0x000000
                trellis.pixels[key] = 0x000000
                return _found_pairs, None
        else:
            return _found_pairs, key
    return _found_pairs, None

def check_for_key(last_pressed):
    now_pressed = set(trellis.pressed_keys)
    new_presses = now_pressed - last_pressed
    if new_presses:
        return now_pressed, list(new_presses)[0]
    return now_pressed, None

def determine_current_state(found_pairs):
    if demo_mode_enabled:
        return audio_engine.DEMO
    elif found_pairs < WINNING_PAIRS / 2:
        return audio_engine.PLAYING
    elif found_pairs < WINNING_PAIRS / 4 * 3:
        return audio_engine.URGENT
    elif found_pairs < WINNING_PAIRS:
        return audio_engine.CRAZY
    elif found_pairs >= WINNING_PAIRS:
        return audio_engine.COMPLETE

while True:
    trellis.pixels.fill(0x000000)
    assign_colors()
    found_pairs = 0
    first_pixel = None
    remaining = [(x, y) for x in range(8) for y in range(4)]

    while found_pairs < WINNING_PAIRS:
        state = determine_current_state(found_pairs)
        if engine.get_state() != state:
            engine.handle_audio_for_state(state, mixer)

        if demo_mode_enabled:
            previously_pressed, key_pressed = check_for_key(previously_pressed)
            if key_pressed:
                demo_mode_enabled = False
                break
            first = random.choice(remaining)
            remaining.remove(first)
            found_pairs, first_pixel = handle_key(first, found_pairs, first_pixel)
            previously_pressed, key_pressed = check_for_key(previously_pressed)
            if key_pressed:
                demo_mode_enabled = False
                break
            c = pixel_colors[index_of(first)]
            match = random.choice([x for x in remaining if pixel_colors[index_of(x)] == c])
            found_pairs, first_pixel = handle_key(match, found_pairs, first_pixel)
            remaining.remove(match)
        else:
            previously_pressed, key_pressed = check_for_key(previously_pressed)
            found_pairs, first_pixel = handle_key(key_pressed, found_pairs, first_pixel)
    if found_pairs >= WINNING_PAIRS:
        state = determine_current_state(found_pairs)
        if engine.get_state() != state and not demo_mode_enabled:
            engine.handle_audio_for_state(state, mixer)
            print("%d : %d" % (engine.get_state(), state))

        t_end = time.time() + 4
        while time.time() < t_end:
            rainbow.splash(trellis)
