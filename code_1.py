

# pylint: disable=stop-iteration-return

import time
import random
import rainbow
import audio_engine
import game_engine

WINNING_PAIRS = 16
COLORS = [0xFF0000, 0xFFFF00, 0x00FF00, 0x00FFFF, 0x0000FF, 0xFF00FF]

game = game_engine.GameEngine(rotation=0)
game.pixels.brightness = 0.2
game.pixels.fill(0)

demo_mode_enabled = True
pixel_colors = [None] * 32
previously_pressed = set([])
first_pixel = None
key_pressed = None
mixer = None

audio = audio_engine.AudioEngine(state_to_path_relationships={
		game_engine.DEMO: "/opening.wav",
		game_engine.PLAYING: "/playing_1.wav",
		game_engine.HALFWAY: "/playing_2.wav",
		game_engine.NEAR_WIN: "/playing_3.wav",
		game_engine.WIN: "/complete.wav",
		game_engine.CORRECT: "/correct.wav",
	}, 
	root_audio_path='/sounds')

audio_out = audio.initialize_audio()
mixer = audio.initialize_mixer()
audio_out.play(mixer)

# def handle_key(key, _found_pairs, _first_pixel):
#	 if key is None:
#		 return _found_pairs, _first_pixel
#	 key_color = pixel_colors[index_of(key)]
#	 if key_color is not None:
#		 trellis.pixels[key] = pixel_colors[index_of(key)]
#		 time.sleep(0.4)
#		 if _first_pixel and _first_pixel != key:
#			 if key_color == pixel_colors[index_of(_first_pixel)]:
#				 pixel_colors[index_of(_first_pixel)] = None
#				 pixel_colors[index_of(key)] = None
#				 if not demo_mode_enabled:
#					 print("Match found!!")
#					 audio.play_correct_sound(mixer)
#				 for _ in range(2):
#					 trellis.pixels[_first_pixel] = 0xFFFFFF
#					 trellis.pixels[key] = 0xFFFFFF
#					 time.sleep(0.05)
#					 trellis.pixels[_first_pixel] = 0x000000
#					 trellis.pixels[key] = 0x000000
#					 time.sleep(0.05)
#				 trellis.pixels[_first_pixel] = 0x444444
#				 trellis.pixels[key] = 0x444444
#				 return _found_pairs + 1, None
#			 else:
#				 trellis.pixels[_first_pixel] = 0x000000
#				 trellis.pixels[key] = 0x000000
#				 return _found_pairs, None
#		 else:
#			 return _found_pairs, key
#	 return _found_pairs, None

game.pixels.fill(0)

while True:
	now = time.monotonic()
	game.set_time(now)
	game.handle_selection(game.process_keys())
	audio.handle_audio_for_state(state=game.state, mixer=mixer)
	game.process_blinks()

	if game.state == game_engine.WIN and game.processing_complete:
		t_end = time.time() + 4
		while time.time() < t_end:
			rainbow.splash(game)
		game.reset_all()

	# remaining = [(x, y) for x in range(8) for y in range(4)]

	# while found_pairs < WINNING_PAIRS:
	# 	 state = determine_current_state(found_pairs)
	# 	 if audio.get_state() != state:
	# 		 audio.handle_audio_for_state(state, mixer)

	# 	 if demo_mode_enabled:
	# 		 previously_pressed, key_pressed = check_for_key(previously_pressed)
	# 		 if key_pressed:
	# 			 demo_mode_enabled = False
	# 			 break
	# 		 first = random.choice(remaining)
	# 		 remaining.remove(first)
	# 		 found_pairs, first_pixel = handle_key(first, found_pairs, first_pixel)
	# 		 previously_pressed, key_pressed = check_for_key(previously_pressed)
	# 		 if key_pressed:
	# 			 demo_mode_enabled = False
	# 			 break
	# 		 c = pixel_colors[index_of(first)]
	# 		 match = random.choice([x for x in remaining if pixel_colors[index_of(x)] == c])
	# 		 found_pairs, first_pixel = handle_key(match, found_pairs, first_pixel)
	# 		 remaining.remove(match)
	# 	 else:
	# 		 previously_pressed, key_pressed = check_for_key(previously_pressed)
	# 		 found_pairs, first_pixel = handle_key(key_pressed, found_pairs, first_pixel)
	# if found_pairs >= WINNING_PAIRS:
	# 	 state = determine_current_state(found_pairs)
	# 	 if audio.get_state() != state and not demo_mode_enabled:
	# 		 audio.handle_audio_for_state(state, mixer)
	# 		 print("%d : %d" % (audio.get_state(), state))

	
