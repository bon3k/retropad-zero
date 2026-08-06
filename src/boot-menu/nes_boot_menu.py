#!/usr/bin/env python3

import os
import sys
import time
import subprocess

from gpiozero import OutputDevice, DigitalInputDevice

from interface import InterfazLCD

from camera import Camera

from picamera2 import Picamera2
from PIL import Image
from datetime import datetime

from libcamera import Transform

from pathlib import Path


# ============================================================
# LCD
# ============================================================

lcd = InterfazLCD()

SAVE_DIR = "/home/nes/Pictures"

os.makedirs(SAVE_DIR, exist_ok=True)



# ============================================================
# NES Controller wiring (BCM)
# ============================================================

DATA_PIN = 17
LATCH_PIN = 22
CLOCK_PIN = 27

latch = OutputDevice(LATCH_PIN)
clock = OutputDevice(CLOCK_PIN)
data = DigitalInputDevice(DATA_PIN, pull_up=True)


# ============================================================
# NES button indexes
# ============================================================

NES_A = 0
NES_B = 1
NES_SELECT = 2
NES_START = 3
NES_UP = 4
NES_DOWN = 5
NES_LEFT = 6
NES_RIGHT = 7


# ============================================================
# NES reader
# ============================================================

def read_controller():

    states = []

    latch.on()
    time.sleep(0.00001)
    latch.off()

    for _ in range(8):

        states.append(data.value)

        clock.on()
        time.sleep(0.00001)

        clock.off()
        time.sleep(0.00001)

    return states


# ============================================================
# Input abstraction
# ============================================================

class NESButtons:

    def __init__(self):

        self.last_button = None
        self.last_time = 0

        # tiempo minimo entre repeticiones
        self.repeat_delay = 0.18

    def get_action(self):

        states = read_controller()

        action = None


        if states[NES_UP]:
            action = "arriba"

        elif states[NES_DOWN]:
            action = "abajo"

        elif states[NES_A]:
            action = "enter"

        elif states[NES_START]:
            action = "enter"

        elif states[NES_B]:
            action = "back"

        if action is None:
            self.last_button = None
            return None

        now = time.time()

        if (
            action == self.last_button
            and
            now - self.last_time < self.repeat_delay
        ):
            return None

        self.last_button = action
        self.last_time = now

        return action


buttons = NESButtons()

camera = Camera(lcd, buttons) ###############


# ============================================================
# Menu input
# ============================================================

HDMI_STATUS = "/sys/class/drm/card0-HDMI-A-1/status"

def hdmi_connected():
    try:
        with open(HDMI_STATUS) as f:
            return f.read().strip() == "connected"
    except Exception:
        return False


def leer_entrada_menu():

    while True:

        action = buttons.get_action()

        if action:
            return action

        time.sleep(0.03)


# ============================================================
# Menu actions
# ============================================================

def start_seedsigner():

    lcd.show_black_screen()

    os.execv(
        "/home/nes/seedsigner/src/run_seedsigner.sh",
        [
            "/home/nes/seedsigner/src/run_seedsigner.sh"
        ]
    )

#    subprocess.Popen(
#        [
#            "sudo",
#            "systemctl",
#            "start",
#            "seedsigner.service"
#        ]
#    )

    sys.exit(0)


def start_emulationstation():


    if not hdmi_connected():
        lcd.show_message("No HDMI display")
        time.sleep(2)
        return


    lcd.show_black_screen()


    os.execv(
        "/bin/bash",
        [
            "bash",
            "/home/nes/start_emulationstation.sh"
        ]
    )


#    subprocess.run(
#        [
#            "sudo",
#            "systemctl",
#            "start",
#            "nes-controller.service"
#        ],
#        check=False
#    )


#    subprocess.Popen(
#        [
#            "/usr/bin/emulationstation"
#        ]
#    )

    sys.exit(0)


def shutdown():

    try:
        lcd.limpiar_lcd()

        # apagar backlight
        lcd.bl_pwm.ChangeDutyCycle(0)

        time.sleep(0.5)

        latch.close()
        clock.close()
        data.close()

    except Exception as e:
        print(f"Error durante shutdown: {e}")

    subprocess.run(
        ["sudo", "shutdown", "-h", "now"],
        check=False
    )


# ============================================================
# Main menu
# ============================================================

def menu():

    options = [
        "Camara",
        "SeedSigner",
        "EmulationStation",
        "shutdown"
    ]

    selected = 0

    while True:

        lcd.display_menu(
            options,
            selected,
            "BOOT"
        )

        action = leer_entrada_menu()

        if action == "arriba":

            selected = (
                selected - 1
            ) % len(options)

        elif action == "abajo":

            selected = (
                selected + 1
            ) % len(options)

        elif action == "enter":

            if selected == 0:
#                start_camera()
                camera.run()

            elif selected == 1:
                start_seedsigner()

            elif selected == 2:
                start_emulationstation()

            elif selected == 3:
                shutdown()


# ============================================================
# Main
# ============================================================

def main():

    menu()


if __name__ == "__main__":

    main()

