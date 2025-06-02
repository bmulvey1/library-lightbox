# 256 ────────────────┐241
# 225┌────────────────┘240
# 224└────────────────┐209
# 193┌────────────────┘208
# 192└────────────────┐177
# 161┌────────────────┘176
# 160└────────────────┐145
# 129┌────────────────┘144
# 128└────────────────┐113
# 097┌────────────────┘112
# 096└────────────────┐081
# 065┌────────────────┘080
# 064└────────────────┐049
# 033┌────────────────┘048
# 032└────────────────┐016
# 000 ────────────────┘015

import time
import board
import audiomp3
import audiopwmio
import digitalio
import neopixel
import neomatrix


class Colors:
    OFF = 0x000000
    RED = 0xff0000
    ORANGE = 0xff1e00
    YELLOW = 0xff7f00
    GREEN = 0x00ff00
    BLUE = 0x0000ff
    PURPLE = 0x7f00ff
  
class State:
    standby = 0
    spiral = 1
    attract = 2
    attract_silent = 3
    
PIXEL_PIN = board.IO1  # temp
ACC_BUTTON_PIN = board.IO2 # temp
BIG_BUTTON_PIN = board.IO3 # temp
AUDIO_PIN = board.IO4 # temp


ROWS = 16
COLS = 16
NUM_PIXELS = ROWS*COLS
BRIGHTNESS = 0.3

pixels = neopixel.NeoPixel(
    PIXEL_PIN, NUM_PIXELS, pixel_order=neopixel.GRB, brightness=BRIGHTNESS, auto_write=False)

matrixType = (neomatrix.NEO_MATRIX_BOTTOM, neomatrix.NEO_MATRIX_LEFT,
              neomatrix.NEO_MATRIX_ROWS, neomatrix.NEO_MATRIX_ZIGZAG)

matrix = neomatrix.NeoMatrix(pixels, ROWS, COLS, 1, 1, matrixType, rotation=0)


acc_button = digitalio.DigitalInOut(ACC_BUTTON_PIN)
acc_button.direction = digitalio.Direction.INPUT
acc_button.pull = digitalio.Pull.UP

big_button = digitalio.DigitalInOut(BIG_BUTTON_PIN)
big_button.direction = digitalio.Direction.INPUT
big_button.pull = digitalio.Pull.UP

audio = audiopwmio.PWMAudioOut(AUDIO_PIN)

state = State.standby

big_button_last_pressed = 1

while 1:

    if not acc_button.value:
        # accessory button pressed
        if state == State.attract_silent:
            state = State.standby
        else:
            state = state + 1

    if state == State.standby:
        matrix.fill(Colors.OFF)
        audio.stop()

    elif state == State.spiral:
        pass

    elif state == State.attract:
        # only trip on 0-to-1
        if big_button_last_pressed == 1 and big_button.value ==  0:
            state = State.spiral

    elif state == State.attract_silent:
        # only trip on 0-to-1
        if big_button_last_pressed == 1 and big_button.value ==  0:
            state = State.spiral

    else:
        state = State.standby

    big_button_last_pressed = big_button.value

    continue
