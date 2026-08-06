import os
import time

from datetime import datetime

from picamera2 import Picamera2
from PIL import Image


class Camera:

    def __init__(self, lcd, buttons,
                 save_dir="/home/nes/Pictures"):

        self.lcd = lcd
        self.buttons = buttons
        self.save_dir = save_dir

        os.makedirs(self.save_dir, exist_ok=True)

        self.preview_config = None
        self.capture_config = None

    # ============================================================
    # Camera setup
    # ============================================================

    def _create_camera(self):

        picam = Picamera2()

        self.preview_config = picam.create_preview_configuration(
            main={
                "size": (240, 240),
                "format": "RGB888"
            }
        )

        self.capture_config = picam.create_still_configuration()

        picam.configure(self.preview_config)

        return picam

    # ============================================================
    # Frame rendering
    # ============================================================

    def _display_frame(self, frame):

        # OV5647 fix bgr <-> rgb swap
        frame = frame[:, :, [2, 1, 0]]

        img = Image.fromarray(frame)

        # Corregir orientación de la cámara
        img = img.rotate(-90, expand=True)

        self.lcd.display_image(img)

    # ============================================================
    # Photo capture
    # ============================================================

    def _capture_photo(self, picam):

        filename = os.path.join(
            self.save_dir,
            datetime.now().strftime("%Y%m%d_%H%M%S.jpg")
        )

        picam.switch_mode_and_capture_file(
            self.capture_config,
            filename
        )

        picam.switch_mode(self.preview_config)

    # ============================================================
    # Main loop
    # ============================================================

    def run(self):

        picam = self._create_camera()

        picam.start()

        time.sleep(0.5)

        try:

            while True:

                frame = picam.capture_array()

                self._display_frame(frame)

                action = self.buttons.get_action()

                if action == "enter":

                    self._capture_photo(picam)

                elif action == "back":

                    break

                time.sleep(0.01)

        finally:

            picam.stop()
            picam.close()

            self.lcd.show_black_screen()

