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

POINTS_PER_GAME = 5

pigpio.exceptions = False
pi = pigpio.pi()
nsg_reset = 21
ON = 0
OFF = 1

# image rec
SAVE_ALL_FRAMES = False
SAVE_DIR_PATH = "./games/ninswitch/imgs"
global save_individual_fame, allowReset
save_individual_fame = False
allowReset = True

# ----------------------------------------------------

ODYSSEY_NAV_MENU = [ # Valid Pause
    ((796, 683), (205, 177, 7)),
    ((904, 690), (199, 171, 2)),
    ((1026, 686), (190, 164, 0)),
    ((1125, 687), (204, 169, 7)),
    ((90, 694), (199, 172, 3)),
    ((388, 591), (199, 168, 0)),
    ((1111, 52), (253, 253, 253)),
    ((203, 686), (255, 255, 255)),
    ((654, 687), (255, 255, 255)),
]

TALKING = [ # Valid pause but not optimal
    ((1004, 641), (255, 255, 255)),
    ((1033, 640), (255, 254, 255)),
    ((1019, 660), (255, 254, 255)),
    ((1018, 627), (255, 255, 255)),
]

SHOP_LOAD = [
    ((345, 597), (254, 129, 0)),
    ((810, 261), (254, 129, 0)),
    ((134, 153), (255, 144, 0)),
    ((1096, 657), (253, 252, 248)),
    ((951, 636), (254, 255, 249)),
    ((929, 636), (242, 249, 242)),
]

SHOP = [
    ((35, 32), (255, 15, 24)),
    ((325, 31), (255, 15, 24)),
    ((89, 680), (40, 40, 40)),
    ((799, 686), (241, 241, 241)),
    ((40, 624), (255, 15, 24)),
    ((74, 661), (102, 217, 0)),
]

SCREENSHOTS = [
    ((103, 66), (242, 242, 242)),
    ((76, 66), (249, 249, 249)),
    ((682, 686), (251, 251, 251)),
    ((818, 684), (255, 255, 255)),
    ((1036, 684), (249, 249, 249)),
    ((1166, 681), (249, 249, 249)),
    ((106, 693), (255, 255, 255)),
    ((74, 662), (140, 248, 5)),
    ((297, 693), (52, 52, 52)),
    ((462, 687), (52, 52, 52)),
    ((385, 46), (52, 52, 52)),
    ((614, 46), (52, 52, 52)),
]

SETTINGS = [
    ((104, 51), (255, 255, 255)),
    ((90, 36), (245, 245, 245)),
    ((75, 50), (254, 254, 254)),
    ((89, 65), (255, 255, 255)),
    ((75, 662), (141, 242, 0)),
    ((88, 680), (255, 255, 255)),
    ((1036, 683), (249, 249, 249)),
    ((1152, 682), (255, 255, 255)),
    ((410, 686), (52, 52, 52)),
    ((549, 692), (52, 52, 52)),
    ((548, 48), (52, 52, 52)),
    ((815, 71), (52, 52, 52)),
]

HOME_MENU = [
    ((604, 66), (255, 142, 50)),
    ((711, 65), (255, 142, 50)),
    ((318, 95), (52, 52, 52)),
    ((912, 82), (52, 52, 52)),
    ((981, 689), (255, 255, 255)),
    ((105, 690), (253, 253, 253)),
    ((74, 662), (140, 248, 5)),
    ((336, 688), (52, 52, 52)),
    ((688, 685), (52, 52, 52)),
]

PLUS_MENU_INGAME = [
    ((78, 687), (201, 163, 0)),
    ((1000, 684), (203, 171, 2)),
    ((1125, 687), (209, 176, 11)),
    ((707, 690), (255, 255, 255)),
    ((424, 690), (255, 255, 255)),
    ((186, 87), (254, 10, 0)),
    ((72, 75), (253, 15, 2)),
    ((91, 85), (21, 255, 0)),
    ((115, 80), (255, 236, 0)),
    ((140, 70), (3, 143, 255)),
    ((156, 68), (107, 217, 40)),
    ((105, 126), (14, 254, 253)),
    ((119, 113), (75, 255, 254)),
    ((140, 119), (44, 252, 252)),
    ((160, 120), (15, 253, 255)),
    ((134, 45), (250, 252, 251)),
]

MINUS_MENU_INGAME = [
    ((30, 695), (255, 255, 255)),
    ((77, 688), (202, 171, 2)),
    ((281, 696), (255, 255, 255)),
    ((455, 700), (255, 255, 255)),
    ((601, 699), (255, 255, 255)),
    ((720, 685), (197, 168, 2)),
    ((733, 684), (196, 170, 0)),
    ((911, 685), (202, 173, 7)),
    ((925, 684), (196, 170, 0)),
    ((1027, 690), (194, 170, 2)),
    ((1042, 688), (200, 168, 5)),
    ((1131, 687), (200, 168, 0)),
    ((1148, 688), (208, 170, 7)),
    ((599, 663), (193, 171, 0)),
]

GAME_MAIN_MENU = [
    ((78, 687), (201, 163, 0)),
    ((360, 691), (255, 255, 255)),
    ((549, 690), (255, 255, 255)),
    ((1000, 684), (203, 171, 2)),
    ((1123, 686), (203, 175, 13)),
    ((42, 58), (247, 248, 242)),
    ((499, 87), (242, 243, 237)),
    ((1156, 74), (246, 247, 241)),
    ((1237, 591), (246, 247, 241)),
    ((100, 596), (246, 247, 241)),
]

CONTROLLER_DC_INPUT_NEEDED =  [
    ((427, 87), (255, 253, 254)),
    ((571, 107), (254, 254, 254)),
    ((658, 85), (232, 237, 233)),
    ((698, 106), (237, 239, 234)),
    ((789, 80), (242, 255, 243)),
    ((830, 96), (254, 251, 255)),
    ((529, 237), (47, 83, 255)),
    ((586, 241), (47, 83, 255)),
    ((617, 258), (41, 88, 254)),
    ((499, 259), (48, 84, 255)),
    ((540, 593), (185, 229, 255)),
    ((568, 593), (185, 230, 253)),
    ((597, 690), (251, 255, 252)),
    ((1013, 689), (255, 255, 255)),
]

CONTROLLER_DC_RECONNECTED = [
    ((499, 260), (50, 80, 255)),
    ((527, 245), (47, 85, 254)),
    ((586, 247), (47, 83, 255)),
    ((618, 258), (45, 87, 255)),
    ((588, 452), (76, 76, 76)),
    ((637, 407), (52, 52, 52)),
    ((691, 454), (76, 76, 76)),
    ((655, 430), (239, 239, 239)),
    ((604, 410), (237, 237, 237)),
    ((427, 88), (252, 252, 252)),
    ((572, 107), (253, 254, 255)),
    ((481, 382), (255, 255, 255)),
    ((754, 438), (255, 255, 255)),
    ((658, 85), (232, 237, 233)),
    ((698, 106), (237, 239, 234)),
    ((789, 79), (249, 255, 246)),
    ((829, 95), (249, 253, 255)),
    ((651, 688), (255, 252, 251)),
    ((1012, 678), (255, 255, 255)),
]

# ----------------------------------------------------


GOT_MOON_BIG = [
    ((207, 129), (253, 255, 254)),
    ((234, 165), (252, 254, 251)),
    ((250, 127), (255, 255, 253)),
    ((291, 118), (249, 255, 255)),
    ((311, 158), (251, 255, 254)),
    ((350, 114), (255, 255, 255)),
    ((379, 159), (252, 255, 255)),
    ((390, 124), (255, 255, 255)),
    ((480, 94), (252, 254, 253)),
    ((438, 121), (247, 247, 247)),
    ((497, 120), (253, 252, 250)),
    ((475, 138), (254, 255, 255)),
    ((549, 91), (255, 255, 255)),
    ((520, 110), (255, 255, 255)),
    ((567, 113), (251, 252, 254)),
    ((543, 134), (254, 255, 255)),
    ((610, 84), (255, 255, 253)),
    ((610, 122), (255, 253, 254)),
    ((679, 135), (255, 255, 255)),
    ((700, 91), (255, 255, 251)),
    ((719, 129), (254, 254, 255)),
    ((775, 136), (255, 255, 255)),
    ((780, 98), (255, 255, 253)),
    ((797, 121), (255, 255, 255)),
    ((820, 100), (255, 255, 255)),
    ((823, 141), (255, 255, 255)),
    ((870, 145), (255, 255, 255)),
    ((875, 98), (252, 255, 255)),
    ((956, 105), (255, 254, 255)),
    ((945, 152), (255, 254, 255)),
    ((992, 160), (247, 253, 253)),
    ((1005, 118), (255, 255, 255)),
    ((1026, 159), (255, 255, 255)),
    ((1040, 118), (255, 255, 253)),
    ((1057, 173), (254, 254, 254)),
    ((1067, 131), (254, 254, 255)),
    ((661, 243), (40, 139, 241)),
    ((718, 244), (47, 134, 237)),
    ((469, 250), (249, 246, 57)),
    ((559, 60), (247, 241, 31)),
    ((31, 58), (254, 34, 36)),
]

GOT_MOON_RETRO = [
    ((258, 432), (255, 255, 255)),
    ((275, 468), (254, 255, 255)),
    ((293, 432), (254, 254, 252)),
    ((317, 451), (252, 255, 255)),
    ((363, 451), (255, 255, 253)),
    ((379, 430), (254, 255, 253)),
    ((415, 473), (253, 253, 251)),
    ((501, 434), (255, 255, 255)),
    ((468, 459), (255, 255, 255)),
    ((503, 470), (255, 255, 255)),
    ((558, 431), (255, 255, 255)),
    ((554, 476), (255, 255, 255)),
    ((615, 429), (255, 255, 255)),
    ((614, 470), (255, 255, 255)),
    ((675, 472), (255, 255, 255)),
    ((716, 472), (255, 255, 255)),
    ((694, 424), (255, 255, 253)),
    ((766, 474), (255, 255, 255)),
    ((784, 459), (255, 255, 255)),
    ((806, 428), (255, 255, 255)),
    ((853, 430), (255, 255, 255)),
    ((851, 471), (250, 250, 250)),
    ((890, 450), (255, 255, 255)),
    ((944, 452), (255, 255, 255)),
    ((958, 473), (252, 252, 252)),
    ((962, 432), (255, 255, 255)),
    ((994, 468), (255, 255, 255)),
    ((997, 433), (255, 255, 255)),
    ((1021, 433), (255, 255, 255)),
    ((1022, 473), (255, 255, 255)),
    ((631, 298), (254, 255, 7)),
    ((632, 246), (254, 255, 4)),
]

GOT_MOON_NORMAL = [
    ((257, 430), (252, 255, 255)),
    ((277, 469), (254, 255, 253)),
    ((316, 454), (254, 255, 255)),
    ((363, 449), (251, 255, 252)),
    ((380, 428), (255, 253, 254)),
    ((415, 469), (254, 255, 250)),
    ((503, 433), (255, 251, 255)),
    ((467, 467), (255, 255, 255)),
    ((540, 436), (255, 255, 255)),
    ((571, 465), (255, 255, 255)),
    ((597, 426), (254, 255, 255)),
    ((613, 471), (254, 254, 252)),
    ((673, 477), (254, 255, 255)),
    ((694, 435), (255, 255, 255)),
    ((758, 472), (255, 254, 255)),
    ((805, 431), (253, 255, 252)),
    ((853, 428), (255, 255, 255)),
    ((852, 475), (255, 255, 255)),
    ((894, 450), (254, 255, 255)),
    ((941, 450), (255, 255, 255)),
    ((959, 474), (254, 255, 255)),
    ((997, 430), (254, 255, 250)),
    ((1017, 430), (254, 254, 255)),
    ((1020, 475), (253, 255, 252)),
    ((625, 261), (144, 255, 99)),
    ((661, 197), (94, 255, 141)),
    ((655, 248), (79, 147, 222)),
]

GOT_MULTI_MOON = [
    ((78, 141), (251, 255, 254)),
    ((107, 178), (255, 254, 255)),
    ((148, 153), (251, 255, 254)),
    ((199, 144), (252, 253, 255)),
    ((216, 115), (255, 255, 255)),
    ((254, 108), (253, 254, 255)),
    ((244, 163), (255, 254, 255)),
    ((358, 119), (250, 255, 255)),
    ((307, 109), (252, 255, 253)),
    ((385, 97), (255, 252, 255)),
    ((428, 132), (255, 254, 252)),
    ((449, 82), (254, 255, 255)),
    ((479, 82), (255, 255, 255)),
    ((471, 132), (254, 255, 253)),
    ((537, 127), (251, 255, 254)),
    ((556, 78), (250, 250, 250)),
    ((629, 126), (251, 255, 255)),
    ((678, 72), (253, 255, 254)),
    ((699, 76), (255, 253, 250)),
    ((735, 119), (255, 251, 251)),
    ((764, 78), (255, 255, 253)),
    ((784, 127), (248, 254, 254)),
    ((800, 77), (255, 254, 255)),
    ((839, 80), (253, 254, 255)),
    ((859, 111), (253, 251, 254)),
    ((653, 231), (250, 255, 249)),
    ((723, 489), (100, 154, 200)),
    ((781, 512), (135, 173, 210)),
    ((537, 498), (255, 254, 104)),
    ((728, 348), (255, 255, 113)),
    ((625, 317), (115, 100, 95)),
    ((472, 428), (117, 99, 97)),
    ((25, 67), (254, 34, 36)),
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
        global DEBUG
        if DEBUG:
            DEBUG = False
        else:
            DEBUG = True

        logging.info(f"\t{seat} | debug_switch down")

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

class SMO_IR(Game):
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
                "plus": NSSwitch(self.nsg, NSButton.PLUS),
                "debug_switch": debug_switch(),
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
        # self.userIDs = []
        # self.userScores = []
        # self.knownIndex = 0
        # self.points = 0
        # with open("player_scores.dat", "r") as file:
        #     for line in file:
        #         currentPlace=line[:-1]
        #         breakPt = currentPlace.index("|")
        #         uid = currentPlace[0:int(breakPt)]
        #         score = int(currentPlace[int(breakPt)+1:])
        #         if not uid in self.userIDs:
        #             self.userIDs.append(uid)
        #             self.userScores.append(score)

# ----------------------------------------------------

    async def on_start(self):
        self.curUser = self.players
        player = json.loads(json.dumps(self.players))[0]['username']

        req = requests.get("https://g9b1fyald3.execute-api.eu-west-1.amazonaws.com/master/users?search="+str(player)).text
        uid = json.loads(req)['result'][0]['userId']
        self.userID = uid
        # if str(uid) in self.userIDs:
        #     self.knownIndex = self.userIDs.index(str(uid))
        #     self.points = self.userScores[self.knownIndex]
        # else: 
        #     self.userIDs.append(str(uid))
        #     self.points = 0
        #     self.userScores.append(self.points)
        #     self.knownIndex = len(self.userScores)-1

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

        # self.userScores[0] = 0
        # self.io.send_score(score=self.points, seat=1, final_score=True)
        # self.userScores[self.knownIndex] = self.points

        # with open("player_scores.dat", "w") as file:
        #     for i in range(len(self.userIDs)):
        #         item = self.userIDs[i]+"|"+str(self.userScores[i])
        #         file.write('%s\n' % item)

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
        
        global LOCKED, allowReset
        LOCKED = False

        # get detector
        odyssey_nav_menu = get_pixel_detector(ODYSSEY_NAV_MENU, 50)
        talking = get_pixel_detector(TALKING, 50)
        minus_menu_ingame = get_pixel_detector(MINUS_MENU_INGAME, 50)

        controller_dc_input_needed = get_pixel_detector(CONTROLLER_DC_INPUT_NEEDED, 50)
        controller_dc_reconnected = get_pixel_detector(CONTROLLER_DC_RECONNECTED, 50)

        shop_load = get_pixel_detector(SHOP_LOAD, 50)
        shop = get_pixel_detector(SHOP, 50)
        screenshots = get_pixel_detector(SCREENSHOTS, 50)
        settings = get_pixel_detector(SETTINGS, 50)
        home_menu = get_pixel_detector(HOME_MENU, 50)
        plus_menu_ingame = get_pixel_detector(PLUS_MENU_INGAME, 50)
        game_main_menu = get_pixel_detector(GAME_MAIN_MENU, 50)

        got_moon_big = get_pixel_detector(GOT_MOON_BIG, 50)
        got_moon_retro = get_pixel_detector(GOT_MOON_RETRO, 50)
        got_moon_normal = get_pixel_detector(GOT_MOON_NORMAL, 50)
        got_multi_moon = get_pixel_detector(GOT_MULTI_MOON, 50)


        # loop through frames
        i = 0
        z = 0
        async for frame in self.cap.frames():
            # detect
            if i%30==0 and (controller_dc_reconnected(frame) or controller_dc_input_needed(frame) or controller_dc_reconnected(frame) or controller_dc_input_needed(frame)):
                pi.write(nsg_reset, ON)
                await asyncio.sleep(0.5)
                pi.write(nsg_reset, OFF)
                await asyncio.sleep(1)
            try:
                if (controller_dc_reconnected(frame) or controller_dc_input_needed(frame)) and not DEBUG:
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
                if (controller_dc_reconnected(frame) or controller_dc_input_needed(frame)) and not DEBUG:
                    self.nsg.press(NSButton.A)
                    await asyncio.sleep(0.1)
                    self.nsg.release(NSButton.A)
                    await asyncio.sleep(2)
                    self.nsg.press(NSButton.A)
                    await asyncio.sleep(0.1)
                    self.nsg.release(NSButton.A)
                    await asyncio.sleep(2)

            if (self.prepare and not ((odyssey_nav_menu(frame) or talking(frame) or minus_menu_ingame(frame))) and not LOCKED) and not DEBUG:
                if z % 3 == 2:
                    self.nsg.press(NSButton.A)
                    await asyncio.sleep(0.1)
                    self.nsg.release(NSButton.A)
                    await asyncio.sleep(1)
                    self.nsg.press(NSButton.B)
                    await asyncio.sleep(0.1)
                    self.nsg.release(NSButton.B)
                    await asyncio.sleep(1)
                else:
                    self.nsg.press(NSButton.MINUS)
                    await asyncio.sleep(0.1)
                    self.nsg.release(NSButton.MINUS)
                    await asyncio.sleep(1)
                z += 1
            elif not LOCKED:
                z = 0
                self.prepare = False

            try:
                if (shop_load(frame) or shop(frame) or screenshots(frame) or settings(frame) or home_menu(frame) or plus_menu_ingame(frame) or game_main_menu(frame)) and not LOCKED and not DEBUG:
                    self.io.disable_input(0)
                    player = json.loads(json.dumps(self.curUser))[0]['username']
                    msg = "SUPER MARIO ODYSSEY\nGame locked due to either being at home screen or capture card bars. \nUser's information are as follows:\n> "+player+"\n> "+self.userID
                    bot.send_message(chat_id, msg, parse_mode="markdown")
                    LOCKED = True
            except:
                if (shop_load(frame) or shop(frame) or screenshots(frame) or settings(frame) or home_menu(frame) or plus_menu_ingame(frame) or game_main_menu(frame)) and not LOCKED and not DEBUG:
                    player = json.loads(json.dumps(self.curUser))[0]['username']
                    msg = "SUPER MARIO ODYSSEY\nGame locked due to either being at home screen or capture card bars. \nUser's information are as follows:\n> "+player+"\n> "+self.userID
                    bot.send_message(chat_id, msg, parse_mode="markdown")
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
    SMO_IR().run()
