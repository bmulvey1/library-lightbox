# pylint: disable=C0114,C0115,R0903,C0200,C0103

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
# ['__class__', '__name__', 'A0', 'A1', 'A2', 'A3', 'GP0', 'GP1', 'GP10', 'GP11', 'GP12',
# 'GP13', 'GP14', 'GP15', 'GP16', 'GP17', 'GP18', 'GP19', 'GP2', 'GP20', 'GP21', 'GP22',
# 'GP23', 'GP24', 'GP25', 'GP26', 'GP26_A0', 'GP27', 'GP27_A1', 'GP28', 'GP28_A2', 'GP3',
# 'GP4', 'GP5', 'GP6', 'GP7', 'GP8', 'GP9', 'LED', 'SMPS_MODE', 'STEMMA_I2C', 'VBUS_SENSE',
# 'VOLTAGE_MONITOR', '__dict__', 'board_id']

import time
import random
import math
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


colors = [Color.OFF, Color.RED, Color.ORANGE,
          Color.YELLOW, Color.GREEN, Color.BLUE, Color.PURPLE]


class State:
    STANDBY = 0
    SPIRAL = 1
    SPIRAL_END = 2
    ATTRACT = 3
    ATTRACT_SILENT = 4


SPIRAL_TIME = 0.02  # 20 ms / px = 5.12 sec to finish spiral
SPIRAL_EXPAND_TIME = 0.2

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

matrixType = (neomatrix.NEO_MATRIX_BOTTOM + neomatrix.NEO_MATRIX_LEFT +
              neomatrix.NEO_MATRIX_ROWS + neomatrix.NEO_MATRIX_ZIGZAG)

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
        matrix.auto_write = True
        end_color = colors[random.randint(1, 6)]
        frame = []
        for i in range(NUM_PIXELS):
            frame.append(colors[random.randint(1, 6)])
        # set middle 4 to end color
        frame[math.floor((ROWS-1)/2) * 16 + math.floor((COLS-1)/2)] = end_color
        frame[math.floor((ROWS-1)/2) * 16 +
              math.floor((COLS-1)/2) + 1] = end_color
        frame[(math.floor((ROWS-1)/2) + 1) * 16 +
              math.floor((COLS-1)/2)] = end_color
        frame[(math.floor((ROWS-1)/2) + 1) * 16 +
              math.floor((COLS-1)/2) + 1] = end_color

        xmin = 0
        xmax = COLS-1
        ymin = 0
        ymax = ROWS-1
        xsrc = 0
        ysrc = 0
        direction = 0

        for src in range(len(frame)):
            matrix.pixel(xsrc, ysrc, frame[src])
            if direction == 0:      # go right
                xsrc += 1
            if xsrc == xmax:
                direction += 1
            elif direction == 1:    # go down
                ysrc += 1
                if ysrc == ymax:
                    direction += 1
            elif direction == 2:    # go left
                xsrc -= 1
                if xsrc == xmin:
                    direction += 1
            else:                   # go up
                ysrc -= 1
                if ysrc == ymin:
                    direction = 0
                    # end of box has been reached
                    # start next, smaller box
                    xmin += 1
                    xmax -= 1
                    xsrc = xmin
                    ymin += 1
                    ymax -= 1
                    ysrc = ymin
            time.sleep(SPIRAL_TIME)

        xmin = math.floor((ROWS-1)/2)
        xmax = math.floor((ROWS-1)/2) + 1
        ymin = math.floor((COLS-1)/2)
        ymax = math.floor((COLS-1)/2) + 1

        matrix.auto_write = False
        while xmin >= 0:
            xmin -= 1
            xmax += 1
            ymin -= 1
            ymax += 1

            for y in range(ymin, ymax):
                for x in range(xmin, xmax):
                    matrix.pixel(x, y, end_color)

            matrix.display()
            time.sleep(SPIRAL_EXPAND_TIME)

    elif state == State.SPIRAL_END:
        if event.pressed & event.key_number == KEY_BBUTTON:
            state = State.SPIRAL

    elif state == State.ATTRACT:
        if event.pressed & event.key_number == KEY_BBUTTON:
            state = State.SPIRAL

    elif state == State.ATTRACT_SILENT:
        if event.pressed & event.key_number == KEY_BBUTTON:
            state = State.SPIRAL

    else:
        state = State.STANDBY
