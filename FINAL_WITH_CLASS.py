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
import board
import random
import audioio
import rainbow
import audiocore
import audiomixer
import adafruit_trellism4

WINNING_PAIRS = 16
COLORS = [0xFF0000, 0xFFFF00, 0x00FF00, 0x00FFFF, 0x0000FF, 0xFF00FF]

DEMO, PLAYING, URGENT, CRAZY, COMPLETE, CORRECT = range(6)
state = DEMO

trellis = adafruit_trellism4.TrellisM4Express(rotation=0)
trellis.pixels.brightness = 0.2
trellis.pixels.fill(0)

demo_mode_enabled = True
pixel_colors = [None] * 32
previously_pressed = set([])
first_pixel = None
key_pressed = None
mixer = None

class AudioEngine:
    root_path = '/sounds'
    paths = {
        DEMO: "/opening.wav",
        PLAYING: "/playing_1.wav",
        URGENT: "/playing_2.wav",
        CRAZY: "/playing_3.wav",
        COMPLETE: "/complete.wav",
        CORRECT: "/correct.wav",
    }
    currently_playing_state = None
    current_bg_audio = None
    correct_audio_file = None
    correct_wav_data = None

    channel_count = None
    bits_per_sample = None
    sample_rate = None

    def __get_path(self, state):
        return self.root_path + self.paths[state]

    def __init__(self):
        self.voices = 2
        with open(self.__get_path(DEMO), 'rb') as file:
            wav = audiocore.WaveFile(file)
            
            self.channel_count = wav.channel_count
            self.bits_per_sample = wav.bits_per_sample
            self.sample_rate = wav.sample_rate

            print('%d channels, %d bits per sample, %d Hz sample rate ' %
                (wav.channel_count, wav.bits_per_sample, wav.sample_rate))

            file.close()

        self.correct_audio_file = open(self.__get_path(CORRECT), 'rb')
        self.correct_wav_data = audiocore.WaveFile(self.correct_audio_file)

    def __del__(self):
        if self.correct_audio_file is not None:
            self.correct_audio_file.close()
            self.correct_audio_file = None
            self.audio.deinit()

    def initialize_audio(self):
        if self.channel_count == 1:
            return audioio.AudioOut(board.A1)
        elif self.channel_count == 2:
            return audioio.AudioOut(board.A1, right_channel=board.A0)
        else:
            raise RuntimeError('Must be mono or stereo waves!')
    
    def initialize_mixer(self):
        return audiomixer.Mixer(voice_count=2,
                        sample_rate=self.sample_rate,
                        channel_count=self.channel_count,
                        bits_per_sample=self.bits_per_sample,
                        samples_signed=True)
    
    def get_state(self):
        if self.currently_playing_state is None:
            return -1

        return self.currently_playing_state

    def stop_playing_sample(self):
        if self.current_bg_audio is None:
            return None
        print("Closing file: " + self.current_bg_audio['path'])
        mixer.stop_voice(self.current_bg_audio['voice'])
        self.current_bg_audio['file'].close()

    def handle_audio_for_state(self, state):
        self.stop_playing_sample()

        voice = 0
        loop = state is not COMPLETE

        path = self.__get_path(state)
        print("Opening file: " + path)

        file = open(path, 'rb')
        wav = audiocore.WaveFile(file)
        mixer.voice[0].level = 0.25
        mixer.play(wav, voice=voice, loop=loop)
        self.currently_playing_state = state
        self.current_bg_audio = {
            'voice': voice,
            'file': file,
            'path': path
        }

    def play_correct_sound(self):
        mixer.play(self.correct_wav_data, voice=1, loop=False)

engine = AudioEngine()
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
                    engine.play_correct_sound()
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
        return DEMO
    elif found_pairs < WINNING_PAIRS / 2:
        return PLAYING
    elif found_pairs < WINNING_PAIRS / 4 * 3:
        return URGENT
    elif found_pairs < WINNING_PAIRS:
        return CRAZY
    elif found_pairs >= WINNING_PAIRS:
        return COMPLETE

while True:
    trellis.pixels.fill(0x000000)
    assign_colors()
    found_pairs = 0
    first_pixel = None
    remaining = [(x, y) for x in range(8) for y in range(4)]

    while found_pairs < WINNING_PAIRS:
        state = determine_current_state(found_pairs)
        if engine.get_state() != state:
            engine.handle_audio_for_state(state)

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
            engine.handle_audio_for_state(state)
            print("%d : %d" % (engine.get_state(), state))

        t_end = time.time() + 4
        while time.time() < t_end:
            rainbow.splash(trellis)
