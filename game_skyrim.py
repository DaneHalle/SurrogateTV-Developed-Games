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
B_MENU = [
    ((82, 614), (101, 103, 98)),
    ((643, 614), (106, 106, 104)),
    ((1128, 614), (101, 101, 99)),
    ((476, 359), (137, 137, 135)),
    ((800, 359), (140, 141, 136)),
    ((640, 284), (152, 153, 148)),
    ((641, 432), (130, 131, 125)),
    ((664, 359), (147, 148, 143)),
    ((616, 358), (150, 151, 146)),
    ((640, 335), (139, 140, 134)),
    ((640, 383), (144, 145, 140)),
    ((643, 352), (143, 144, 138)),
    ((634, 364), (144, 145, 140)),
]

CONTROLLER_DC_INPUT_NEEDED = [
    ((427, 87), (253, 255, 254)),
    ((572, 107), (255, 253, 254)),
    ((657, 86), (254, 252, 255)),
    ((698, 106), (245, 246, 248)),
    ((789, 80), (253, 254, 255)),
    ((829, 96), (254, 254, 255)),
    ((802, 95), (255, 255, 255)),
    ((496, 254), (41, 88, 254)),
    ((527, 252), (48, 86, 255)),
    ((586, 251), (47, 84, 253)),
    ((617, 253), (46, 87, 255)),
    ((540, 591), (186, 193, 219)),
    ((555, 613), (184, 194, 219)),
    ((569, 591), (187, 194, 222)),
    ((597, 677), (253, 253, 253)),
    ((597, 689), (255, 255, 255)),
    ((639, 689), (254, 255, 255)),
    ((651, 678), (254, 255, 255)),
    ((1014, 677), (254, 252, 253)),
    ((1013, 689), (255, 255, 255)),
    ((1055, 690), (247, 247, 247)),
    ((1067, 677), (253, 253, 253)),
]

CONTROLLER_DC_RECONNECT = [
    ((427, 87), (253, 255, 254)),
    ((571, 107), (255, 253, 254)),
    ((657, 86), (254, 252, 255)),
    ((698, 106), (245, 246, 248)),
    ((789, 79), (251, 252, 254)),
    ((802, 95), (255, 255, 255)),
    ((829, 95), (247, 247, 249)),
    ((498, 251), (47, 85, 255)),
    ((526, 248), (47, 85, 254)),
    ((586, 247), (47, 84, 253)),
    ((614, 253), (44, 81, 250)),
    ((480, 366), (255, 255, 255)),
    ((636, 486), (255, 255, 255)),
    ((810, 337), (255, 255, 255)),
    ((589, 453), (76, 76, 76)),
    ((637, 406), (52, 52, 52)),
    ((689, 453), (76, 76, 76)),
    ((604, 411), (237, 237, 237)),
    ((619, 430), (241, 241, 241)),
    ((655, 430), (239, 239, 239)),
    ((615, 340), (110, 220, 1)),
    ((632, 340), (217, 217, 217)),
    ((648, 340), (217, 217, 217)),
    ((663, 340), (216, 216, 216)),
    ((541, 593), (44, 85, 255)),
    ((555, 612), (47, 85, 254)),
    ((568, 589), (47, 88, 255)),
    ((597, 677), (253, 253, 253)),
    ((597, 689), (255, 255, 255)),
    ((639, 689), (254, 255, 255)),
    ((650, 678), (248, 250, 249)),
    ((1012, 677), (255, 254, 255)),
    ((1013, 690), (255, 255, 255)),
    ((1054, 690), (255, 255, 255)),
    ((1066, 678), (251, 251, 251)),
]

CREATION_BODY = [
    ((221, 375), (167, 170, 161)),
    ((436, 377), (250, 252, 247)),
    ((456, 377), (244, 245, 237)),
    ((652, 39), (245, 247, 246)),
    ((659, 48), (246, 250, 249)),
    ((628, 41), (245, 245, 243)),
    ((587, 43), (227, 232, 228)),
    ((700, 43), (215, 220, 214)),
    ((42, 689), (241, 241, 241)),
    ((235, 46), (109, 116, 109)),
    ((1047, 47), (77, 86, 83)),
]

CREATION_BROW = [
    ((436, 390), (254, 255, 250)),
    ((456, 377), (252, 255, 255)),
    ((220, 385), (245, 242, 235)),
    ((446, 367), (246, 251, 247)),
    ((587, 43), (222, 228, 226)),
    ((701, 43), (181, 190, 187)),
    ((628, 42), (251, 253, 252)),
    ((637, 40), (244, 248, 247)),
    ((644, 46), (251, 253, 252)),
    ((657, 41), (248, 253, 249)),
    ((234, 46), (118, 129, 131)),
    ((1047, 47), (132, 151, 155)),
    ((42, 689), (236, 236, 236)),
]

CREATION_EYES = [
    ((456, 377), (251, 255, 254)),
    ((437, 377), (252, 255, 248)),
    ((443, 385), (238, 240, 235)),
    ((446, 367), (246, 251, 247)),
    ((221, 389), (182, 182, 174)),
    ((630, 41), (252, 254, 253)),
    ((641, 48), (249, 253, 252)),
    ((648, 43), (254, 255, 255)),
    ((657, 45), (207, 213, 213)),
    ((701, 43), (181, 190, 187)),
    ((586, 43), (186, 192, 190)),
    ((233, 46), (152, 166, 167)),
    ((1047, 47), (132, 151, 155)),
]

CREATION_FACE = [
    ((42, 689), (236, 236, 236)),
    ((456, 377), (252, 255, 255)),
    ((436, 377), (242, 245, 236)),
    ((436, 389), (254, 255, 250)),
    ((220, 395), (240, 240, 228)),
    ((630, 41), (252, 254, 253)),
    ((643, 43), (255, 255, 255)),
    ((648, 46), (248, 252, 251)),
    ((656, 43), (188, 190, 189)),
    ((587, 44), (197, 203, 201)),
    ((700, 43), (210, 219, 216)),
    ((226, 47), (163, 178, 181)),
    ((1047, 46), (162, 181, 187)),
]

CREATION_HAIR = [
    ((456, 377), (251, 255, 254)),
    ((436, 377), (233, 236, 229)),
    ((442, 384), (196, 197, 192)),
    ((220, 393), (238, 240, 227)),
    ((42, 689), (237, 237, 237)),
    ((586, 43), (186, 192, 190)),
    ((701, 43), (181, 190, 187)),
    ((631, 41), (252, 255, 255)),
    ((648, 41), (251, 253, 252)),
    ((652, 45), (253, 255, 254)),
    ((656, 40), (249, 255, 253)),
]

CREATION_MOUTH = [
    ((456, 377), (251, 255, 254)),
    ((436, 389), (254, 255, 250)),
    ((437, 376), (254, 255, 251)),
    ((220, 394), (243, 243, 231)),
    ((43, 689), (200, 200, 200)),
    ((627, 46), (241, 243, 242)),
    ((640, 40), (254, 255, 255)),
    ((651, 48), (252, 255, 255)),
    ((656, 39), (252, 255, 255)),
    ((661, 39), (232, 237, 233)),
    ((700, 43), (210, 219, 216)),
    ((586, 43), (186, 192, 190)),
    ((229, 51), (119, 134, 137)),
    ((1050, 49), (127, 145, 149)),
]

CREATION_RACE = [
    ((456, 377), (252, 255, 253)),
    ((430, 378), (240, 242, 237)),
    ((436, 377), (232, 235, 228)),
    ((442, 384), (195, 195, 193)),
    ((220, 386), (245, 245, 235)),
    ((42, 690), (244, 244, 242)),
    ((629, 42), (243, 247, 246)),
    ((644, 40), (243, 247, 246)),
    ((657, 43), (197, 199, 198)),
    ((700, 43), (212, 221, 218)),
    ((587, 43), (222, 228, 226)),
    ((229, 50), (156, 171, 174)),
    ((1050, 50), (121, 140, 144)),
]

GAME_MAIN_MENU = [
    ((96, 682), (182, 188, 186)),
    ((75, 684), (184, 188, 187)),
    ((58, 673), (175, 181, 179)),
    ((57, 643), (186, 190, 189)),
    ((76, 627), (184, 188, 187)),
    ((95, 628), (179, 183, 182)),
    ((112, 641), (181, 187, 187)),
    ((459, 297), (176, 196, 168)),
    ((446, 183), (73, 75, 61)),
    ((358, 304), (30, 31, 23)),
    ((560, 304), (28, 30, 25)),
    ((461, 574), (24, 25, 17)),
    ((1058, 117), (7, 7, 7)),
    ((771, 344), (0, 0, 0)),
    ((979, 635), (8, 8, 6)),
]

GAME_MAIN_MENU_2 = [
    ((96, 682), (190, 194, 195)),
    ((75, 682), (191, 195, 194)),
    ((60, 669), (192, 194, 193)),
    ((59, 642), (189, 193, 194)),
    ((76, 627), (191, 195, 196)),
    ((96, 627), (195, 196, 198)),
    ((111, 641), (197, 203, 201)),
    ((460, 298), (195, 213, 189)),
    ((446, 187), (85, 85, 77)),
    ((574, 293), (13, 15, 14)),
    ((339, 306), (29, 32, 25)),
    ((464, 569), (24, 25, 19)),
    ((1112, 164), (7, 7, 7)),
    ((945, 253), (7, 7, 7)),
    ((904, 555), (7, 7, 7)),
    ((812, 610), (7, 7, 7)),
    ((1097, 684), (252, 252, 252)),
]

HOME_MENU = [
    ((290, 54), (52, 52, 52)),
    ((29, 57), (52, 52, 52)),
    ((869, 56), (52, 52, 52)),
    ((1239, 38), (52, 52, 52)),
    ((1191, 574), (52, 52, 52)),
    ((127, 543), (52, 52, 52)),
    ((29, 688), (52, 52, 52)),
    ((584, 686), (52, 52, 52)),
    ((982, 678), (252, 252, 252)),
    ((1135, 683), (253, 253, 253)),
    ((90, 681), (255, 255, 255)),
    ((75, 662), (141, 242, 0)),
]

PLUS_GENERAL_STATS = [
    ((569, 70), (255, 255, 253)),
    ((717, 70), (253, 253, 251)),
    ((595, 70), (249, 249, 247)),
    ((600, 61), (245, 245, 245)),
    ((600, 77), (254, 254, 254)),
    ((608, 75), (248, 248, 248)),
    ((614, 63), (204, 204, 204)),
    ((619, 61), (197, 197, 195)),
    ((619, 77), (188, 188, 188)),
    ((628, 68), (254, 254, 252)),
    ((643, 73), (244, 244, 244)),
    ((649, 64), (246, 246, 244)),
    ((661, 64), (247, 247, 245)),
    ((671, 61), (254, 254, 252)),
    ((687, 61), (255, 255, 253)),
    ((677, 73), (236, 236, 236)),
    ((693, 67), (254, 254, 252)),
    ((439, 102), (92, 93, 88)),
    ((439, 592), (103, 104, 99)),
    ((704, 68), (11, 11, 9)),
]

PLUS_OPENING = [
    ((67, 634), (116, 120, 119)),
    ((652, 634), (105, 109, 108)),
    ((1087, 634), (118, 120, 117)),
    ((173, 594), (135, 139, 138)),
    ((1106, 593), (122, 126, 125)),
    ((411, 117), (106, 111, 105)),
    ((416, 576), (102, 107, 101)),
    ((238, 103), (130, 137, 130)),
    ((1039, 103), (111, 113, 108)),
    ((834, 69), (254, 255, 255)),
    ((980, 70), (250, 254, 253)),
    ((893, 70), (219, 221, 220)),
    ((881, 64), (237, 239, 238)),
    ((899, 65), (254, 255, 255)),
    ((909, 61), (251, 253, 252)),
    ((916, 69), (255, 255, 255)),
    ((932, 63), (241, 243, 242)),
    ((649, 68), (104, 108, 107)),
    ((671, 67), (109, 111, 110)),
    ((687, 68), (118, 120, 119)),
    ((600, 69), (116, 118, 117)),
    ((392, 64), (124, 126, 125)),
    ((368, 71), (113, 113, 113)),
    ((357, 69), (122, 122, 122)),
]

PLUS_SYSTEM_GEN = [
    ((169, 587), (112, 113, 108)),
    ((1111, 586), (120, 121, 115)),
    ((410, 113), (67, 67, 55)),
    ((415, 552), (81, 82, 77)),
    ((249, 103), (117, 117, 107)),
    ((987, 103), (107, 109, 106)),
    ((834, 70), (255, 255, 251)),
    ((981, 70), (250, 251, 246)),
    ((882, 76), (224, 225, 219)),
    ((884, 61), (253, 254, 248)),
    ((892, 74), (255, 255, 255)),
    ((895, 62), (251, 252, 247)),
    ((903, 61), (255, 255, 251)),
    ((901, 76), (244, 245, 240)),
    ((909, 61), (251, 252, 247)),
    ((909, 76), (255, 255, 253)),
    ((919, 69), (234, 234, 232)),
    ((932, 64), (249, 249, 247)),
    ((924, 73), (252, 252, 250)),
]

PLUS_QUESTS = [
    ((304, 69), (253, 253, 251)),
    ((451, 70), (255, 255, 251)),
    ((362, 66), (255, 255, 255)),
    ((368, 66), (254, 254, 254)),
    ((373, 61), (251, 251, 249)),
    ((373, 77), (248, 248, 248)),
    ((391, 61), (255, 255, 253)),
    ((399, 76), (236, 236, 234)),
    ((397, 64), (249, 249, 247)),
    ((458, 102), (101, 100, 95)),
    ((458, 591), (103, 102, 98)),
    ((420, 68), (14, 15, 10)),
]

PLUS_SYSTEM = [
    ((834, 70), (249, 250, 245)),
    ((981, 69), (232, 233, 228)),
    ((881, 62), (241, 241, 239)),
    ((892, 75), (247, 247, 245)),
    ((895, 62), (252, 252, 250)),
    ((900, 67), (255, 255, 253)),
    ((909, 61), (252, 252, 250)),
    ((916, 61), (239, 238, 234)),
    ((916, 77), (243, 243, 241)),
    ((933, 75), (254, 254, 252)),
    ((925, 65), (250, 250, 248)),
    ((413, 102), (93, 94, 89)),
    ((413, 592), (104, 105, 100)),
    ((856, 68), (13, 14, 9)),
]

PLUS_SYSTEM_2 = [
    ((834, 70), (252, 255, 255)),
    ((881, 65), (253, 253, 253)),
    ((885, 73), (249, 253, 252)),
    ((892, 73), (253, 255, 254)),
    ((899, 64), (252, 254, 253)),
    ((901, 76), (245, 249, 248)),
    ((910, 61), (251, 253, 252)),
    ((916, 74), (254, 255, 255)),
    ((933, 75), (254, 255, 255)),
    ((980, 70), (251, 255, 254)),
]

SETTINGS_MENU = [
    ((88, 49), (52, 52, 52)),
    ((103, 50), (254, 254, 254)),
    ((554, 55), (52, 52, 52)),
    ((794, 51), (52, 52, 52)),
    ((1152, 44), (52, 52, 52)),
    ((1165, 679), (254, 254, 254)),
    ((1130, 700), (52, 52, 52)),
    ((1036, 681), (251, 251, 251)),
    ((954, 688), (52, 52, 52)),
    ((687, 685), (52, 52, 52)),
    ((395, 689), (52, 52, 52)),
    ((88, 681), (245, 245, 245)),
    ((89, 702), (52, 52, 52)),
    ((50, 683), (52, 52, 52)),
    ((74, 662), (140, 248, 5)),
    ((105, 661), (116, 116, 116)),
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
        self.started = False
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
                "plus": NSSwitch(self.nsg, NSButton.PLUS),
            },
        )
        self.io.register_inputs(
            {
                "home": NSSwitch(self.nsg, NSButton.HOME),
                "capture": NSSwitch(self.nsg, NSButton.CAPTURE),
                "debug_switch": debug_switch(),
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
        self.started = True
        self.prepare = False

# ----------------------------------------------------

    async def on_pre_game(self):
        self.io.send_pre_game_not_ready()
        self.nsg.press(NSButton.B)
        await asyncio.sleep(0.1)
        self.nsg.release(NSButton.B)
        await asyncio.sleep(0.5)
        self.nsg.press(NSButton.Y)
        await asyncio.sleep(0.1)
        self.nsg.release(NSButton.Y)
        await asyncio.sleep(0.5)
        self.io.send_pre_game_ready()

# ----------------------------------------------------

    async def on_prepare(self):
        pi.write(nsg_reset, ON)
        await asyncio.sleep(0.5)
        pi.write(nsg_reset, OFF)
        await asyncio.sleep(2)

        self.prepare = True
        self.started = False

        while self.prepare: 
            await asyncio.sleep(3)

# ----------------------------------------------------

    async def on_finish(self):
        self.prepare = True
        self.started = False
        self.io.disable_inputs()
        global LOCKED
        if not LOCKED:
            self.nsg.releaseAll()
            self.nsg.rightYAxis(128)
            self.nsg.rightXAxis(128)
            self.nsg.leftYAxis(128)
            self.nsg.leftXAxis(128)   

        self.io.send_score(score=1, seat=0, final_score=True)

        self.knownIndex = 0

# ----------------------------------------------------

    async def on_exit(self, reason, exception):
        # end controls
        self.io.disable_inputs() 
        global LOCKED
        if not LOCKED:
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


        controller_dc_input_needed = get_pixel_detector(CONTROLLER_DC_INPUT_NEEDED, 150)
        controller_dc_reconnect = get_pixel_detector(CONTROLLER_DC_RECONNECT, 100)

        b_menu = get_pixel_detector(B_MENU, 150)
        creation_body = get_pixel_detector(CREATION_BODY, 150)
        creation_brow = get_pixel_detector(CREATION_BROW, 150)
        creation_eyes = get_pixel_detector(CREATION_EYES, 150)
        creation_face = get_pixel_detector(CREATION_FACE, 150)
        creation_hair = get_pixel_detector(CREATION_HAIR, 150)
        creation_mouth = get_pixel_detector(CREATION_MOUTH, 150)
        creation_race = get_pixel_detector(CREATION_RACE, 150)

        plus_opening = get_pixel_detector(PLUS_OPENING, 200) # Need to allow for reasons
        plus_system = get_pixel_detector(PLUS_SYSTEM_GEN, 200) # Avoid if possible
        plus_system_2 = get_pixel_detector(PLUS_SYSTEM_2, 200)

        plus_general_stats = get_pixel_detector(PLUS_GENERAL_STATS, 200) # Disable going to System
        plus_quests = get_pixel_detector(PLUS_QUESTS, 200) # Disable going to system

        game_main_menu = get_pixel_detector(GAME_MAIN_MENU, 150)
        game_main_menu_2 = get_pixel_detector(GAME_MAIN_MENU_2, 150)
        home_menu = get_pixel_detector(HOME_MENU, 150)
        settings_menu = get_pixel_detector(SETTINGS_MENU, 150)

        # loop through frames
        i = 0
        z = 0
        async for frame in self.cap.frames():
            # detect trigger
            if i%30==0 and (controller_dc_input_needed(frame) or controller_dc_reconnect(frame)) and not DEBUG:
                pi.write(nsg_reset, ON)
                await asyncio.sleep(0.5)
                pi.write(nsg_reset, OFF)
                await asyncio.sleep(1)
            try:
                if (controller_dc_input_needed(frame) or controller_dc_reconnect(frame)) and not DEBUG:
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
                if (controller_dc_input_needed(frame) or controller_dc_reconnect(frame)) and not DEBUG:
                    self.nsg.press(NSButton.A)
                    await asyncio.sleep(0.1)
                    self.nsg.release(NSButton.A)
                    await asyncio.sleep(2)
                    self.nsg.press(NSButton.A)
                    await asyncio.sleep(0.1)
                    self.nsg.release(NSButton.A)
                    await asyncio.sleep(2)

            try:
                if (self.started and (plus_system(frame) or plus_system_2(frame))) and not DEBUG:
                    self.io.disable_input(0)
                    self.nsg.press(NSButton.LEFT_THROTTLE)
                    await asyncio.sleep(0.1)
                    self.nsg.release(NSButton.LEFT_THROTTLE)
                    await asyncio.sleep(1)
                    self.nsg.press(NSButton.B)
                    await asyncio.sleep(0.1)
                    self.nsg.release(NSButton.B)
                    await asyncio.sleep(1)
                    self.io.enable_input(0)
            except:
                if (self.started and (plus_system(frame) or plus_system_2(frame))) and not DEBUG:
                    self.nsg.press(NSButton.LEFT_THROTTLE)
                    await asyncio.sleep(0.1)
                    self.nsg.release(NSButton.LEFT_THROTTLE)
                    await asyncio.sleep(1)
                    self.nsg.press(NSButton.B)
                    await asyncio.sleep(0.1)
                    self.nsg.release(NSButton.B)
                    await asyncio.sleep(1)

            if (self.prepare and b_menu(frame) and not LOCKED and not DEBUG):
                self.nsg.press(NSButton.B)
                await asyncio.sleep(0.1)
                self.nsg.release(NSButton.B)

            # Get to pause frames...Update as needed
            if (self.prepare and not ((plus_system(frame) or plus_system_2(frame) or creation_body(frame) or creation_brow(frame) or creation_eyes(frame) or creation_face(frame) or creation_hair(frame) or creation_mouth(frame) or creation_race(frame) or plus_general_stats(frame) or plus_quests(frame))) and not LOCKED) and not DEBUG:
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
                    self.nsg.rightXAxis(255)
                    self.nsg.rightYAxis(128)
                    await asyncio.sleep(0.5)
                    self.nsg.rightXAxis(128)
                    self.nsg.rightYAxis(128)
                    await asyncio.sleep(1)
                    self.nsg.press(NSButton.PLUS)
                    await asyncio.sleep(0.1)
                    self.nsg.release(NSButton.PLUS)
                    await asyncio.sleep(1)
                    self.nsg.press(NSButton.LEFT_THROTTLE)
                    await asyncio.sleep(0.1)
                    self.nsg.release(NSButton.LEFT_THROTTLE)
                    await asyncio.sleep(1)
                z += 1
            elif not LOCKED:
                z = 0
                self.prepare = False


            # lock trigger
            try:
                if (game_main_menu(frame) or game_main_menu_2(frame) or home_menu(frame) or settings_menu(frame)) and not LOCKED and not DEBUG:
                    self.io.disable_input(0)
                    if not (i<100 or bypass):
                        player = json.loads(json.dumps(self.curUser))[0]['username']
                        msg = "SKYRIM\nGame locked due to either being at home screen or capture card bars. \nUser's information are as follows:\n> "+player+"\n> "+self.userID
                        bot.send_message(chat_id, msg, parse_mode="markdown")
                        LOCKED = True
                        self.nsg.end()
                        self.prepare = False
                        content = json.loads('{"game":"skyrim"}')
                        req = requests.post("[REDACTED]", content)
                    else:
                        msg = "SKYRIM\nBypass utilized...Take action to get to a proper menu before something messes up."
                        bot.send_message(chat_id, msg, parse_mode="markdown")
                        bypass = True
                        DEBUG = True
                        LOCKED = True
                        content = json.loads('{"game":"skyrim"}')
                        req = requests.post("[REDACTED]", content)
            except:
                if (game_main_menu(frame) or game_main_menu_2(frame) or home_menu(frame) or settings_menu(frame)) and not LOCKED and not DEBUG:
                    if not (i<100 or bypass):
                        player = json.loads(json.dumps(self.curUser))[0]['username']
                        msg = "SKYRIM\nGame locked due to either being at home screen or capture card bars. \nUser's information are as follows:\n> "+player+"\n> "+self.userID
                        bot.send_message(chat_id, msg, parse_mode="markdown")
                        LOCKED = True
                        self.nsg.end()
                        self.prepare = False
                        content = json.loads('{"game":"skyrim"}')
                        req = requests.post("[REDACTED]", content)
                    else:
                        msg = "SKYRIM\nBypass utilized...Take action to get to a proper menu before something messes up."
                        bot.send_message(chat_id, msg, parse_mode="markdown")
                        bypass = True
                        DEBUG = True
                        LOCKED = True
                        content = json.loads('{"game":"skyrim"}')
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
