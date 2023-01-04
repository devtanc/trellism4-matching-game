

import time
import rainbow
import audio_engine
import game_engine

WINNING_PAIRS = 16
COLORS = [0xFF0000, 0xFFFF00, 0x00FF00, 0x00FFFF, 0x0000FF, 0xFF00FF]

audio = audio_engine.AudioEngine(state_to_path_relationships={
		game_engine.DEMO: "/opening.wav",
		game_engine.PLAYING: "/playing_1.wav",
		game_engine.HALFWAY: "/playing_2.wav",
		game_engine.NEAR_WIN: "/playing_3.wav",
		game_engine.WIN: "/complete.wav",
		game_engine.SETTINGS: "/settings.wav",
		game_engine.CORRECT: "/correct.wav",
	}, 
	root_audio_path='/sounds')

audio_out = audio.initialize_audio()
mixer = audio.initialize_mixer()
audio_out.play(mixer)

game = game_engine.GameEngine(rotation=0, audio_mixer=mixer, audio_engine=audio)
game.pixels.brightness = 0.2
game.pixels.fill(0)

game.pixels.fill(0)

while True:
	now = time.monotonic()
	game.set_time(now)
	pressed_key = game.process_keys()
	if game.state is game_engine.SETTINGS:
		game.handle_setting_selection(pressed_key)
	else:
		game.handle_selection(pressed_key)
		game.process_blinks()

	if game.processing_complete:
		audio.handle_audio_for_state(state=game.state, mixer=mixer)
		if game.state == game_engine.WIN:
			t_end = time.time() + 4
			while time.time() < t_end:
				rainbow.splash(game)
			game.reset_all()
