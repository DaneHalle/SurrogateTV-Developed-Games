import asyncio
import logging
import time
import cv2
from pathlib import Path
from surrortg import Game
from surrortg.inputs import Switch 
from surrortg.image_recognition import AsyncVideoCapture, get_pixel_detector
from games.ninswitch.ns_gamepad_serial import NSGamepadSerial, NSButton, NSDPad
from games.surrobros.ns_dpad_switch import NSDPadSwitch
from games.surrobros.ns_joystick import NSJoystick
from games.surrobros.ns_switch import NSSwitch

import os
import sys
import serial

# image rec
SAVE_FRAMES = False
SAVE_DIR_PATH = "./games/surrobros/imgs/"

# sample detectable
PIXELS_FINISH = [
    ((312, 71), (255, 224, 1)),
    ((317, 87), (237, 192, 1)),
    ((325, 68), (254, 227, 0)),
    ((343, 59), (254, 227, 0)),
    ((330, 82), (253, 212, 0)),
    ((348, 77), (254, 225, 0)),
    ((362, 79), (254, 227, 0)),
    ((344, 95), (236, 191, 0)),
    ((359, 96), (237, 195, 0)),
    ((345, 106), (209, 161, 0)),
    ((361, 110), (210, 160, 0)),
    ((347, 123), (182, 129, 0)),
    ((361, 123), (184, 134, 0)),
    ((348, 135), (179, 128, 0)),
    ((361, 139), (180, 129, 1)),
    ((348, 154), (182, 141, 1)),
    ((361, 156), (182, 139, 0)),
    ((348, 170), (187, 159, 0)),
    ((360, 172), (187, 157, 0)),
    ((347, 183), (203, 185, 1)),
    ((363, 187), (204, 188, 4)),
    ((355, 64), (255, 226, 0)),
]

class SurroBrosIR(Game):

    async def on_init(self):
        # init controls
        self.usb_0 = NSGamepadSerial()
        self.usb_1 = NSGamepadSerial()
        self.usb_2 = NSGamepadSerial()
        self.usb_3 = NSGamepadSerial()
        self.usb_4 = NSGamepadSerial()
        try:
            # RX -> TXD | GPIO14 (08 - Blue Wire) | TX -> RXD | GPIO15 (10 - Green Wire)
            # SERIAL_0 = serial.Serial('/dev/ttyAMA0', 2000000, timeout=0)
            # RX -> TXD | GPIO00 (27 - Blue Wire) | TX -> RXD | GPIO01 (28 - Green Wire)
            SERIAL_1 = serial.Serial('/dev/ttyAMA1', 2000000, timeout=0) 
            # RX -> TXD | GPIO04 (07 - Blue Wire) | TX -> RXD | GPIO05 (29 - Green Wire)
            SERIAL_2 = serial.Serial('/dev/ttyAMA2', 2000000, timeout=0)
            # RX -> TXD | GPIO08 (24 - Blue Wire) | TX -> RXD | GPIO09 (21 - Green Wire)
            SERIAL_3 = serial.Serial('/dev/ttyAMA3', 2000000, timeout=0)
            # RX -> TXD | GPIO12 (32 - Blue Wire) | TX -> RXD | GPIO13 (33 - Green Wire)
            SERIAL_4 = serial.Serial('/dev/ttyAMA4', 2000000, timeout=0)
            logging.info(f"Found ttyAMA0/ttyAMA1/ttyAMA2/ttyAMA3/ttyAMA4")
        except:
            logging.critical(f"NSGadget serial port not found")
            sys.exit(1)
        # usb_0.begin(SERIAL_0)
        self.usb_1.begin(SERIAL_1)
        self.usb_2.begin(SERIAL_2)
        self.usb_3.begin(SERIAL_3)
        self.usb_4.begin(SERIAL_4)

        self.io.register_inputs(
            {
                "left_joystick": NSJoystick( "Left",
                    self.usb_1.leftXAxis, self.usb_1.leftYAxis,
                    self.usb_2.leftXAxis, self.usb_2.leftYAxis,
                    self.usb_3.leftXAxis, self.usb_3.leftYAxis,
                    self.usb_4.leftXAxis, self.usb_4.leftYAxis
                ),
                "right_joystick": NSJoystick( "Right",
                    self.usb_1.rightXAxis, self.usb_1.rightYAxis,
                    self.usb_2.rightXAxis, self.usb_2.rightYAxis,
                    self.usb_3.rightXAxis, self.usb_3.rightYAxis,
                    self.usb_4.rightXAxis, self.usb_4.rightYAxis
                ),
                "dpad_up": NSDPadSwitch(self.usb_1, self.usb_2, self.usb_3, self.usb_4, NSDPad.UP, "UP"),
                "dpad_left": NSDPadSwitch(self.usb_1, self.usb_2, self.usb_3, self.usb_4, NSDPad.LEFT, "LEFT"),
                "dpad_right": NSDPadSwitch(self.usb_1, self.usb_2, self.usb_3, self.usb_4, NSDPad.RIGHT, "RIGHT"),
                "dpad_down": NSDPadSwitch(self.usb_1, self.usb_2, self.usb_3, self.usb_4, NSDPad.DOWN, "DOWN"),
                "Y": NSSwitch(self.usb_1, self.usb_2, self.usb_3, self.usb_4, NSButton.Y, "Y"),
                "X": NSSwitch(self.usb_1, self.usb_2, self.usb_3, self.usb_4, NSButton.X, "X"),
                "A": NSSwitch(self.usb_1, self.usb_2, self.usb_3, self.usb_4, NSButton.A, "A"),
                "B": NSSwitch(self.usb_1, self.usb_2, self.usb_3, self.usb_4, NSButton.B, "B"),
                "left_throttle": NSSwitch(self.usb_1, self.usb_2, self.usb_3, self.usb_4, NSButton.LEFT_THROTTLE, "LEFT_THROTTLE"),
                "left_trigger": NSSwitch(self.usb_1, self.usb_2, self.usb_3, self.usb_4, NSButton.LEFT_TRIGGER, "LEFT_TRIGGER"),
                "right_throttle": NSSwitch(self.usb_1, self.usb_2, self.usb_3, self.usb_4, NSButton.RIGHT_THROTTLE, "RIGHT_THROTTLE"),
                "right_trigger": NSSwitch(self.usb_1, self.usb_2, self.usb_3, self.usb_4, NSButton.RIGHT_TRIGGER, "RIGHT_TRIGGER"),
                "left_stick": NSSwitch(self.usb_1, self.usb_2, self.usb_3, self.usb_4, NSButton.LEFT_STICK, "LEFT_STICK"),
                "right_stick": NSSwitch(self.usb_1, self.usb_2, self.usb_3, self.usb_4, NSButton.RIGHT_STICK, "RIGHT_STICK"),
            },
        )
        self.io.register_inputs(
            {
                "minus": NSSwitch(self.usb_1, self.usb_2, self.usb_3, self.usb_4, NSButton.MINUS, "MINUS"),
                "plus": NSSwitch(self.usb_1, self.usb_2, self.usb_3, self.usb_4, NSButton.PLUS, "PLUS"),
                "home": NSSwitch(self.usb_1, self.usb_2, self.usb_3, self.usb_4, NSButton.HOME, "HOME"),
                "capture": NSSwitch(self.usb_1, self.usb_2, self.usb_3, self.usb_4, NSButton.CAPTURE, "CAPTURE"),
            },
            admin = True,
        )

        # init image rec
        self.image_rec_task = asyncio.create_task(self.image_rec_main())
        self.image_rec_task.add_done_callback(self.image_rec_done_cb)
        self.image_rec_task_cancelled = False

        self.has_started = False
        self.pre_game_ready_sent = False


        # init frame saving
        # if SAVE_FRAMES:
        #     logging.info(f"SAVING FRAMES TO {SAVE_DIR_PATH}")
        #     Path(SAVE_DIR_PATH).mkdir(parents=True, exist_ok=True)


    async def on_pre_game(self):
        self.io.send_pre_game_ready()

    async def on_finish(self):
        logging.info(f"Finish")
        self.io.disable_inputs()

        self.usb_1.rightYAxis(128)
        self.usb_1.rightXAxis(128)
        self.usb_1.leftYAxis(128)
        self.usb_1.leftXAxis(128)    

        self.usb_2.rightYAxis(128)
        self.usb_2.rightXAxis(128)
        self.usb_2.leftYAxis(128)
        self.usb_2.leftXAxis(128)   

        self.usb_3.rightYAxis(128)
        self.usb_3.rightXAxis(128)
        self.usb_3.leftYAxis(128)
        self.usb_3.leftXAxis(128)   

        self.usb_4.rightYAxis(128)
        self.usb_4.rightXAxis(128)
        self.usb_4.leftYAxis(128)
        self.usb_4.leftXAxis(128)  

        self.usb_1.releaseAll()
        self.usb_2.releaseAll()
        self.usb_3.releaseAll()
        self.usb_4.releaseAll()

    async def on_prepare(self):
        logging.info("preparing...")
        
        await asyncio.sleep(2)

        self.usb_1.press(NSButton.HOME)
        await asyncio.sleep(0.1)
        self.usb_1.release(NSButton.HOME)
        await asyncio.sleep(1)
        self.usb_1.press(NSButton.X)
        await asyncio.sleep(0.1)
        self.usb_1.release(NSButton.X)
        await asyncio.sleep(1)
        self.usb_1.press(NSButton.A)
        await asyncio.sleep(0.1)
        self.usb_1.release(NSButton.A)
        await asyncio.sleep(3)
        self.usb_1.press(NSButton.A)
        await asyncio.sleep(0.1)
        self.usb_1.release(NSButton.A)
        await asyncio.sleep(1)
        self.usb_1.press(NSButton.A)
        await asyncio.sleep(0.1)
        self.usb_1.release(NSButton.A)
        await asyncio.sleep(1)
        self.usb_1.press(NSButton.A)
        await asyncio.sleep(0.1)
        self.usb_1.release(NSButton.A)

        self.usb_1.releaseAll()
        self.usb_2.releaseAll()
        self.usb_3.releaseAll()
        self.usb_4.releaseAll()
        logging.info("...preparing.finish")


    async def on_exit(self, reason, exception):
        # end controls
        logging.info(f"Exit")
        self.io.disable_inputs() 

        self.usb_1.end()
        self.usb_2.end()
        self.usb_3.end()
        self.usb_4.end()

        # end image rec task
        await self.cap.release()
        self.image_rec_task.cancel()

    async def image_rec_main(self):
        # create capture
        self.cap = await AsyncVideoCapture.create("/dev/video21")

        # get detectors
        finish_flag = get_pixel_detector(PIXELS_FINISH)

        # loop through frames
        i = 0
        async for frame in self.cap.frames():
            # detect
            if finish_flag(frame):
                logging.info("Has flag!")
                for seat in self.io._message_router.get_all_seats():
                    logging.info(f"\t"+str(seat))
                    self.io.send_score(
                        score=1, seat=seat, seat_final_score=True,
                    )
                self.io.send_score(score=1, final_score=True)

            # generic
            # if i % 100 == 0:
            #     logging.info("100 frames checked")
            # if SAVE_FRAMES and i % 100 == 0:
            #     cv2.imwrite(f"{SAVE_DIR_PATH}/{i}.jpg", frame)
            #     logging.info(f"SAVED {i}.jpg")
            # i += 1

        if self.image_rec_task_cancelled:
            logging.info("Image rec task finished.")
        else:
            raise RuntimeError("Image rec task finished by itself")

    async def image_rec_done_cb(self, fut):
        # make program end if image_rec_task raises error
        if not fut.cancelled() and fut.exception() is not None:
            import traceback, sys  # noqa: E401

            e = fut.exception()
            logging.error(
                "".join(traceback.format_exception(None, e, e.__traceback__))
            )
            sys.exit(1)

if __name__ == "__main__":
    SurroBrosIR().run()
