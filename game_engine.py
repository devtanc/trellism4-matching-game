import random
import adafruit_trellism4
from logger_builder import logger

[
	DEMO,
	PLAYING,
	HALFWAY,
	NEAR_WIN,
	WIN,
	CORRECT
] = range(6)

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
	P_PREV_BLINK_TIME,
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

CORRECT_BLINKS = 3

PIXEL_INIT = {
	P_MATCHED: False
}

PIXEL_BLINK_INIT = {
	P_PREV_BLINK_TIME: -1,
	P_BLINKS: 0,
	P_BLINK_DELAY: 0.1,
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

class GameEngine(adafruit_trellism4.TrellisM4Express):
	PIXELS_X = 8
	PIXELS_Y = 4
	NUMBER_OF_PIXELS = PIXELS_X * PIXELS_Y
	WINNING_PAIRS = NUMBER_OF_PIXELS / 2

	COLORS = [RED, YELLOW, GREEN, CYAN, BLUE, VIOLET]

	state = DEMO
	trellis = None
	pixel_meta = {}
	selected = None
	found_pairs = 0
	show_colors = False
	processing_complete = False
	last_pressed_keys = set()
	last_held_keys = set()
	now = -1

	def __init__(self, rotation):
		super().__init__(rotation=rotation)
		if self.NUMBER_OF_PIXELS % 2 == 1:
			raise RuntimeError('Must be an even number of pixels')
		self.initialize_grid()
		logger.info("game engine initialized")
		
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
		self.pixel_meta[(0,0)][P_HOLD_ACTION] = S_TOGGLE_COLORS

	def set_time(self, now):
		self.now = now

	def toggle_show_colors(self):
		self.show_colors = not self.show_colors
		logger.info("show_colors: %s", self.show_colors)

	def __reset_held_pixel(self, key, values = None):
		self.pixel_meta[key].update(HOLDABLE_INIT)
		
		if values is not None:
			self.pixel_meta[key].update(values)
	
	def __reset_blink_values(self, key):
		if key is None:
			return

		self.pixel_meta[key].update(PIXEL_BLINK_INIT)
		if self.pixel_meta[key][P_MATCHED]:
			self.pixels[key] = WHITE

	def __reset_pixel(self, key, values = None):
		if key is None:
			return
		if key not in self.pixel_meta:
			self.pixel_meta[key] = {}
		
		self.pixel_meta[key].update(PIXEL_INIT)
		self.pixel_meta[key].update(PIXEL_BLINK_INIT)

		if values is not None:
			self.pixel_meta[key].update(values)
	
	def reset_all(self):
		self.initialize_grid()
		self.state = DEMO
		self.pixels.fill(0)
		self.found_pairs = 0
		self.selected = None
		self.last_pressed_keys = set()
		self.last_held_keys = set()
		self.now = -1
		
	def blink_pixel(self, key, times, speed = PIXEL_BLINK_INIT[P_BLINK_DELAY]):
		logger.info("Blinking key %s %s times with %ss delay", key, times, speed)
		# Make sure it's off before blinking
		self.pixels[key] = OFF
		self.pixel_meta[key][P_BLINK_DELAY] = speed
		self.pixel_meta[key][P_BLINKS] = times

	def blink_pixels(self, keys, times, speed = PIXEL_BLINK_INIT[P_BLINK_DELAY]):
		for key in keys:
			self.blink_pixel(key, times, speed)

	def coord_to_index(self, coord):
		x, y = coord
		return y * self.PIXELS_X + x

	def handle_selection(self, key, blinks = CORRECT_BLINKS):
		if key is None:
			return
		if self.pixel_meta[key][P_MATCHED]:
			return
		if self.selected is None:
			self.selected = key
			self.pixels[key] = self.pixel_meta[key][P_COLOR]
			return

		if self.selected != key:
			pixel_1 = self.pixel_meta[self.selected]
			pixel_2 = self.pixel_meta[key]
			if pixel_1[P_COLOR] == pixel_2[P_COLOR]:
				# Match found!
				pixel_1[P_MATCHED] = True
				pixel_2[P_MATCHED] = True
				self.blink_pixels([key, self.selected], blinks)
				self.selected = None
				self.increment_found_pairs()
			else:
				# Not a match
				pixel_1[P_BLINK_ON_COLOR] = pixel_1[P_COLOR]
				pixel_2[P_BLINK_ON_COLOR] = pixel_2[P_COLOR]
				self.blink_pixels([key, self.selected], times=1, speed=0.5)
				self.pixels[self.selected] = OFF
				self.selected = None

	def increment_found_pairs(self):
		self.found_pairs += 1
		if self.found_pairs < self.WINNING_PAIRS / 2:
				self.state = PLAYING
		elif self.found_pairs < self.WINNING_PAIRS / 4 * 3:
				self.state = HALFWAY
		elif self.found_pairs < self.WINNING_PAIRS:
				self.state = NEAR_WIN
		elif self.found_pairs >= self.WINNING_PAIRS:
				self.state = WIN

	def process_blinks(self):
		found_blink = False
		for pixel_key in self.pixel_meta:
			pixel = self.pixel_meta[pixel_key]
			if pixel[P_BLINKS] == 0:
				continue
			
			found_blink = True
			logger.debug("Processing blink for: %s", pixel_key)
			logger.debug("Data: %s", self.pixel_meta[pixel_key])

			# Is it even time to process this pixel yet?
			if self.now >= pixel[P_PREV_BLINK_TIME] + pixel[P_BLINK_DELAY]:
				# if off, turn it on and reset the delay
				if self.pixels[pixel_key] == (0,0,0):
					self.pixels[pixel_key] = pixel[P_BLINK_ON_COLOR] if not self.show_colors else pixel[P_COLOR]
					pixel[P_PREV_BLINK_TIME] = self.now
				# if on, turn it off, reset the delay, and decrease necessary blinks
				else:
					self.pixels[pixel_key] = pixel[P_BLINK_OFF_COLOR]
					pixel[P_PREV_BLINK_TIME] = self.now
					if pixel[P_BLINKS] > 1:
						pixel[P_BLINKS] -= 1
					else:
						self.__reset_blink_values(pixel_key)
		self.processing_complete = not found_blink

	def process_keys(self):
		pressed_keys = set(self.pressed_keys)
		# Get newly pressed keys
		new_presses = pressed_keys - self.last_pressed_keys
		self.last_pressed_keys = pressed_keys

		# Check for held keys
		held_keys = pressed_keys & self.last_pressed_keys

		#  Reset released keys here
		keys_to_unhold = self.last_held_keys - held_keys
		for key in keys_to_unhold:
			if not P_HOLDABLE in self.pixel_meta[key]:
				continue
			if not self.pixel_meta[key][P_HOLD_TRIGGERED]:
				# If not triggered, add this to be processed as a non-holdable
				# since it wasn't processed earlier
				new_presses.add(key)
			self.__reset_held_pixel(key, {
				P_HOLD_ACTION: self.pixel_meta[key][P_HOLD_ACTION]
			})
		self.last_held_keys = held_keys

		# Process still-held keys
		if held_keys:
			for key in held_keys:
				pixel = self.pixel_meta[key]
				if not P_HOLDABLE in pixel:
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
						# Prevent setting blinks if the button is already blinking
						if pixel[P_BLINKS] < 1:
							self.blink_pixel(key, 1)
		if new_presses:
			if self.state == DEMO:
				self.state = PLAYING
			return list(new_presses)[0]

	def handle_pressed_state(self, state):
		if state == S_TOGGLE_COLORS:
			self.toggle_show_colors()
