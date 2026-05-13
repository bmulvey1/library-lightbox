# pylint: disable=C0114,C0115,C0116,R0903,C0200,C0103,W0603,W0702,C0321

import time
import random
import board
import audiocore
import audiomixer
import audiopwmio
import digitalio
import displayio
import neopixel
import neomatrix
import os
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

# dino_files = ["dino0.bmp", "dino1.bmp", "dino2.bmp", "dino3.bmp",
#               "dino4.bmp", "dino5.bmp", "dino6.bmp", "dino7.bmp", "dino8.bmp"]

dino_files_path = "dinos/"
dino_files = os.listdir(dino_files_path)

audio_path = "audio/"
audio_files = os.listdir(audio_path)


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
    START_DINO = 1
    DINO_END = 2
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

mixer = audiomixer.Mixer(voice_count=1, sample_rate=16000, channel_count=1, bits_per_sample=16, samples_signed=True)
audio.play(mixer)

state = State.STANDBY

just_went_standby = True

select_new_flash = True
current_fade_percentage = 0
fade_percentage_increment = 2
reverse_fade = False

dino_timeout = -1
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


def reset_fade():
    global select_new_flash
    global current_fade_percentage
    global reverse_fade
    global fade_pixels
    global fade_color
    select_new_flash = True
    current_fade_percentage = 0
    reverse_fade = False
    fade_pixels = []
    fade_color = Color.OFF


while 1:

    event = keys.events.get()

    if event:
        if DEBUG: print(event)

        if (event.pressed) and (event.key_number == KEY_ACC):
            if state == State.ATTRACT:
                state = State.STANDBY
                just_went_standby = True
            elif state == State.STANDBY:
                state = State.ATTRACT
            else:
                state = state + 1
                reset_fade()
            if DEBUG: print(state)
        elif (event.pressed) & (event.key_number == KEY_BBUTTON):
            state = State.START_DINO

        # if (event.pressed) & (event.key_number == KEY_ACC):
        #     if selected_dino == 8:
        #         selected_dino = 0
        #     else:
        #         selected_dino += 1
        #     if DEBUG: print(f"dino #{selected_dino} selected")
        #     just_selected_new_dino = True

        # if (event.pressed) & (event.key_number == KEY_BBUTTON):
        #     matrix.fill(Color.OFF)
        #     matrix.display()
        #     selected_dino = 0

    if state == State.STANDBY and just_went_standby:
        matrix.fill(Color.OFF)
        matrix.display()
        reset_fade()
        just_went_standby = False

    elif state == State.START_DINO:
        dino_filename = dino_files[random.randint(0, len(dino_files)-1)]
        if DEBUG: print(f"{dino_filename} selected")

        sound_filename = audio_files[random.randint(0, len(audio_files)-1)]
        #sound_filename = "roar.wav"
        if DEBUG: print(f"{sound_filename} selected")

        try:
            decoder = audiocore.WaveFile(audio_path + sound_filename)
        except:
            pass

        with open(dino_files_path + dino_filename, "rb") as dino_file:
            image, palette = adafruit_imageload.load(
                dino_file, bitmap=displayio.Bitmap, palette=displayio.Palette)
        transparent_index = get_transparent_index(palette)
        if transparent_index > -1:
            palette[transparent_index] = Color.OFF

        # wipe w/ solid color
        matrix.auto_write = False
        wipe_color = colors[random.randint(1,6)]
        for y in range(0,16):
            for x in range(0,16):
                matrix.pixel(x,y,wipe_color)
            matrix.display()
            time.sleep(0.05)

        # then wipe away to reveal and play sound effect
        try:
            mixer.play(decoder)
        except:
            pass

        for y in range(0,16):
            for x in range(0,16):
                matrix.pixel(x,y,palette[image[x,y]])
            matrix.display()
            time.sleep(0.05)

        # time out after 3 minutes and go back to attract mode
        dino_timeout = ticks_add(supervisor.ticks_ms(), 180_000)
        state = State.DINO_END

        # clear out event queue so spamming the button doesn't work
        keys.events.clear()

    elif state == State.DINO_END:
        if event and event.pressed & event.key_number == KEY_BBUTTON:
            state = State.START_DINO
        if ticks_less(dino_timeout, supervisor.ticks_ms()):
            state = State.ATTRACT
            reset_fade()

    elif state == State.ATTRACT:
        if event and event.pressed & event.key_number == KEY_BBUTTON:
            state = State.START_DINO
        # select random x, y, color
        if select_new_flash:
            matrix.fill(Color.OFF)
            matrix.display()
            select_new_flash = False
            if DEBUG: print("new flash")
            coords = (random.randint(2, ROWS-2), random.randint(2, COLS-2))
            fade_size = random.randint(0, 2)
            if DEBUG: print(f"fade_size: {fade_size}")
            fade_color = colors[random.randint(1, 6)]
            if DEBUG: print(f"fade_color: {fade_color}")
            current_fade_percentage = 0
            reverse_fade = False
            fade_pixels = list((range(coords[0] - fade_size, coords[0] + fade_size + 1), range(
                coords[1] - fade_size, coords[1] + fade_size + 1))) if fade_size >= 1 else [[coords[0]], [coords[1]]]
            next_fade_update = supervisor.ticks_ms()
            if DEBUG: print(f"next update, current_time: {(next_fade_update, supervisor.ticks_ms())}")

        # fade in and out over ATTRACT_FADE_TIME seconds
        if ticks_less(next_fade_update, supervisor.ticks_ms()):
            for x, y in product(fade_pixels[0], fade_pixels[1]):
                matrix.pixel(x, y, set_brightness(
                    fade_color, current_fade_percentage/100))
            matrix.display()

            current_fade_percentage = current_fade_percentage + \
                fade_percentage_increment if not reverse_fade else current_fade_percentage - \
                fade_percentage_increment
            if current_fade_percentage >= 100:
                reverse_fade = True

            if reverse_fade and current_fade_percentage <= 0:
                reverse_fade = False
                select_new_flash = True
            next_fade_update = ticks_add(supervisor.ticks_ms(), 30)

    # if just_selected_new_dino:
    #     just_selected_new_dino = False
    #     file = open(dino_files_path+dino_files[selected_dino], "rb")

    #     image, palette = adafruit_imageload.load(file, bitmap=displayio.Bitmap, palette=displayio.Palette)
    #     file.close()
    #     transparent_index = get_transparent_index(palette)
    #     if transparent_index > -1:
    #         palette[transparent_index] = Color.OFF

    #     matrix.auto_write = False
    #     for x,y in product(range(0,16), range(0,16)):
    #         color = palette[image[x,y]]
    #         matrix.pixel(x,y,color)
    #     matrix.display()
