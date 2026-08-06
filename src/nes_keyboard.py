import pigpio
from time import sleep
from evdev import UInput, ecodes as e

import signal
import sys

# =========================
# GPIO wiring (BCM)
# =========================

DATA = 17
LATCH = 22
CLOCK = 27

# =========================
# pigpio setup
# =========================

pi = pigpio.pi()
if not pi.connected:
    raise RuntimeError("pigpio daemon not running")

pi.set_mode(DATA, pigpio.INPUT)
pi.set_pull_up_down(DATA, pigpio.PUD_UP)

pi.set_mode(LATCH, pigpio.OUTPUT)
pi.set_mode(CLOCK, pigpio.OUTPUT)

pi.write(LATCH, 0)
pi.write(CLOCK, 0)

# =========================
# NES mapping
# =========================

buttons = [
    "A", "B", "Select", "Start",
    "Up", "Down", "Left", "Right"
]

keymap = {
    "A": e.KEY_X,
    "B": e.KEY_Z,
    "Select": e.KEY_RIGHTSHIFT,
    "Start": e.KEY_ENTER,
    "Up": e.KEY_UP,
    "Down": e.KEY_DOWN,
    "Left": e.KEY_LEFT,
    "Right": e.KEY_RIGHT
}

capabilities = {
    e.EV_KEY: list(keymap.values())
}

ui = UInput(capabilities, name="NES Controller pigpio")

# =========================
# Control de salida
# =========================

running = True

def shutdown(sig, frame):
    global running
    running = False
    try:
        ui.close()
        pi.stop()
    except:
        pass
    sys.exit(0)

signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)

# =========================
# Read controller
# =========================

def read_controller():
    states = []

    # latch pulse
    pi.write(LATCH, 1)
    pi.write(LATCH, 0)

    # shift register read
    for _ in range(8):
        states.append(pi.read(DATA))

        pi.write(CLOCK, 1)
        pi.write(CLOCK, 0)

    return states

# =========================
# Main loop
# =========================

previous = [1] * 8


try:
    while running:

        states = read_controller()
        changed = False

        for i, state in enumerate(states):

            key = keymap[buttons[i]]

            # NES logic: 0 = pressed
            pressed = not state
            prev_pressed = not previous[i]

            if pressed and not prev_pressed:
                ui.write(e.EV_KEY, key, 1)
                changed = True

            elif not pressed and prev_pressed:
                ui.write(e.EV_KEY, key, 0)
                changed = True

        if changed:
            ui.syn()

        previous = states

        sleep(0.01)

finally:
    try:
        ui.close()
        pi.stop()
    except:
        pass
