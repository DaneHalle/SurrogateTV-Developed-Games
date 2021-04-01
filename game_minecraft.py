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
chat_id = [REDACTED]

pigpio.exceptions = False
pi = pigpio.pi()
nsg_reset = 18
ON = 0
OFF = 1

# image rec
SAVE_ALL_FRAMES = False
SAVE_DIR_PATH = "./games/ninswitch/imgs"
global save_individual_fame, allowReset, bypass
save_individual_fame = False
allowReset = True
bypass = False

# ----------------------------------------------------

CONTROLLER_DC_GAME_DETECT = [
    ((375, 204), (204, 204, 204)),
    ((641, 202), (204, 204, 204)),
    ((887, 203), (204, 204, 204)),
    ((795, 475), (28, 148, 0)),
    ((498, 475), (28, 148, 0)),
    ((443, 372), (16, 16, 16)),
    ((823, 367), (16, 16, 16)),
    ((636, 521), (207, 207, 207)),
]

CONTROLLER_DC_INPUT_NEEDED = [
    ((427, 87), (254, 254, 254)),
    ((572, 107), (255, 254, 255)),
    ((657, 85), (252, 250, 251)),
    ((699, 106), (238, 238, 238)),
    ((789, 79), (249, 250, 252)),
    ((802, 96), (254, 254, 252)),
    ((830, 95), (255, 254, 255)),
    ((528, 241), (48, 86, 255)),
    ((498, 264), (48, 85, 254)),
    ((587, 243), (50, 84, 254)),
    ((616, 257), (40, 87, 255)),
    ((542, 594), (187, 193, 215)),
    ((570, 591), (187, 197, 222)),
    ((598, 690), (252, 252, 252)),
    ((1014, 691), (255, 255, 255)),
]

CONTROLLER_DC_RECONNECT = [
    ((426, 88), (253, 251, 252)),
    ((571, 107), (255, 255, 255)),
    ((657, 85), (252, 250, 251)),
    ((698, 106), (245, 245, 245)),
    ((790, 79), (251, 255, 254)),
    ((830, 95), (255, 254, 255)),
    ((802, 96), (254, 254, 252)),
    ((499, 260), (52, 82, 255)),
    ((525, 243), (45, 86, 255)),
    ((588, 242), (48, 87, 253)),
    ((617, 259), (45, 86, 255)),
    ((614, 364), (108, 213, 0)),
    ((604, 420), (237, 237, 237)),
    ((619, 440), (224, 224, 224)),
    ((656, 441), (231, 231, 231)),
    ((631, 418), (52, 52, 52)),
    ((590, 458), (76, 76, 76)),
    ((687, 462), (76, 76, 76)),
    ((475, 391), (255, 255, 255)),
    ((754, 405), (255, 255, 255)),
    ((544, 592), (32, 79, 243)),
    ((573, 591), (44, 80, 254)),
    ((597, 689), (255, 254, 255)),
    ((1012, 690), (253, 253, 253)),
]

# ----------------------------------------------------

GAME_MAIN_MENU = [
    ((233, 188), (222, 209, 203)),
    ((258, 135), (192, 183, 176)),
    ((293, 156), (204, 193, 187)),
    ((350, 104), (178, 171, 163)),
    ((333, 177), (213, 204, 197)),
    ((380, 210), (45, 45, 45)),
    ((386, 108), (180, 173, 165)),
    ((437, 107), (191, 184, 176)),
    ((489, 210), (45, 45, 45)),
    ((600, 225), (13, 15, 14)),
    ((542, 202), (45, 45, 43)),
    ((561, 103), (179, 170, 163)),
    ((620, 101), (178, 171, 163)),
    ((655, 212), (45, 45, 45)),
    ((767, 104), (179, 172, 164)),
    ((720, 204), (45, 45, 45)),
    ((821, 115), (10, 14, 15)),
    ((849, 116), (9, 13, 14)),
    ((812, 211), (44, 44, 44)),
    ((861, 210), (45, 45, 45)),
    ((901, 102), (179, 170, 163)),
    ((988, 103), (178, 171, 163)),
    ((507, 369), (204, 204, 204)),
    ((502, 465), (204, 204, 204)),
    ((1052, 620), (28, 148, 0)),
]

GAME_MAIN_MENU_WORLD = [
    ((534, 150), (204, 204, 204)),
    ((780, 201), (28, 148, 0)),
    ((469, 200), (28, 148, 0)),
    ((238, 95), (80, 82, 81)),
    ((1042, 97), (84, 84, 84)),
    ((626, 640), (204, 204, 204)),
]

GAME_PAUSE_MENU = [
    ((138, 58), (179, 170, 163)),
    ((108, 124), (210, 199, 193)),
    ((157, 106), (205, 196, 189)),
    ((204, 60), (179, 172, 164)),
    ((190, 123), (216, 205, 199)),
    ((230, 124), (216, 205, 199)),
    ((230, 60), (181, 177, 168)),
    ((270, 58), (179, 170, 161)),
    ((267, 124), (215, 206, 199)),
    ((306, 126), (218, 207, 201)),
    ((323, 61), (180, 173, 165)),
    ((354, 59), (180, 171, 164)),
    ((399, 59), (180, 171, 164)),
    ((396, 91), (198, 187, 181)),
    ((398, 128), (220, 209, 203)),
    ((341, 126), (213, 206, 200)),
    ((425, 124), (216, 205, 199)),
    ((479, 126), (217, 208, 199)),
    ((435, 95), (199, 190, 183)),
    ((470, 61), (180, 173, 167)),
    ((430, 58), (178, 171, 165)),
    ((496, 63), (183, 176, 168)),
    ((545, 59), (180, 170, 168)),
    ((552, 126), (218, 207, 201)),
    ((526, 91), (198, 187, 181)),
    ((508, 126), (218, 209, 202)),
    ((585, 123), (216, 205, 199)),
    ((574, 61), (180, 173, 167)),
    ((623, 58), (178, 171, 163)),
    ((622, 125), (217, 206, 204)),
    ((662, 118), (214, 203, 197)),
    ((653, 63), (183, 173, 164)),
    ((692, 59), (179, 172, 164)),
    ((701, 93), (198, 189, 182)),
    ((762, 122), (215, 204, 198)),
    ((723, 60), (179, 172, 164)),
    ((772, 57), (177, 170, 160)),
    ((155, 326), (28, 148, 0)),
    ((410, 326), (28, 148, 0)),
    ((173, 413), (204, 204, 204)),
    ((373, 404), (204, 204, 204)),
    ((157, 484), (204, 204, 204)),
    ((391, 496), (204, 204, 204)),
    ((158, 574), (204, 204, 204)),
    ((410, 573), (204, 204, 204)),
    ((280, 286), (92, 92, 92)),
    ((276, 614), (94, 94, 94)),
    ((58, 451), (95, 95, 95)),
    ((506, 453), (93, 93, 93)),
    ((628, 587), (78, 78, 78)),
    ((647, 586), (80, 80, 80)),
    ((704, 602), (204, 204, 204)),
    ((698, 566), (204, 204, 204)),
]

GAME_SETTINGS_MENU = [
    ((32, 31), (204, 204, 204)),
    ((343, 27), (204, 204, 204)),
    ((704, 22), (204, 204, 204)),
    ((1194, 18), (204, 204, 204)),
    ((496, 427), (203, 204, 206)),
    ((1264, 216), (205, 204, 202)),
    ((26, 330), (28, 148, 0)),
    ((402, 126), (204, 204, 204)),
    ((398, 175), (204, 204, 204)),
    ((421, 389), (204, 204, 204)),
    ((422, 480), (204, 204, 204)),
    ((425, 616), (204, 204, 204)),
    ((427, 661), (204, 204, 204)),
]

HOME_MENU = [
    ((89, 681), (255, 255, 255)),
    ((72, 695), (255, 255, 255)),
    ((107, 696), (255, 255, 255)),
    ((970, 689), (253, 253, 253)),
    ((1135, 682), (255, 255, 255)),
    ((1204, 21), (52, 52, 52)),
    ((647, 19), (52, 52, 52)),
    ((57, 12), (52, 52, 52)),
    ((71, 79), (254, 11, 0)),
]

SETTINGS_MENU = [
    ((28, 32), (52, 52, 52)),
    ((663, 22), (52, 52, 52)),
    ((1207, 27), (52, 52, 52)),
    ((1166, 683), (253, 253, 253)),
    ((1157, 716), (52, 52, 52)),
    ((1036, 684), (249, 249, 249)),
    ((1027, 705), (52, 52, 52)),
    ((647, 683), (52, 52, 52)),
    ((89, 679), (255, 255, 255)),
    ((50, 693), (52, 52, 52)),
]

# ----------------------------------------------------

INVENTORY_CONDENCED = [
    ((683, 127), (199, 201, 198)),
    ((751, 125), (147, 147, 147)),
    ((596, 110), (81, 81, 81)),
    ((920, 107), (81, 81, 81)),
    ((853, 155), (204, 204, 204)),
    ((420, 152), (201, 201, 201)),
    ((417, 564), (203, 203, 203)),
    ((864, 564), (205, 205, 205)),
    ((775, 334), (204, 204, 204)),
    ((791, 233), (147, 147, 147)),
    ((595, 175), (7, 7, 7)),
    ((490, 321), (7, 7, 7)),
]

INVENTORY_EXTENDED = [
    ((881, 126), (147, 146, 141)),
    ((954, 125), (204, 204, 204)),
    ((802, 107), (81, 81, 81)),
    ((1119, 109), (82, 82, 82)),
    ((1043, 157), (204, 204, 204)),
    ((1060, 556), (205, 205, 205)),
    ((619, 563), (201, 201, 201)),
    ((599, 343), (103, 103, 103)),
    ((622, 152), (204, 204, 204)),
    ((153, 121), (83, 83, 83)),
    ((642, 119), (81, 81, 81)),
    ((217, 569), (207, 207, 207)),
    ((59, 602), (68, 68, 68)),
]

# ----------------------------------------------------

YOU_DIED_LEFT = [
    ((535, 202), (253, 253, 253)),
    ((566, 196), (253, 254, 255)),
    ((557, 206), (253, 253, 251)),
    ((567, 217), (252, 254, 251)),
    ((578, 207), (255, 253, 255)),
    ((588, 205), (253, 255, 254)),
    ((609, 216), (255, 254, 255)),
    ((643, 207), (253, 254, 255)),
    ((663, 201), (248, 247, 245)),
    ((655, 217), (255, 253, 255)),
    ((674, 185), (255, 254, 251)),
    ((674, 203), (255, 254, 255)),
    ((685, 207), (254, 255, 255)),
    ((706, 217), (255, 255, 253)),
    ((707, 200), (255, 250, 248)),
    ((717, 208), (251, 253, 252)),
    ((739, 196), (254, 254, 254)),
    ((739, 215), (255, 254, 249)),
    ((749, 217), (253, 251, 252)),
    ((749, 195), (255, 255, 255)),
    ((354, 388), (28, 148, 0)),
    ((565, 391), (28, 148, 0)),
    ((446, 395), (230, 255, 211)),
    ((295, 361), (247, 255, 250)),
    ((611, 427), (251, 253, 240)),
    ((585, 557), (85, 81, 80)),
    ((604, 557), (79, 79, 79)),
    ((724, 386), (204, 204, 204)),
    ((943, 389), (204, 204, 204)),
    ((828, 425), (109, 109, 111)),
]

YOU_DIED_RIGHT = [
    ((525, 185), (255, 253, 250)),
    ((546, 185), (250, 249, 247)),
    ((535, 215), (255, 254, 250)),
    ((556, 211), (255, 251, 248)),
    ((579, 202), (255, 249, 247)),
    ((589, 195), (255, 251, 245)),
    ((610, 217), (255, 255, 255)),
    ((643, 210), (251, 255, 254)),
    ((664, 186), (255, 252, 248)),
    ((675, 185), (255, 249, 248)),
    ((675, 216), (243, 243, 243)),
    ((707, 217), (255, 250, 250)),
    ((690, 196), (253, 252, 255)),
    ((750, 217), (255, 254, 255)),
    ((749, 186), (255, 251, 251)),
    ((347, 393), (204, 204, 204)),
    ((540, 391), (204, 204, 204)),
    ((450, 425), (110, 108, 113)),
    ((584, 557), (82, 80, 81)),
    ((606, 555), (79, 79, 79)),
    ((723, 394), (28, 148, 0)),
    ((959, 396), (28, 148, 0)),
    ((668, 362), (239, 255, 241)),
    ((984, 427), (255, 254, 242)),
]

SURE_QUIT_CONFIRM = [
    ((367, 158), (202, 207, 203)),
    ((451, 282), (16, 16, 16)),
    ((684, 156), (204, 204, 204)),
    ((809, 289), (16, 16, 16)),
    ((904, 151), (204, 204, 204)),
    ((465, 436), (204, 204, 204)),
    ((797, 432), (204, 204, 204)),
    ((800, 517), (28, 148, 0)),
    ((521, 533), (28, 148, 0)),
    ((958, 394), (204, 204, 204)),
    ((318, 388), (204, 204, 204)),
    ((369, 568), (204, 203, 201)),
    ((911, 567), (204, 205, 209)),
]

SURE_QUIT_CANCEL = [
    ((367, 158), (202, 207, 203)),
    ((451, 282), (16, 16, 16)),
    ((684, 156), (204, 204, 204)),
    ((809, 289), (16, 16, 16)),
    ((904, 151), (204, 204, 204)),
    ((465, 436), (204, 204, 204)),
    ((797, 432), (204, 204, 204)),
    ((800, 517), (28, 148, 0)),
    ((521, 533), (28, 148, 0)),
    ((958, 394), (204, 204, 204)),
    ((318, 388), (204, 204, 204)),
    ((369, 568), (204, 203, 201)),
    ((911, 567), (204, 205, 209)),
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
                "minus": NSSwitch(self.nsg, NSButton.MINUS),
                "left_stick": NSSwitch(self.nsg, NSButton.LEFT_STICK),
                "right_stick": NSSwitch(self.nsg, NSButton.RIGHT_STICK),
                "capture_frame": CaptureScreen(),
                "reset_trinkets": reset_trinkets(),
            },
        )
        self.io.register_inputs(
            {
                "home": NSSwitch(self.nsg, NSButton.HOME),
                "capture": NSSwitch(self.nsg, NSButton.CAPTURE),
                "debug_switch": debug_switch(),
                "plus": NSSwitch(self.nsg, NSButton.PLUS),
            },
            admin=True,
        )

        self.curUser = "[{'id': 'SurrogateTVRePlayrobot', 'streamer': 'SurrogateTVRePlaystreamer', 'queueOptionId': '0', 'seat': 0, 'set': 0, 'enabled': True, 'username': 'dummydummydummydummydummydummydummyd'}]"
        self.userID = "eu-west-1:dummydummydummydummydummydummydummyd"
        # init image rec
        self.image_rec_task = asyncio.create_task(self.image_rec_main())
        self.image_rec_task.add_done_callback(self.image_rec_done_cb)

        # init frame saving
        logging.info(f"SAVING FRAMES TO {SAVE_DIR_PATH}")
        Path(SAVE_DIR_PATH).mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------

    async def on_start(self):
        self.curUser = self.players
        player = json.loads(json.dumps(self.players))[0]['username']

        req = requests.get("https://g9b1fyald3.execute-api.eu-west-1.amazonaws.com/master/users?search="+str(player)).text
        uid = json.loads(req)['result'][0]['userId']
        self.userID = uid

# ----------------------------------------------------

    async def on_pre_game(self):
        self.io.send_pre_game_not_ready()
        self.nsg.press(NSButton.B)
        await asyncio.sleep(0.1)
        self.nsg.release(NSButton.B)
        await asyncio.sleep(1)
        self.io.send_pre_game_ready()

# ----------------------------------------------------

    async def on_prepare(self):
        pi.write(nsg_reset, ON)
        await asyncio.sleep(0.5)
        pi.write(nsg_reset, OFF)
        await asyncio.sleep(2)

        self.prepare = True

        while self.prepare: 
            await asyncio.sleep(3)

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
        self.knownIndex = 0

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
        controller_dc_game_detec = get_pixel_detector(CONTROLLER_DC_GAME_DETECT, 50)
        controller_dc_input_needed = get_pixel_detector(CONTROLLER_DC_INPUT_NEEDED, 50)
        controller_dc_reconnect = get_pixel_detector(CONTROLLER_DC_RECONNECT, 50)

        game_pause_menu = get_pixel_detector(GAME_PAUSE_MENU, 75)
        game_settings_menu = get_pixel_detector(GAME_SETTINGS_MENU, 50)

        inventory_condenced = get_pixel_detector(INVENTORY_CONDENCED, 50)
        inventory_extended = get_pixel_detector(INVENTORY_EXTENDED, 50)

        game_main_menu = get_pixel_detector(GAME_MAIN_MENU, 50)
        game_main_menu_world = get_pixel_detector(GAME_MAIN_MENU_WORLD, 50)
        home_menu = get_pixel_detector(HOME_MENU, 50)
        settings_menu = get_pixel_detector(SETTINGS_MENU, 50)

        you_died_left = get_pixel_detector(YOU_DIED_LEFT, 50)
        you_died_right = get_pixel_detector(YOU_DIED_RIGHT, 50)
        sure_quit_confirm = get_pixel_detector(SURE_QUIT_CONFIRM, 50)
        sure_quit_cancel = get_pixel_detector(SURE_QUIT_CANCEL, 50)

        # loop through frames
        i = 0
        z = 0
        async for frame in self.cap.frames():
            # detect trigger
            if i%30==0 and (controller_dc_game_detec(frame) or controller_dc_input_needed(frame) or controller_dc_reconnect(frame) or you_died_left(frame) or you_died_right(frame) or sure_quit_cancel(frame) or sure_quit_confirm(frame)) and not DEBUG:
                pi.write(nsg_reset, ON)
                await asyncio.sleep(0.5)
                pi.write(nsg_reset, OFF)
                await asyncio.sleep(1)
            try:
                if (controller_dc_game_detec(frame) or controller_dc_input_needed(frame) or controller_dc_reconnect(frame)) and not DEBUG:
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
                if (controller_dc_game_detec(frame) or controller_dc_input_needed(frame) or controller_dc_reconnect(frame)) and not DEBUG:
                    self.nsg.press(NSButton.A)
                    await asyncio.sleep(0.1)
                    self.nsg.release(NSButton.A)
                    await asyncio.sleep(2)
                    self.nsg.press(NSButton.A)
                    await asyncio.sleep(0.1)
                    self.nsg.release(NSButton.A)
                    await asyncio.sleep(2)

            try:
                if (you_died_left(frame)) and not DEBUG:
                    self.io.disable_input(0)
                    self.nsg.press(NSButton.A)
                    await asyncio.sleep(0.1)
                    self.nsg.release(NSButton.A)
                    await asyncio.sleep(2)
                    self.io.enable_input(0)

                if (you_died_right(frame)) and not DEBUG:
                    self.io.disable_input(0)
                    self.nsg.leftXAxis(0)
                    self.nsg.leftYAxis(128)
                    await asyncio.sleep(0.1)
                    self.nsg.leftXAxis(128)
                    self.nsg.leftYAxis(128)
                    await asyncio.sleep(0.1)
                    self.nsg.press(NSButton.A)
                    await asyncio.sleep(0.1)
                    self.nsg.release(NSButton.A)
                    await asyncio.sleep(2)
                    self.io.enable_input(0)

                if(sure_quit_confirm(frame) or sure_quit_cancel(frame)) and not DEBUG:
                    self.io.disable_input(0)
                    self.nsg.press(NSButton.B)
                    await asyncio.sleep(0.1)
                    self.nsg.release(NSButton.B)
                    await asyncio.sleep(2)
                    self.io.enable_input(0)

            except:
                if (you_died_left(frame)) and not DEBUG:
                    self.nsg.press(NSButton.A)
                    await asyncio.sleep(0.1)
                    self.nsg.release(NSButton.A)
                    await asyncio.sleep(2)

                if (you_died_right(frame)) and not DEBUG:
                    self.nsg.leftXAxis(0)
                    self.nsg.leftYAxis(128)
                    await asyncio.sleep(0.1)
                    self.nsg.leftXAxis(128)
                    self.nsg.leftYAxis(128)
                    await asyncio.sleep(0.1)
                    self.nsg.press(NSButton.A)
                    await asyncio.sleep(0.1)
                    self.nsg.release(NSButton.A)
                    await asyncio.sleep(2)

                if(sure_quit_confirm(frame) or sure_quit_cancel(frame)) and not DEBUG:
                    self.nsg.press(NSButton.B)
                    await asyncio.sleep(0.1)
                    self.nsg.release(NSButton.B)
                    await asyncio.sleep(2)


            # Get to pause frames...Update as needed
            if (self.prepare and not (game_pause_menu(frame)) and not LOCKED) and not DEBUG:
                if z % 3 == 2:
                    self.nsg.press(NSButton.A)
                    await asyncio.sleep(0.1)
                    self.nsg.release(NSButton.A)
                    await asyncio.sleep(1)
                    self.nsg.press(NSButton.B)
                    await asyncio.sleep(0.1)
                    self.nsg.release(NSButton.B)
                    await asyncio.sleep(1)
                elif z % 3 == 1:
                    self.nsg.press(NSButton.PLUS)
                    await asyncio.sleep(0.1)
                    self.nsg.release(NSButton.PLUS)
                    await asyncio.sleep(2)
                z += 1
            elif not LOCKED:
                z = 0
                self.prepare = False

            # lock trigger
            try:
                if (game_main_menu(frame) or game_main_menu_world(frame) or home_menu(frame) or settings_menu(frame)) and not LOCKED and not DEBUG:
                    self.io.disable_input(0)
                    if not (i<100 or bypass):
                        player = json.loads(json.dumps(self.curUser))[0]['username']
                        msg = "MINECRAFT\nGame locked due to either being at home screen or capture card bars. \nUser's information are as follows:\n> "+player+"\n> "+self.userID
                        bot.send_message(chat_id, msg, parse_mode="markdown")
                        LOCKED = True
                        self.nsg.end()
                        self.prepare = False
                    else:
                        msg = "MINECRAFT\nBypass utilized...Take action to get to a proper menu before something messes up."
                        bot.send_message(chat_id, msg, parse_mode="markdown")
                        bypass = True
                        DEBUG = True
                        LOCKED = True
            except:
                if (game_main_menu(frame) or game_main_menu_world(frame) or home_menu(frame) or settings_menu(frame)) and not LOCKED and not DEBUG:
                    if not (i<100 or bypass):
                        player = json.loads(json.dumps(self.curUser))[0]['username']
                        msg = "MINECRAFT\nGame locked due to either being at home screen or capture card bars. \nUser's information are as follows:\n> "+player+"\n> "+self.userID
                        bot.send_message(chat_id, msg, parse_mode="markdown")
                        LOCKED = True
                        self.nsg.end()
                        self.prepare = False
                    else:
                        msg = "MINECRAFT\nBypass utilized...Take action to get to a proper menu before something messes up."
                        bot.send_message(chat_id, msg, parse_mode="markdown")
                        bypass = True
                        DEBUG = True
                        LOCKED = True

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
