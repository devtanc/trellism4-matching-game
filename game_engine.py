import random

[
	PLAYING,
	HALFWAY,
	NEAR_WIN,
	WIN,
	CORRECT
] = range(5)

# LED COLORS
OFF = 0x000000
RED = 0xFF0000
YELLOW = 0xFFFF00
GREEN = 0x00FF00
CYAN = 0x00FFFF
BLUE = 0x0000FF
VIOLET = 0xFF00FF
WHITE = 0xFFFFFF

# PIXEL DEFAULT KEYS
[
	P_MATCHED,
	P_COLOR,
	P_PREV_TIME,
	P_BLINKS,
	P_BLINK_DELAY,
	P_BLINK_ON_COLOR,
	P_BLINK_OFF_COLOR,
	P_HOLDABLE,
	P_HOLD_DELAY,
	P_HOLD_ACTION,
	P_PREV_HOLD_TIME,
	P_HOLD_TRIGGERED
] = range(12)

# PIXEL HELD ACTIONS
[
	S_TOGGLE_COLORS,
] = range(1)

CORRECT_BLINKS = 2
INCORRECT_BLINKS = 1

PIXEL_INIT = {
	P_PREV_TIME: -1,
	P_BLINKS: 0,
	P_BLINK_DELAY: 0.05,
	P_BLINK_ON_COLOR: WHITE,
	P_BLINK_OFF_COLOR: OFF,
}

HOLDABLE_INIT = {
	P_HOLDABLE: True,
	P_PREV_HOLD_TIME: -1,
	P_HOLD_DELAY: 0.3,
	P_HOLD_ACTION: None,
	P_HOLD_TRIGGERED: False
}

def pop_random_from_list(list):
	index = random.randrange(0, len(list))
	return list.pop(index)

class GameEngine:
	PIXELS_X = 8
	PIXELS_Y = 4
	NUMBER_OF_PIXELS = PIXELS_X * PIXELS_Y
	WINNING_PAIRS = NUMBER_OF_PIXELS / 2

	COLORS = [RED, YELLOW, GREEN, CYAN, BLUE, VIOLET]

	state = None
	pixels = {}
	selected = None
	found_pairs = 0
	is_key_held = False
	show_colors = False
	last_pressed_keys = set()
	last_held_keys = set()
	now = -1

	def __init__(self):
		if self.NUMBER_OF_PIXELS % 2 == 1:
			raise RuntimeError('Must be an even number of pixels')
		self.initialize_grid()
		
	def initialize_grid(self):
		coords = [(x, y) for x in range(self.PIXELS_X) for y in range (self.PIXELS_Y)]
		while coords:
			pixel = {
				P_MATCHED: False,
				P_COLOR: random.choice(self.COLORS)
			}

			self.__reset_pixel(pop_random_from_list(coords), pixel)
			self.__reset_pixel(pop_random_from_list(coords), pixel)
		self.__reset_held_pixel((0,0))
		self.pixels[(0,0)][P_HOLD_ACTION] = S_TOGGLE_COLORS

	def set_time(self, now):
		self.now = now

	def toggle_show_colors(self):
		self.show_colors = not self.show_colors

	def __reset_held_pixel(self, key):
		if P_HOLD_ACTION in self.pixels[key] and self.pixels[key][P_HOLD_ACTION] is not None:
			state = self.pixels[key][P_HOLD_ACTION]
			self.pixels[key].update(HOLDABLE_INIT)
			self.pixels[key][P_HOLD_ACTION] = state
		else:
			self.pixels[key].update(HOLDABLE_INIT)

	def __reset_pixel(self, key, values = None):
		if key is None:
			return
		if key not in self.pixels:
			self.pixels[key] = {}
		
		self.pixels[key].update(PIXEL_INIT)

		if values is not None:
			self.pixels[key].update(values)
		
	def blink_pixel(self, key, times):
		print("BLINKING:", key, times)
		self.pixels[key][P_BLINKS] = times

	def blink_pixels(self, keys, times):
		for key in keys:
			self.pixels[key][P_BLINKS] = times

	def coord_to_index(self, coord):
		x, y = coord
		return y * self.PIXELS_X + x

	def handle_selection(self, key, blinks = CORRECT_BLINKS):
		if key is None:
			return
		self.blink_pixel(key, blinks)

	def determine_current_state(self):
		if self.found_pairs < self.WINNING_PAIRS / 2:
				return PLAYING
		elif self.found_pairs < self.WINNING_PAIRS / 4 * 3:
				return HALFWAY
		elif self.found_pairs < self.WINNING_PAIRS:
				return NEAR_WIN
		elif self.found_pairs >= self.WINNING_PAIRS:
				return WIN

	def process_blinks(self, pixel_state):
		updates = []
		for pixel_key in self.pixels:
			pixel = self.pixels[pixel_key]
			if pixel[P_BLINKS] == 0:
				continue

			# Is it even time to process this pixel yet?
			if self.now >= pixel[P_PREV_TIME] + pixel[P_BLINK_DELAY]:
				# if off, turn it on and reset the delay
				if pixel_state[pixel_key] == (0,0,0):
					updates.append((pixel_key, pixel[P_BLINK_ON_COLOR] if not self.show_colors else pixel[P_COLOR]))
					pixel[P_PREV_TIME] = self.now
				# if on, turn it off, reset the delay, and decrease necessary blinks
				else:
					updates.append((pixel_key, pixel[P_BLINK_OFF_COLOR]))
					pixel[P_PREV_TIME] = self.now
					if pixel[P_BLINKS] > 1:
						pixel[P_BLINKS] -= 1
					else:
						self.__reset_pixel(pixel_key)
		return updates

	def process_keys(self, pressed_keys):
		# Get newly pressed keys
		new_presses = pressed_keys - self.last_pressed_keys
		self.last_pressed_keys = pressed_keys

		# Check for held keys
		held_keys = pressed_keys & self.last_pressed_keys

		#  Reset released keys here
		keys_to_unhold = self.last_held_keys - held_keys
		for key in keys_to_unhold:
			if not P_HOLDABLE in self.pixels[key]:
				continue
			if not self.pixels[key][P_HOLD_TRIGGERED]:
				new_presses.add(key)
			self.__reset_held_pixel(key)
		self.last_held_keys = held_keys

		# Process still-held keys
		if held_keys:
			for key in held_keys:
				pixel = self.pixels[key]
				if not P_HOLDABLE in self.pixels[key]:
					continue
				# Only process as a holdable key
				new_presses.discard(key)
				if pixel[P_PREV_HOLD_TIME] is -1:
					pixel[P_PREV_HOLD_TIME] = self.now
					continue
				if self.now >= pixel[P_PREV_HOLD_TIME] + pixel[P_HOLD_DELAY]:
					# This has now been held long enough to trigger
					if not pixel[P_HOLD_TRIGGERED]:
						self.handle_pressed_state(pixel[P_HOLD_ACTION])
						pixel[P_HOLD_TRIGGERED] = True
						self.blink_pixel(key, 1)
		if new_presses:
			# for key in new_presses:
			# 	if P_HOLDABLE in self.pixels[key] and self.pixels[key][P_HOLDABLE]:
			# 		new_presses.remove(key)
			return list(new_presses)[0]

	def handle_pressed_state(self, state):
		if state == S_TOGGLE_COLORS:
			self.toggle_show_colors()

# engine = GameEngine()

# for key in sorted(engine.pixels):
# 	print(key, engine.pixels[key])