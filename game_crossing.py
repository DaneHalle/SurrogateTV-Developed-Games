import asyncio
import logging
import cv2
from pathlib import Path
from surrortg import Game
from surrortg.inputs import Switch
from surrortg.image_recognition import AsyncVideoCapture, get_pixel_detector
from games.ninswitch.ns_gamepad_serial import NSGamepadSerial, NSButton, NSDPad
from games.ninswitch.ns_switch import NSSwitch
from games.ninswitch.ns_dpad_switch import NSDPadSwitch
from games.ninswitch.ns_joystick import NSJoystick
import pigpio
import sys
import json
import requests
import telebot
bot = telebot.TeleBot("[REDACTED]")
chat_id = 1645773858

pigpio.exceptions = False
pi = pigpio.pi()
nsg_reset = 18
ON = 0
OFF = 1

# image rec
SAVE_ALL_FRAMES = False
SAVE_DIR_PATH = "./games/ninswitch/imgs"
global save_individual_fame, allowReset
save_individual_fame = False
allowReset = True

# ----------------------------------------------------

HOME = [
    ((262, 45), (41, 41, 41)),
    ((902, 43), (41, 41, 41)),
    ((1186, 29), (41, 41, 41)),
    ((1254, 678), (41, 41, 41)),
    ((288, 695), (41, 41, 41)),
    ((15, 690), (41, 41, 41)),
    ((88, 680), (254, 254, 254)),
    ((74, 662), (153, 252, 3)),
]

INPUT_NEEDED = [
    ((427, 87), (252, 253, 248)),
    ((572, 107), (252, 255, 255)),
    ((656, 86), (252, 251, 247)),
    ((698, 106), (233, 239, 239)),
    ((790, 80), (255, 255, 248)),
    ((802, 95), (255, 253, 250)),
    ((830, 95), (255, 255, 253)),
    ((498, 261), (39, 79, 255)),
    ((535, 233), (57, 75, 233)),
    ((587, 240), (39, 79, 255)),
    ((615, 259), (28, 74, 248)),
    ((521, 246), (36, 79, 254)),
    ((596, 693), (254, 255, 255)),
    ((1013, 678), (255, 255, 253)),
]

RECONNECTED = [
    ((637, 422), (41, 41, 41)),
    ((595, 461), (69, 69, 69)),
    ((692, 458), (69, 69, 69)),
    ((617, 488), (255, 255, 255)),
    ((451, 436), (255, 255, 255)),
    ((769, 405), (255, 255, 255)),
    ((497, 261), (37, 79, 249)),
    ((521, 244), (36, 79, 254)),
    ((589, 244), (37, 78, 254)),
    ((619, 262), (39, 79, 254)),
    ((572, 107), (254, 255, 253)),
    ((427, 87), (255, 255, 255)),
    ((658, 85), (253, 254, 248)),
    ((555, 609), (38, 77, 255)),
    ((569, 588), (28, 76, 248)),
    ((539, 588), (47, 96, 255)),
    ((697, 106), (249, 248, 243)),
    ((789, 80), (252, 249, 240)),
    ((802, 95), (255, 255, 251)),
    ((830, 96), (255, 255, 255)),
]

SETTINGS = [
    ((87, 48), (42, 42, 42)),
    ((441, 39), (41, 41, 41)),
    ((1111, 43), (41, 41, 41)),
    ((1251, 682), (41, 41, 41)),
    ((610, 712), (41, 41, 41)),
    ((87, 680), (255, 255, 255)),
    ((38, 683), (41, 41, 41)),
    ((74, 661), (151, 250, 0)),
]

TITLE = [
    ((638, 101), (255, 235, 170)),
    ((687, 133), (196, 119, 37)),
    ((497, 119), (185, 110, 42)),
    ((465, 147), (255, 229, 46)),
    ((501, 216), (255, 229, 48)),
    ((457, 254), (255, 224, 35)),
    ((435, 327), (255, 220, 20)),
    ((489, 288), (255, 227, 31)),
    ((520, 285), (255, 224, 23)),
    ((505, 331), (255, 218, 18)),
    ((566, 257), (255, 224, 39)),
    ((579, 298), (254, 222, 17)),
    ((636, 256), (255, 227, 37)),
    ((603, 297), (254, 222, 15)),
    ((677, 275), (255, 225, 37)),
    ((651, 322), (255, 225, 23)),
    ((708, 243), (254, 226, 41)),
    ((702, 314), (254, 221, 20)),
    ((741, 271), (252, 222, 28)),
    ((782, 331), (252, 218, 6)),
    ((834, 244), (255, 225, 39)),
    ((832, 310), (254, 215, 13)),
    ((817, 174), (255, 227, 51)),
    ((745, 187), (255, 226, 44)),
    ((680, 202), (255, 228, 56)),
    ((613, 194), (255, 226, 47)),
    ((571, 178), (255, 230, 50)),
    ((864, 31), (0, 188, 128)),
    ((806, 41), (111, 217, 241)),
    ((772, 84), (251, 255, 211)),
]

# ----------------------------------------------------

class reset_trinkets(Switch):
    async def on(self, seat=0):
        global allowReset
        if allowReset:
            pi.write(nsg_reset, ON)
            await asyncio.sleep(0.5)
            pi.write(nsg_reset, OFF)
            await asyncio.sleep(2)
            allowReset = False
            logging.info(f"\t{seat} | TRINKET_RESET down")

    async def off(self, seat=0):
        logging.info(f"\t...{seat} | TRINKET_RESET up")

# ----------------------------------------------------

class debug_switch(Switch):
    def __init__(self):
        global DEBUG
        DEBUG = False

    async def on(self, seat=0):
        global DEBUG, bypass, LOCKED
        if DEBUG:
            DEBUG = False
            if bypass:
                bypass = False
                LOCKED = False
        else:
            DEBUG = True

        logging.info(f"\t{seat} | debug_switch down in position {DEBUG}")

    async def off(self, seat=0):
        logging.info(f"\t{seat} | debug_switch up")

# ----------------------------------------------------

class CaptureScreen(Switch):
    async def on(self, seat=0):
        global save_individual_fame
        save_individual_fame = True
        logging.info(f"\t{seat} | Capturing_Frames down")

    async def off(self, seat=0):
        global save_individual_fame
        save_individual_fame = False
        logging.info(f"\t{seat} | Capturing_Frames up")

# ----------------------------------------------------

class SAMPLE_ADVANCED_GAME(Game):
    async def on_init(self):
        self.prepare = True
        # init controls
        self.nsg = NSGamepadSerial()
        self.nsg.begin()
        self.io.register_inputs(
            {
                "left_joystick": NSJoystick(
                    self.nsg.leftXAxis, self.nsg.leftYAxis
                ),
                "right_joystick": NSJoystick(
                    self.nsg.rightXAxis, self.nsg.rightYAxis
                ),
                "dpad_up": NSDPadSwitch(self.nsg, NSDPad.UP),
                "dpad_left": NSDPadSwitch(self.nsg, NSDPad.LEFT),
                "dpad_right": NSDPadSwitch(self.nsg, NSDPad.RIGHT),
                "dpad_down": NSDPadSwitch(self.nsg, NSDPad.DOWN),
                "Y": NSSwitch(self.nsg, NSButton.Y),
                "X": NSSwitch(self.nsg, NSButton.X),
                "A": NSSwitch(self.nsg, NSButton.A),
                "B": NSSwitch(self.nsg, NSButton.B),
                "left_throttle": NSSwitch(self.nsg, NSButton.LEFT_THROTTLE),
                "left_trigger": NSSwitch(self.nsg, NSButton.LEFT_TRIGGER),
                "right_throttle": NSSwitch(self.nsg, NSButton.RIGHT_THROTTLE),
                "right_trigger": NSSwitch(self.nsg, NSButton.RIGHT_TRIGGER),
                "left_stick": NSSwitch(self.nsg, NSButton.LEFT_STICK),
                "right_stick": NSSwitch(self.nsg, NSButton.RIGHT_STICK),
                "reset_trinkets": reset_trinkets(),
                "plus": NSSwitch(self.nsg, NSButton.PLUS),
            },
        )
        self.io.register_inputs(
            {
                "home": NSSwitch(self.nsg, NSButton.HOME),
                "capture": NSSwitch(self.nsg, NSButton.CAPTURE),
                "debug_switch": debug_switch(),
                "capture_frame": CaptureScreen(),
                "minus": NSSwitch(self.nsg, NSButton.MINUS),
            },
            admin=True,
        )

        # init image rec
        self.image_rec_task = asyncio.create_task(self.image_rec_main())
        self.image_rec_task.add_done_callback(self.image_rec_done_cb)

        # init frame saving
        logging.info(f"SAVING FRAMES TO {SAVE_DIR_PATH}")
        Path(SAVE_DIR_PATH).mkdir(parents=True, exist_ok=True)

        self.curUser = "[{'id': 'SurrogateTVRePlayrobot', 'streamer': 'SurrogateTVRePlaystreamer', 'queueOptionId': '0', 'seat': 0, 'set': 0, 'enabled': True, 'username': 'dummydummydummydummydummydummydummyd'}]"
        self.userID = "eu-west-1:dummydummydummydummydummydummydummyd"

# ----------------------------------------------------

    async def on_start(self):
        self.curUser = self.players
        player = json.loads(json.dumps(self.players))[0]['username']

        req = requests.get("https://g9b1fyald3.execute-api.eu-west-1.amazonaws.com/master/users?search="+str(player)).text
        uid = json.loads(req)['result'][0]['userId']
        self.userID = uid

# ----------------------------------------------------

    async def on_prepare(self):
        pi.write(nsg_reset, ON)
        await asyncio.sleep(0.5)
        pi.write(nsg_reset, OFF)
        await asyncio.sleep(2)

# ----------------------------------------------------

    async def on_finish(self):
        self.io.disable_inputs()
        self.nsg.releaseAll()

        self.nsg.rightYAxis(128)
        self.nsg.rightXAxis(128)
        self.nsg.leftYAxis(128)
        self.nsg.leftXAxis(128)   

        self.io.send_score(score=1, seat=0, final_score=True)

        self.prepare = True

# ----------------------------------------------------

    async def on_exit(self, reason, exception):
        # end controls
        self.io.disable_inputs() 
        self.nsg.end()
        # end image rec task
        await self.cap.release()
        self.image_rec_task.cancel()

# ----------------------------------------------------

    async def image_rec_main(self):
        # create capture
        self.cap = await AsyncVideoCapture.create("/dev/video21")
        
        global LOCKED, allowReset, bypass, DEBUG
        LOCKED = False

        # get detector
        home = get_pixel_detector(HOME, 50)
        input_needed = get_pixel_detector(INPUT_NEEDED, 50)
        reconnected = get_pixel_detector(RECONNECTED, 50)
        settings = get_pixel_detector(SETTINGS, 50)
        title = get_pixel_detector(TITLE, 50)

        # loop through frames
        i = 0
        z = 0
        async for frame in self.cap.frames():
            # detect trigger
            if i%30==0 and (input_needed(frame) or reconnected(frame)):
                pi.write(nsg_reset, ON)
                await asyncio.sleep(0.5)
                pi.write(nsg_reset, OFF)
                await asyncio.sleep(1)
            try:
                if (input_needed(frame) or reconnected(frame)) and not DEBUG:
                    self.io.disable_input(0)
                    self.nsg.press(NSButton.A)
                    await asyncio.sleep(0.1)
                    self.nsg.release(NSButton.A)
                    await asyncio.sleep(2)
                    self.nsg.press(NSButton.A)
                    await asyncio.sleep(0.1)
                    self.nsg.release(NSButton.A)
                    await asyncio.sleep(2)
                    self.io.enable_input(0)
            except:
                if (input_needed(frame) or reconnected(frame)) and not DEBUG:
                    self.nsg.press(NSButton.A)
                    await asyncio.sleep(0.1)
                    self.nsg.release(NSButton.A)
                    await asyncio.sleep(2)
                    self.nsg.press(NSButton.A)
                    await asyncio.sleep(0.1)
                    self.nsg.release(NSButton.A)
                    await asyncio.sleep(2)

            # lock trigger
            try:
                if (home(frame) or settings(frame) or title(frame)) and not LOCKED and not DEBUG:
                    self.io.disable_input(0)
                    if not (i<100 or bypass):
                        player = json.loads(json.dumps(self.curUser))[0]['username']
                        msg = "ANIMAL CROSSING\nGame locked due to either being at home screen or capture card bars. \nUser's information are as follows:\n> "+player+"\n> "+self.userID
                        bot.send_message(chat_id, msg, parse_mode="markdown")
                        LOCKED = True
                        self.nsg.end()
                        self.prepare = False
                        content = json.loads('{"game":"crossing"}')
                        req = requests.post("[REDACTED]", content)
                    else:
                        msg = "ANIMAL CROSSING\nBypass utilized...Take action to get to a proper menu before something messes up."
                        bot.send_message(chat_id, msg, parse_mode="markdown")
                        bypass = True
                        DEBUG = True
                        LOCKED = True
                        content = json.loads('{"game":"crossing"}')
                        req = requests.post("[REDACTED]", content)
            except:
                if (home(frame) or settings(frame) or title(frame)) and not LOCKED and not DEBUG:
                    if not (i<100 or bypass):
                        player = json.loads(json.dumps(self.curUser))[0]['username']
                        msg = "ANIMAL CROSSING\nGame locked due to either being at home screen or capture card bars. \nUser's information are as follows:\n> "+player+"\n> "+self.userID
                        bot.send_message(chat_id, msg, parse_mode="markdown")
                        LOCKED = True
                        self.nsg.end()
                        self.prepare = False
                        content = json.loads('{"game":"crossing"}')
                        req = requests.post("[REDACTED]", content)
                    else:
                        msg = "ANIMAL CROSSING\nBypass utilized...Take action to get to a proper menu before something messes up."
                        bot.send_message(chat_id, msg, parse_mode="markdown")
                        bypass = True
                        DEBUG = True
                        LOCKED = True
                        content = json.loads('{"game":"crossing"}')
                        req = requests.post("[REDACTED]", content)

            if LOCKED: 
                self.io.send_playing_ended()
                self.prepare = True

            # generic
            if i%100==0:
                allowReset = True
            if SAVE_ALL_FRAMES or save_individual_fame:
                cv2.imwrite(f"{SAVE_DIR_PATH}/{i}.jpg", frame)
                logging.info(f"SAVED {i}.jpg")
            i += 1

# ----------------------------------------------------

    def image_rec_done_cb(self, fut):
        # make program end if image_rec_task raises error
        if not fut.cancelled() and fut.exception() is not None:
            import traceback, sys  # noqa: E401

            e = fut.exception()
            logging.error(
                "".join(traceback.format_exception(None, e, e.__traceback__))
            )
            sys.exit(1)


if __name__ == "__main__":
    SAMPLE_ADVANCED_GAME().run()