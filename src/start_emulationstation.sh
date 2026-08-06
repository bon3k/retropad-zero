#!/bin/bash

sudo systemctl start nes-controller.service

exec /usr/bin/emulationstation

sudo systemctl stop nes-controller.service

stty sane

reset

exec /home/nes/boot-menu/start_boot_menu.sh
