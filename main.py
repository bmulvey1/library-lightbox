# pylint: disable=C0114,C0115,R0903

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

# >>> dir(board)
# ['__class__', '__name__', 'A0', 'A1', 'A2', 'A3', 'GP0', 'GP1', 'GP10', 'GP11', 'GP12', 'GP13', 'GP14', 'GP15', 'GP16', 'GP17', 'GP18', 'GP19', 'GP2', 'GP20', 'GP21', 'GP22', 'GP23', 'GP24', 'GP25', 'GP26', 'GP26_A0', 'GP27', 'GP27_A1', 'GP28', 'GP28_A2', 'GP3', 'GP4', 'GP5', 'GP6', 'GP7', 'GP8', 'GP9', 'LED', 'SMPS_MODE', 'STEMMA_I2C', 'VBUS_SENSE', 'VOLTAGE_MONITOR', '__dict__', 'board_id']

import time
import board
import audiomp3
import audiopwmio
import digitalio
import neopixel
import neomatrix
import keypad


class Color:
    OFF = 0x000000
    RED = 0xff0000
    ORANGE = 0xff1e00
    YELLOW = 0xff7f00
    GREEN = 0x00ff00
    BLUE = 0x0000ff
    PURPLE = 0x7f00ff


class State:
    STANDBY = 0
    SPIRAL = 1
    ATTRACT = 2
    ATTRACT_SILENT = 3


PIXEL_PIN = board.GP27
ACC_BUTTON_PIN = board.GP15
BIG_BUTTON_PIN = board.GP26
AUDIO_PIN = board.GP20

keys = keypad.keys((ACC_BUTTON_PIN, BIG_BUTTON_PIN),
                   value_when_pressed=True, pull=True)

KEY_ACC = 0
KEY_BBUTTON = 1

ROWS = 16
COLS = 16
NUM_PIXELS = ROWS*COLS
BRIGHTNESS = 0.3

pixels = neopixel.NeoPixel(
    PIXEL_PIN, NUM_PIXELS, pixel_order=neopixel.GRB, brightness=BRIGHTNESS, auto_write=False)

matrixType = (neomatrix.NEO_MATRIX_BOTTOM, neomatrix.NEO_MATRIX_LEFT,
              neomatrix.NEO_MATRIX_ROWS, neomatrix.NEO_MATRIX_ZIGZAG)

matrix = neomatrix.NeoMatrix(pixels, ROWS, COLS, 1, 1, matrixType, rotation=0)

audio = audiopwmio.PWMAudioOut(AUDIO_PIN)

state = State.STANDBY

while 1:

    event = keys.events.get()

    if event.pressed & event.key_number == KEY_ACC:
        # accessory button pressed
        if state == State.ATTRACT_SILENT:
            state = State.STANDBY
        elif state == State.STANDBY:
            state = State.ATTRACT
        else:
            state = state + 1

    if state == State.STANDBY:
        matrix.fill(Color.OFF)
        audio.stop()

    elif state == State.SPIRAL:
        pass

    elif state == State.ATTRACT:
        if event.pressed & event.key_number == KEY_BBUTTON:
            state = State.SPIRAL

    elif state == State.ATTRACT_SILENT:
        if event.pressed & event.key_number == KEY_BBUTTON:
            state = State.SPIRAL

    else:
        state = State.STANDBY

    continue
