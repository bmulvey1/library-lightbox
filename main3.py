# pylint: disable=C0114,C0115,C0116,R0903,C0200,C0103,W0603,W0702,C0321

import time
import random
import math
import board
import audiomp3
import audiopwmio
import digitalio
import displayio
import neopixel
import neomatrix
import keypad
import supervisor
from adafruit_itertools import product
import adafruit_imageload


DEBUG = True

TICKS_PERIOD = 1 << 29  # supervisor.ticks_ms() overflows after 2^29 ms
TICKS_MAX = TICKS_PERIOD - 1
TICKS_HALFPERIOD = int(TICKS_PERIOD / 2)

# displayio doesn't support indexed bmps with transparency
COLOR_TRANSPARENT = 0x0000FF

YEAR = 2026

dino_files = ["dino0.bmp", "dino1.bmp", "dino2.bmp", "dino3.bmp",
              "dino4.bmp", "dino5.bmp", "dino6.bmp", "dino7.bmp", "dino8.bmp"]
dino_files_path = "dinos/"


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


SPIRAL_TIME = 0.01
SPIRAL_EXPAND_TIME = 0.2

ATTRACT_FADE_TIME = 3

VBUS_PIN = board.VBUS_SENSE
PIXEL_PIN = board.GP26
ACC_BUTTON_PIN = board.GP16
BIG_BUTTON_PIN = board.GP27
AUDIO_PIN = board.GP19

USB_CONNECTED = digitalio.DigitalInOut(VBUS_PIN).value

keys = keypad.Keys((ACC_BUTTON_PIN, BIG_BUTTON_PIN),
                   value_when_pressed=False, pull=True)

KEY_ACC = 0
KEY_BBUTTON = 1

ROWS = 16
COLS = 16
NUM_PIXELS = ROWS*COLS
# keep brightness low if usb connected to avoid overloading port
BRIGHTNESS = 0.4 if not USB_CONNECTED else 0.01

pixels = neopixel.NeoPixel(
    PIXEL_PIN, NUM_PIXELS, pixel_order=neopixel.GRB, brightness=BRIGHTNESS, auto_write=False)

matrixType = (neomatrix.NEO_MATRIX_BOTTOM + neomatrix.NEO_MATRIX_LEFT +
              neomatrix.NEO_MATRIX_ROWS + neomatrix.NEO_MATRIX_ZIGZAG)

matrix = neomatrix.NeoMatrix(pixels, ROWS, COLS, 1, 1, matrixType, rotation=0)

audio = audiopwmio.PWMAudioOut(AUDIO_PIN)

state = State.STANDBY

just_went_standby = True

select_new_flash = True
current_fade_percentage = 0
fade_percentage_increment = 2
reverse_fade = False

spiral_timeout = -1
next_fade_update = -1

fade_pixels = []
fade_color = Color.OFF

selected_dino = 0
just_selected_new_dino = False


def ticks_add(ticks, delta):
    return (ticks + delta) % TICKS_PERIOD


def ticks_diff(ticks1, ticks2):
    diff = (ticks1 - ticks2) & TICKS_MAX
    diff = ((diff + TICKS_HALFPERIOD) & TICKS_MAX) - TICKS_HALFPERIOD
    return diff


def ticks_less(ticks1, ticks2):
    return ticks_diff(ticks1, ticks2) < 0


def set_brightness(color, brightness):
    return round((color >> 16) * brightness) << 16 | round(((color >> 8) & 0xFF) * brightness) << 8 | round((color & 0xFF) * brightness)


def get_transparent_index(palette):
    for idx, i in enumerate(palette):
        if i == COLOR_TRANSPARENT:
            return idx
    return -1


while 1:

    event = keys.events.get()

    if event:
        if DEBUG:
            print(event)

        if (event.pressed) & (event.key_number == KEY_ACC):
            if selected_dino == 8:
                selected_dino = 0
            else:
                selected_dino += 1
            just_selected_new_dino = True

    if just_selected_new_dino:
        file = open(dino_files_path+dino_files[selected_dino], "rb")

        image, palette = adafruit_imageload.load(file, bitmap=displayio.Bitmap, palette=displayio.Palette)
        file.close()
        transparent_index = get_transparent_index(palette)
        if transparent_index > -1:
            palette[transparent_index] = Color.OFF
            
        matrix.auto_write = False
        for x,y in product(range(0,16), range(0,16)):
            color = palette[image[x,y]]
            matrix.pixel(x,y,color)
        matrix.display()

    
