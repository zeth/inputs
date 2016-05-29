"""Inputs - user input for humans.

About
-----

Inputs aims to provide easy to use, cross-platform, user input device
support for Python. I.e. keyboards, mice, gamepads, etc.

It is still early days. Currently supported platforms are the
Raspberry Pi, Linux and Windows. Hopefully Mac OS X, BSD and Android
should be supported soon. Optional Asyncio-based event loop support
will be included eventually.

Obviously high level graphical libraries such as PyGame and PyQT will
provide user input support in a very friendly way. However, this
module does not require your program to use any particular graphical
toolkit, or even have a monitor at all.

In the Embedded Linux or Raspberry Pi Internet of Things type
situation, you may not even have an X-server installed or running.

This module may also be useful where a computer needs to run a
particular application full screen but you would want to listen out in
the background for a particular set of user inputs, e.g. to bring up
an admin panel in a digital signage setup.

Note to Children
----------------

It is pretty easy to use any user input device library, including this
one, to build a keylogger. Using this module to spy on your mum or
teacher or sibling is not cool and may get you into trouble. So please
do not do that. Make a game instead, games are cool.

Quick Start
-----------

To access all the available input devices on the current system:

>>> from inputs import devices
>>> for device in devices:
...     print(device)

You can also access devices by type:

>>> devices.gamepads
>>> devices.keyboards
>>> devices.mice
>>> devices.other_devices

Each device object has the obvious methods and properties that you
expect, stop reading now and just get playing!

If that is not high level enough, there are three basic functions that
simply give you the latest event (key press, mouse movement/press or
gamepad activity) from the first connected device in the category, for
example:

>>> from inputs import get_gamepad
>>> while 1:
...     event = get_gamepad()
...     print(event.ev_type, event.code, event.state)

>>> from inputs import get_key
>>> while 1:
...     event = get_gamepad()
...     print(event.ev_type, event.code, event.state)

>>> from inputs import get_mouse
>>> while 1:
...     event = get_gamepad()
...     print(event.ev_type, event.code, event.state)

Advanced documentation
----------------------

A keyboard is represented by the Keyboard class, a mouse by the Mouse
class and a gamepad by the Gamepad class. These themselves are
subclasses of InputDevice.

The devices object is an instance of DeviceManager, as you can prove:

>>> from inputs import DeviceManager
>>> devices = DeviceManager()

The DeviceManager is reponsible for finding input devices on the
user's system and setting up InputDevice objects.

The InputDevice objects emit instances of InputEvent. So from top
down, the classes are arranged thus:

DeviceManager > InputDevice > InputEvent

So when you have a particular InputEvent instance, you can access its
device and manager:

>>> event.device.manager

The event object has a property called device and the device has a
property called manager.

As you can see, it is really very simple. The device manager has an
attribute called codes which is giant dictionary of key, button and
other codes.

Using pypi is superior but is yet another thing to learn for new
users. Therefore, inputs is kept as one file to make it easy for
people to include in their project.

Gamepads
--------

An approach often taken by PC games, especially open source games, is
to assume that all gamepads are Microsoft Xbox 360 controllers and
then users use software such as x360ce (on Windows) or xboxdrv (on
Linux) to make other models of gamepad report Xbox 360 style button
and joystick codes to the operating system.

So for inputs the primary target device is the Microsoft Xbox 360
Wired Controller and this has the best support. Another gamepad might
just work but if not you can use xboxdrv or x360ce to configure it
yourself.

More testing and support for common gamepads will come in due course.

Raspberry Pi Sense HAT
----------------------

The microcontroller on the Raspberry Pi Sense HAT presents the
joystick to the operating system as a keyboard, so find it there under
keyboards. If you worry about this, you are over-thinking things.

Credits
-------

Inputs is by Zeth, all mistakes are mine.

Thanks to Dave Jones for stick.py which is not only the basis for
Sense HAT stick support in this module but more importantly also
taught me an easier way to parse the Evdev event format in Python.

https://github.com/RPi-Distro/python-sense-hat/blob/master/sense_hat/stick.py
https://github.com/waveform80/pisense/blob/master/pisense/stick.py

Thanks to Andy (r4dian) and Jason R. Coombs whose existing (MIT
licenced) Python examples for Xbox 360 controller support on Windows
helped me understand xinput greatly. Xbox 360 controller support on
Windows here is based on their work.
https://github.com/r4dian/Xbox-360-Controller-for-Python
http://pydoc.net/Python/jaraco.input/1.0.1/jaraco.input.win32.xinput/

"""

from __future__ import print_function

import os
import io
import glob
import struct
import platform
import math
import time
from warnings import warn
from itertools import count
from operator import itemgetter
import ctypes


# long, long, unsigned short, unsigned short, unsigned int
EVENT_FORMAT = str('llHHI')
EVENT_SIZE = struct.calcsize(EVENT_FORMAT)

SPECIAL_DEVICES = (
    ("Raspberry Pi Sense HAT Joystick",
     "/dev/input/by-id/gpio-Raspberry_Pi_Sense_HAT_Joystick-event-kbd"),)

XINPUT_MAPPING = (
    (1, 0x11),
    (2, 0x11),
    (3, 0x10),
    (4, 0x10),
    (5, 0x13a),
    (6, 0x13b),
    #  (7, None),
    #  (8, None),
    (9, 0x136),
    (10, 0x137),
    #  (11, None),
    #  (12, None),
    (13, 0x130),
    (14, 0x131),
    (15, 0x134),
    (16, 0x133)
)

XINPUT_DLL_NAMES = (
    "XInput1_4.dll",
    "XInput9_1_0.dll",
    "XInput1_3.dll",
    "XInput1_2.dll",
    "XInput1_1.dll"
)

XINPUT_ERROR_DEVICE_NOT_CONNECTED = 1167
XINPUT_ERROR_SUCCESS = 0

DEVICE_PROPERTIES = (
    (0x00, "INPUT_PROP_POINTER"),  # needs a pointer
    (0x01, "INPUT_PROP_DIRECT"),  # direct input devices
    (0x02, "INPUT_PROP_BUTTONPAD"),  # has button(s) under pad
    (0x03, "INPUT_PROP_SEMI_MT"),  # touch rectangle only
    (0x04, "INPUT_PROP_TOPBUTTONPAD"),  # softbuttons at top of pad
    (0x05, "INPUT_PROP_POINTING_STICK"),  # is a pointing stick
    (0x06, "INPUT_PROP_ACCELEROMETER"),  # has accelerometer
    (0x1f, "INPUT_PROP_MAX"),
    (0x1f + 1, "INPUT_PROP_CNT"))

EVENT_TYPES = (
    (0x00, "Sync"),
    (0x01, "Key"),
    (0x02, "Relative"),
    (0x03, "Absolute"),
    (0x04, "Misc"),
    (0x05, "Switch"),
    (0x11, "LED"),
    (0x12, "Sound"),
    (0x14, "Repeat"),
    (0x15, "ForceFeedback"),
    (0x16, "Power"),
    (0x17, "ForceFeedbackStatus"),
    (0x1f, "Max"),
    (0x1f+1, "Current"))

SYNCHRONIZATION_EVENTS = (
    (0, "SYN_REPORT"),
    (1, "SYN_CONFIG"),
    (2, "SYN_MT_REPORT"),
    (3, "SYN_DROPPED"),
    (0xf, "SYN_MAX"),
    (0xf+1, "SYN_CNT"))

KEYS_AND_BUTTONS = (
    (0, "KEY_RESERVED"),
    (1, "KEY_ESC"),
    (2, "KEY_1"),
    (3, "KEY_2"),
    (4, "KEY_3"),
    (5, "KEY_4"),
    (6, "KEY_5"),
    (7, "KEY_6"),
    (8, "KEY_7"),
    (9, "KEY_8"),
    (10, "KEY_9"),
    (11, "KEY_0"),
    (12, "KEY_MINUS"),
    (13, "KEY_EQUAL"),
    (14, "KEY_BACKSPACE"),
    (15, "KEY_TAB"),
    (16, "KEY_Q"),
    (17, "KEY_W"),
    (18, "KEY_E"),
    (19, "KEY_R"),
    (20, "KEY_T"),
    (21, "KEY_Y"),
    (22, "KEY_U"),
    (23, "KEY_I"),
    (24, "KEY_O"),
    (25, "KEY_P"),
    (26, "KEY_LEFTBRACE"),
    (27, "KEY_RIGHTBRACE"),
    (28, "KEY_ENTER"),
    (29, "KEY_LEFTCTRL"),
    (30, "KEY_A"),
    (31, "KEY_S"),
    (32, "KEY_D"),
    (33, "KEY_F"),
    (34, "KEY_G"),
    (35, "KEY_H"),
    (36, "KEY_J"),
    (37, "KEY_K"),
    (38, "KEY_L"),
    (39, "KEY_SEMICOLON"),
    (40, "KEY_APOSTROPHE"),
    (41, "KEY_GRAVE"),
    (42, "KEY_LEFTSHIFT"),
    (43, "KEY_BACKSLASH"),
    (44, "KEY_Z"),
    (45, "KEY_X"),
    (46, "KEY_C"),
    (47, "KEY_V"),
    (48, "KEY_B"),
    (49, "KEY_N"),
    (50, "KEY_M"),
    (51, "KEY_COMMA"),
    (52, "KEY_DOT"),
    (53, "KEY_SLASH"),
    (54, "KEY_RIGHTSHIFT"),
    (55, "KEY_KPASTERISK"),
    (56, "KEY_LEFTALT"),
    (57, "KEY_SPACE"),
    (58, "KEY_CAPSLOCK"),
    (59, "KEY_F1"),
    (60, "KEY_F2"),
    (61, "KEY_F3"),
    (62, "KEY_F4"),
    (63, "KEY_F5"),
    (64, "KEY_F6"),
    (65, "KEY_F7"),
    (66, "KEY_F8"),
    (67, "KEY_F9"),
    (68, "KEY_F10"),
    (69, "KEY_NUMLOCK"),
    (70, "KEY_SCROLLLOCK"),
    (71, "KEY_KP7"),
    (72, "KEY_KP8"),
    (73, "KEY_KP9"),
    (74, "KEY_KPMINUS"),
    (75, "KEY_KP4"),
    (76, "KEY_KP5"),
    (77, "KEY_KP6"),
    (78, "KEY_KPPLUS"),
    (79, "KEY_KP1"),
    (80, "KEY_KP2"),
    (81, "KEY_KP3"),
    (82, "KEY_KP0"),
    (83, "KEY_KPDOT"),
    (85, "KEY_ZENKAKUHANKAKU"),
    (86, "KEY_102ND"),
    (87, "KEY_F11"),
    (88, "KEY_F12"),
    (89, "KEY_RO"),
    (90, "KEY_KATAKANA"),
    (91, "KEY_HIRAGANA"),
    (92, "KEY_HENKAN"),
    (93, "KEY_KATAKANAHIRAGANA"),
    (94, "KEY_MUHENKAN"),
    (95, "KEY_KPJPCOMMA"),
    (96, "KEY_KPENTER"),
    (97, "KEY_RIGHTCTRL"),
    (98, "KEY_KPSLASH"),
    (99, "KEY_SYSRQ"),
    (100, "KEY_RIGHTALT"),
    (101, "KEY_LINEFEED"),
    (102, "KEY_HOME"),
    (103, "KEY_UP"),
    (104, "KEY_PAGEUP"),
    (105, "KEY_LEFT"),
    (106, "KEY_RIGHT"),
    (107, "KEY_END"),
    (108, "KEY_DOWN"),
    (109, "KEY_PAGEDOWN"),
    (110, "KEY_INSERT"),
    (111, "KEY_DELETE"),
    (112, "KEY_MACRO"),
    (113, "KEY_MUTE"),
    (114, "KEY_VOLUMEDOWN"),
    (115, "KEY_VOLUMEUP"),
    (116, "KEY_POWER"),  # SC System Power Down
    (117, "KEY_KPEQUAL"),
    (118, "KEY_KPPLUSMINUS"),
    (119, "KEY_PAUSE"),
    (120, "KEY_SCALE"),  # AL Compiz Scale (Expose)
    (121, "KEY_KPCOMMA"),
    (122, "KEY_HANGEUL"),
    (123, "KEY_HANJA"),
    (124, "KEY_YEN"),
    (125, "KEY_LEFTMETA"),
    (126, "KEY_RIGHTMETA"),
    (127, "KEY_COMPOSE"),
    (128, "KEY_STOP"),  # AC Stop
    (129, "KEY_AGAIN"),
    (130, "KEY_PROPS"),  # AC Properties
    (131, "KEY_UNDO"),  # AC Undo
    (132, "KEY_FRONT"),
    (133, "KEY_COPY"),  # AC Copy
    (134, "KEY_OPEN"),  # AC Open
    (135, "KEY_PASTE"),  # AC Paste
    (136, "KEY_FIND"),  # AC Search
    (137, "KEY_CUT"),  # AC Cut
    (138, "KEY_HELP"),  # AL Integrated Help Center
    (139, "KEY_MENU"),  # Menu (show menu)
    (140, "KEY_CALC"),  # AL Calculator
    (141, "KEY_SETUP"),
    (142, "KEY_SLEEP"),  # SC System Sleep
    (143, "KEY_WAKEUP"),  # System Wake Up
    (144, "KEY_FILE"),  # AL Local Machine Browser
    (145, "KEY_SENDFILE"),
    (146, "KEY_DELETEFILE"),
    (147, "KEY_XFER"),
    (148, "KEY_PROG1"),
    (149, "KEY_PROG2"),
    (150, "KEY_WWW"),  # AL Internet Browser
    (151, "KEY_MSDOS"),
    (152, "KEY_COFFEE"),  # AL Terminal Lock/Screensaver
    (153, "KEY_ROTATE_DISPLAY"),  # Display orientation for e.g. tablets
    (154, "KEY_CYCLEWINDOWS"),
    (155, "KEY_MAIL"),
    (156, "KEY_BOOKMARKS"),  # AC Bookmarks
    (157, "KEY_COMPUTER"),
    (158, "KEY_BACK"),  # AC Back
    (159, "KEY_FORWARD"),  # AC Forward
    (160, "KEY_CLOSECD"),
    (161, "KEY_EJECTCD"),
    (162, "KEY_EJECTCLOSECD"),
    (163, "KEY_NEXTSONG"),
    (164, "KEY_PLAYPAUSE"),
    (165, "KEY_PREVIOUSSONG"),
    (166, "KEY_STOPCD"),
    (167, "KEY_RECORD"),
    (168, "KEY_REWIND"),
    (169, "KEY_PHONE"),  # Media Select Telephone
    (170, "KEY_ISO"),
    (171, "KEY_CONFIG"),  # AL Consumer Control Configuration
    (172, "KEY_HOMEPAGE"),  # AC Home
    (173, "KEY_REFRESH"),  # AC Refresh
    (174, "KEY_EXIT"),  # AC Exit
    (175, "KEY_MOVE"),
    (176, "KEY_EDIT"),
    (177, "KEY_SCROLLUP"),
    (178, "KEY_SCROLLDOWN"),
    (179, "KEY_KPLEFTPAREN"),
    (180, "KEY_KPRIGHTPAREN"),
    (181, "KEY_NEW"),  # AC New
    (182, "KEY_REDO"),  # AC Redo/Repeat
    (183, "KEY_F13"),
    (184, "KEY_F14"),
    (185, "KEY_F15"),
    (186, "KEY_F16"),
    (187, "KEY_F17"),
    (188, "KEY_F18"),
    (189, "KEY_F19"),
    (190, "KEY_F20"),
    (191, "KEY_F21"),
    (192, "KEY_F22"),
    (193, "KEY_F23"),
    (194, "KEY_F24"),
    (200, "KEY_PLAYCD"),
    (201, "KEY_PAUSECD"),
    (202, "KEY_PROG3"),
    (203, "KEY_PROG4"),
    (204, "KEY_DASHBOARD"),  # AL Dashboard
    (205, "KEY_SUSPEND"),
    (206, "KEY_CLOSE"),  # AC Close
    (207, "KEY_PLAY"),
    (208, "KEY_FASTFORWARD"),
    (209, "KEY_BASSBOOST"),
    (210, "KEY_PRINT"),  # AC Print
    (211, "KEY_HP"),
    (212, "KEY_CAMERA"),
    (213, "KEY_SOUND"),
    (214, "KEY_QUESTION"),
    (215, "KEY_EMAIL"),
    (216, "KEY_CHAT"),
    (217, "KEY_SEARCH"),
    (218, "KEY_CONNECT"),
    (219, "KEY_FINANCE"),  # AL Checkbook/Finance
    (220, "KEY_SPORT"),
    (221, "KEY_SHOP"),
    (222, "KEY_ALTERASE"),
    (223, "KEY_CANCEL"),  # AC Cancel
    (224, "KEY_BRIGHTNESSDOWN"),
    (225, "KEY_BRIGHTNESSUP"),
    (226, "KEY_MEDIA"),
    (227, "KEY_SWITCHVIDEOMODE"),  # Cycle between available video
    (228, "KEY_KBDILLUMTOGGLE"),
    (229, "KEY_KBDILLUMDOWN"),
    (230, "KEY_KBDILLUMUP"),
    (231, "KEY_SEND"),  # AC Send
    (232, "KEY_REPLY"),  # AC Reply
    (233, "KEY_FORWARDMAIL"),  # AC Forward Msg
    (234, "KEY_SAVE"),  # AC Save
    (235, "KEY_DOCUMENTS"),
    (236, "KEY_BATTERY"),
    (237, "KEY_BLUETOOTH"),
    (238, "KEY_WLAN"),
    (239, "KEY_UWB"),
    (240, "KEY_UNKNOWN"),
    (241, "KEY_VIDEO_NEXT"),  # drive next video source
    (242, "KEY_VIDEO_PREV"),  # drive previous video source
    (243, "KEY_BRIGHTNESS_CYCLE"),  # brightness up, after max is min
    (244, "KEY_BRIGHTNESS_AUTO"),  # Set Auto Brightness: manual
    (245, "KEY_DISPLAY_OFF"),  # display device to off state
    (246, "KEY_WWAN"),  # Wireless WAN (LTE, UMTS, GSM, etc.)
    (247, "KEY_RFKILL"),  # Key that controls all radios
    (248, "KEY_MICMUTE"),  # Mute / unmute the microphone
    (0x100, "BTN_MISC"),
    (0x100, "BTN_0"),
    (0x101, "BTN_1"),
    (0x102, "BTN_2"),
    (0x103, "BTN_3"),
    (0x104, "BTN_4"),
    (0x105, "BTN_5"),
    (0x106, "BTN_6"),
    (0x107, "BTN_7"),
    (0x108, "BTN_8"),
    (0x109, "BTN_9"),
    (0x110, "BTN_MOUSE"),
    (0x110, "BTN_LEFT"),
    (0x111, "BTN_RIGHT"),
    (0x112, "BTN_MIDDLE"),
    (0x113, "BTN_SIDE"),
    (0x114, "BTN_EXTRA"),
    (0x115, "BTN_FORWARD"),
    (0x116, "BTN_BACK"),
    (0x117, "BTN_TASK"),
    (0x120, "BTN_JOYSTICK"),
    (0x120, "BTN_TRIGGER"),
    (0x121, "BTN_THUMB"),
    (0x122, "BTN_THUMB2"),
    (0x123, "BTN_TOP"),
    (0x124, "BTN_TOP2"),
    (0x125, "BTN_PINKIE"),
    (0x126, "BTN_BASE"),
    (0x127, "BTN_BASE2"),
    (0x128, "BTN_BASE3"),
    (0x129, "BTN_BASE4"),
    (0x12a, "BTN_BASE5"),
    (0x12b, "BTN_BASE6"),
    (0x12f, "BTN_DEAD"),
    (0x130, "BTN_GAMEPAD"),
    (0x130, "BTN_SOUTH"),
    (0x131, "BTN_EAST"),
    (0x132, "BTN_C"),
    (0x133, "BTN_NORTH"),
    (0x134, "BTN_WEST"),
    (0x135, "BTN_Z"),
    (0x136, "BTN_TL"),
    (0x137, "BTN_TR"),
    (0x138, "BTN_TL2"),
    (0x139, "BTN_TR2"),
    (0x13a, "BTN_SELECT"),
    (0x13b, "BTN_START"),
    (0x13c, "BTN_MODE"),
    (0x13d, "BTN_THUMBL"),
    (0x13e, "BTN_THUMBR"),
    (0x140, "BTN_DIGI"),
    (0x140, "BTN_TOOL_PEN"),
    (0x141, "BTN_TOOL_RUBBER"),
    (0x142, "BTN_TOOL_BRUSH"),
    (0x143, "BTN_TOOL_PENCIL"),
    (0x144, "BTN_TOOL_AIRBRUSH"),
    (0x145, "BTN_TOOL_FINGER"),
    (0x146, "BTN_TOOL_MOUSE"),
    (0x147, "BTN_TOOL_LENS"),
    (0x148, "BTN_TOOL_QUINTTAP"),  # Five fingers on trackpad
    (0x14a, "BTN_TOUCH"),
    (0x14b, "BTN_STYLUS"),
    (0x14c, "BTN_STYLUS2"),
    (0x14d, "BTN_TOOL_DOUBLETAP"),
    (0x14e, "BTN_TOOL_TRIPLETAP"),
    (0x14f, "BTN_TOOL_QUADTAP"),  # Four fingers on trackpad
    (0x150, "BTN_WHEEL"),
    (0x150, "BTN_GEAR_DOWN"),
    (0x151, "BTN_GEAR_UP"),
    (0x160, "KEY_OK"),
    (0x161, "KEY_SELECT"),
    (0x162, "KEY_GOTO"),
    (0x163, "KEY_CLEAR"),
    (0x164, "KEY_POWER2"),
    (0x165, "KEY_OPTION"),
    (0x166, "KEY_INFO"),  # AL OEM Features/Tips/Tutorial
    (0x167, "KEY_TIME"),
    (0x168, "KEY_VENDOR"),
    (0x169, "KEY_ARCHIVE"),
    (0x16a, "KEY_PROGRAM"),  # Media Select Program Guide
    (0x16b, "KEY_CHANNEL"),
    (0x16c, "KEY_FAVORITES"),
    (0x16d, "KEY_EPG"),
    (0x16e, "KEY_PVR"),  # Media Select Home
    (0x16f, "KEY_MHP"),
    (0x170, "KEY_LANGUAGE"),
    (0x171, "KEY_TITLE"),
    (0x172, "KEY_SUBTITLE"),
    (0x173, "KEY_ANGLE"),
    (0x174, "KEY_ZOOM"),
    (0x175, "KEY_MODE"),
    (0x176, "KEY_KEYBOARD"),
    (0x177, "KEY_SCREEN"),
    (0x178, "KEY_PC"),  # Media Select Computer
    (0x179, "KEY_TV"),  # Media Select TV
    (0x17a, "KEY_TV2"),  # Media Select Cable
    (0x17b, "KEY_VCR"),  # Media Select VCR
    (0x17c, "KEY_VCR2"),  # VCR Plus
    (0x17d, "KEY_SAT"),  # Media Select Satellite
    (0x17e, "KEY_SAT2"),
    (0x17f, "KEY_CD"),  # Media Select CD
    (0x180, "KEY_TAPE"),  # Media Select Tape
    (0x181, "KEY_RADIO"),
    (0x182, "KEY_TUNER"),  # Media Select Tuner
    (0x183, "KEY_PLAYER"),
    (0x184, "KEY_TEXT"),
    (0x185, "KEY_DVD"),  # Media Select DVD
    (0x186, "KEY_AUX"),
    (0x187, "KEY_MP3"),
    (0x188, "KEY_AUDIO"),  # AL Audio Browser
    (0x189, "KEY_VIDEO"),  # AL Movie Browser
    (0x18a, "KEY_DIRECTORY"),
    (0x18b, "KEY_LIST"),
    (0x18c, "KEY_MEMO"),  # Media Select Messages
    (0x18d, "KEY_CALENDAR"),
    (0x18e, "KEY_RED"),
    (0x18f, "KEY_GREEN"),
    (0x190, "KEY_YELLOW"),
    (0x191, "KEY_BLUE"),
    (0x192, "KEY_CHANNELUP"),  # Channel Increment
    (0x193, "KEY_CHANNELDOWN"),  # Channel Decrement
    (0x194, "KEY_FIRST"),
    (0x195, "KEY_LAST"),  # Recall Last
    (0x196, "KEY_AB"),
    (0x197, "KEY_NEXT"),
    (0x198, "KEY_RESTART"),
    (0x199, "KEY_SLOW"),
    (0x19a, "KEY_SHUFFLE"),
    (0x19b, "KEY_BREAK"),
    (0x19c, "KEY_PREVIOUS"),
    (0x19d, "KEY_DIGITS"),
    (0x19e, "KEY_TEEN"),
    (0x19f, "KEY_TWEN"),
    (0x1a0, "KEY_VIDEOPHONE"),  # Media Select Video Phone
    (0x1a1, "KEY_GAMES"),  # Media Select Games
    (0x1a2, "KEY_ZOOMIN"),  # AC Zoom In
    (0x1a3, "KEY_ZOOMOUT"),  # AC Zoom Out
    (0x1a4, "KEY_ZOOMRESET"),  # AC Zoom
    (0x1a5, "KEY_WORDPROCESSOR"),  # AL Word Processor
    (0x1a6, "KEY_EDITOR"),  # AL Text Editor
    (0x1a7, "KEY_SPREADSHEET"),  # AL Spreadsheet
    (0x1a8, "KEY_GRAPHICSEDITOR"),  # AL Graphics Editor
    (0x1a9, "KEY_PRESENTATION"),  # AL Presentation App
    (0x1aa, "KEY_DATABASE"),  # AL Database App
    (0x1ab, "KEY_NEWS"),  # AL Newsreader
    (0x1ac, "KEY_VOICEMAIL"),  # AL Voicemail
    (0x1ad, "KEY_ADDRESSBOOK"),  # AL Contacts/Address Book
    (0x1ae, "KEY_MESSENGER"),  # AL Instant Messaging
    (0x1af, "KEY_DISPLAYTOGGLE"),  # Turn display (LCD) on and off
    (0x1b0, "KEY_SPELLCHECK"),  # AL Spell Check
    (0x1b1, "KEY_LOGOFF"),  # AL Logoff
    (0x1b2, "KEY_DOLLAR"),
    (0x1b3, "KEY_EURO"),
    (0x1b4, "KEY_FRAMEBACK"),  # Consumer - transport controls
    (0x1b5, "KEY_FRAMEFORWARD"),
    (0x1b6, "KEY_CONTEXT_MENU"),  # GenDesc - system context menu
    (0x1b7, "KEY_MEDIA_REPEAT"),  # Consumer - transport control
    (0x1b8, "KEY_10CHANNELSUP"),  # 10 channels up (10+)
    (0x1b9, "KEY_10CHANNELSDOWN"),  # 10 channels down (10-)
    (0x1ba, "KEY_IMAGES"),  # AL Image Browser
    (0x1c0, "KEY_DEL_EOL"),
    (0x1c1, "KEY_DEL_EOS"),
    (0x1c2, "KEY_INS_LINE"),
    (0x1c3, "KEY_DEL_LINE"),
    (0x1d0, "KEY_FN"),
    (0x1d1, "KEY_FN_ESC"),
    (0x1d2, "KEY_FN_F1"),
    (0x1d3, "KEY_FN_F2"),
    (0x1d4, "KEY_FN_F3"),
    (0x1d5, "KEY_FN_F4"),
    (0x1d6, "KEY_FN_F5"),
    (0x1d7, "KEY_FN_F6"),
    (0x1d8, "KEY_FN_F7"),
    (0x1d9, "KEY_FN_F8"),
    (0x1da, "KEY_FN_F9"),
    (0x1db, "KEY_FN_F10"),
    (0x1dc, "KEY_FN_F11"),
    (0x1dd, "KEY_FN_F12"),
    (0x1de, "KEY_FN_1"),
    (0x1df, "KEY_FN_2"),
    (0x1e0, "KEY_FN_D"),
    (0x1e1, "KEY_FN_E"),
    (0x1e2, "KEY_FN_F"),
    (0x1e3, "KEY_FN_S"),
    (0x1e4, "KEY_FN_B"),
    (0x1f1, "KEY_BRL_DOT1"),
    (0x1f2, "KEY_BRL_DOT2"),
    (0x1f3, "KEY_BRL_DOT3"),
    (0x1f4, "KEY_BRL_DOT4"),
    (0x1f5, "KEY_BRL_DOT5"),
    (0x1f6, "KEY_BRL_DOT6"),
    (0x1f7, "KEY_BRL_DOT7"),
    (0x1f8, "KEY_BRL_DOT8"),
    (0x1f9, "KEY_BRL_DOT9"),
    (0x1fa, "KEY_BRL_DOT10"),
    (0x200, "KEY_NUMERIC_0"),  # used by phones, remote controls,
    (0x201, "KEY_NUMERIC_1"),  # and other keypads
    (0x202, "KEY_NUMERIC_2"),
    (0x203, "KEY_NUMERIC_3"),
    (0x204, "KEY_NUMERIC_4"),
    (0x205, "KEY_NUMERIC_5"),
    (0x206, "KEY_NUMERIC_6"),
    (0x207, "KEY_NUMERIC_7"),
    (0x208, "KEY_NUMERIC_8"),
    (0x209, "KEY_NUMERIC_9"),
    (0x20a, "KEY_NUMERIC_STAR"),
    (0x20b, "KEY_NUMERIC_POUND"),
    (0x20c, "KEY_NUMERIC_A"),  # Phone key A - HUT Telephony 0xb9
    (0x20d, "KEY_NUMERIC_B"),
    (0x20e, "KEY_NUMERIC_C"),
    (0x20f, "KEY_NUMERIC_D"),
    (0x210, "KEY_CAMERA_FOCUS"),
    (0x211, "KEY_WPS_BUTTON"),  # WiFi Protected Setup key
    (0x212, "KEY_TOUCHPAD_TOGGLE"),  # Request switch touchpad on or off
    (0x213, "KEY_TOUCHPAD_ON"),
    (0x214, "KEY_TOUCHPAD_OFF"),
    (0x215, "KEY_CAMERA_ZOOMIN"),
    (0x216, "KEY_CAMERA_ZOOMOUT"),
    (0x217, "KEY_CAMERA_UP"),
    (0x218, "KEY_CAMERA_DOWN"),
    (0x219, "KEY_CAMERA_LEFT"),
    (0x21a, "KEY_CAMERA_RIGHT"),
    (0x21b, "KEY_ATTENDANT_ON"),
    (0x21c, "KEY_ATTENDANT_OFF"),
    (0x21d, "KEY_ATTENDANT_TOGGLE"),  # Attendant call on or off
    (0x21e, "KEY_LIGHTS_TOGGLE"),  # Reading light on or off
    (0x220, "BTN_DPAD_UP"),
    (0x221, "BTN_DPAD_DOWN"),
    (0x222, "BTN_DPAD_LEFT"),
    (0x223, "BTN_DPAD_RIGHT"),
    (0x230, "KEY_ALS_TOGGLE"),  # Ambient light sensor
    (0x240, "KEY_BUTTONCONFIG"),  # AL Button Configuration
    (0x241, "KEY_TASKMANAGER"),  # AL Task/Project Manager
    (0x242, "KEY_JOURNAL"),  # AL Log/Journal/Timecard
    (0x243, "KEY_CONTROLPANEL"),  # AL Control Panel
    (0x244, "KEY_APPSELECT"),  # AL Select Task/Application
    (0x245, "KEY_SCREENSAVER"),  # AL Screen Saver
    (0x246, "KEY_VOICECOMMAND"),  # Listening Voice Command
    (0x250, "KEY_BRIGHTNESS_MIN"),  # Set Brightness to Minimum
    (0x251, "KEY_BRIGHTNESS_MAX"),  # Set Brightness to Maximum
    (0x260, "KEY_KBDINPUTASSIST_PREV"),
    (0x261, "KEY_KBDINPUTASSIST_NEXT"),
    (0x262, "KEY_KBDINPUTASSIST_PREVGROUP"),
    (0x263, "KEY_KBDINPUTASSIST_NEXTGROUP"),
    (0x264, "KEY_KBDINPUTASSIST_ACCEPT"),
    (0x265, "KEY_KBDINPUTASSIST_CANCEL"),
    (0x2c0, "BTN_TRIGGER_HAPPY"),
    (0x2c0, "BTN_TRIGGER_HAPPY1"),
    (0x2c1, "BTN_TRIGGER_HAPPY2"),
    (0x2c2, "BTN_TRIGGER_HAPPY3"),
    (0x2c3, "BTN_TRIGGER_HAPPY4"),
    (0x2c4, "BTN_TRIGGER_HAPPY5"),
    (0x2c5, "BTN_TRIGGER_HAPPY6"),
    (0x2c6, "BTN_TRIGGER_HAPPY7"),
    (0x2c7, "BTN_TRIGGER_HAPPY8"),
    (0x2c8, "BTN_TRIGGER_HAPPY9"),
    (0x2c9, "BTN_TRIGGER_HAPPY10"),
    (0x2ca, "BTN_TRIGGER_HAPPY11"),
    (0x2cb, "BTN_TRIGGER_HAPPY12"),
    (0x2cc, "BTN_TRIGGER_HAPPY13"),
    (0x2cd, "BTN_TRIGGER_HAPPY14"),
    (0x2ce, "BTN_TRIGGER_HAPPY15"),
    (0x2cf, "BTN_TRIGGER_HAPPY16"),
    (0x2d0, "BTN_TRIGGER_HAPPY17"),
    (0x2d1, "BTN_TRIGGER_HAPPY18"),
    (0x2d2, "BTN_TRIGGER_HAPPY19"),
    (0x2d3, "BTN_TRIGGER_HAPPY20"),
    (0x2d4, "BTN_TRIGGER_HAPPY21"),
    (0x2d5, "BTN_TRIGGER_HAPPY22"),
    (0x2d6, "BTN_TRIGGER_HAPPY23"),
    (0x2d7, "BTN_TRIGGER_HAPPY24"),
    (0x2d8, "BTN_TRIGGER_HAPPY25"),
    (0x2d9, "BTN_TRIGGER_HAPPY26"),
    (0x2da, "BTN_TRIGGER_HAPPY27"),
    (0x2db, "BTN_TRIGGER_HAPPY28"),
    (0x2dc, "BTN_TRIGGER_HAPPY29"),
    (0x2dd, "BTN_TRIGGER_HAPPY30"),
    (0x2de, "BTN_TRIGGER_HAPPY31"),
    (0x2df, "BTN_TRIGGER_HAPPY32"),
    (0x2e0, "BTN_TRIGGER_HAPPY33"),
    (0x2e1, "BTN_TRIGGER_HAPPY34"),
    (0x2e2, "BTN_TRIGGER_HAPPY35"),
    (0x2e3, "BTN_TRIGGER_HAPPY36"),
    (0x2e4, "BTN_TRIGGER_HAPPY37"),
    (0x2e5, "BTN_TRIGGER_HAPPY38"),
    (0x2e6, "BTN_TRIGGER_HAPPY39"),
    (0x2e7, "BTN_TRIGGER_HAPPY40"),
    (0x2ff, "KEY_MAX"),
    (0x2ff+1, "KEY_CNT"))

RELATIVE_AXES = (
    (0x00, "REL_X"),
    (0x01, "REL_Y"),
    (0x02, "REL_Z"),
    (0x03, "REL_RX"),
    (0x04, "REL_RY"),
    (0x05, "REL_RZ"),
    (0x06, "REL_HWHEEL"),
    (0x07, "REL_DIAL"),
    (0x08, "REL_WHEEL"),
    (0x09, "REL_MISC"),
    (0x0f, "REL_MAX"),
    (0x0f+1, "REL_CNT"))

ABSOLUTE_AXES = (
    (0x00, "ABS_X"),
    (0x01, "ABS_Y"),
    (0x02, "ABS_Z"),
    (0x03, "ABS_RX"),
    (0x04, "ABS_RY"),
    (0x05, "ABS_RZ"),
    (0x06, "ABS_THROTTLE"),
    (0x07, "ABS_RUDDER"),
    (0x08, "ABS_WHEEL"),
    (0x09, "ABS_GAS"),
    (0x0a, "ABS_BRAKE"),
    (0x10, "ABS_HAT0X"),
    (0x11, "ABS_HAT0Y"),
    (0x12, "ABS_HAT1X"),
    (0x13, "ABS_HAT1Y"),
    (0x14, "ABS_HAT2X"),
    (0x15, "ABS_HAT2Y"),
    (0x16, "ABS_HAT3X"),
    (0x17, "ABS_HAT3Y"),
    (0x18, "ABS_PRESSURE"),
    (0x19, "ABS_DISTANCE"),
    (0x1a, "ABS_TILT_X"),
    (0x1b, "ABS_TILT_Y"),
    (0x1c, "ABS_TOOL_WIDTH"),
    (0x20, "ABS_VOLUME"),
    (0x28, "ABS_MISC"),
    (0x2f, "ABS_MT_SLOT"),  # MT slot being modified
    (0x30, "ABS_MT_TOUCH_MAJOR"),  # Major axis of touching ellipse
    (0x31, "ABS_MT_TOUCH_MINOR"),  # Minor axis (omit if circular)
    (0x32, "ABS_MT_WIDTH_MAJOR"),  # Major axis of approaching ellipse
    (0x33, "ABS_MT_WIDTH_MINOR"),  # Minor axis (omit if circular)
    (0x34, "ABS_MT_ORIENTATION"),  # Ellipse orientation
    (0x35, "ABS_MT_POSITION_X"),  # Center X touch position
    (0x36, "ABS_MT_POSITION_Y"),  # Center Y touch position
    (0x37, "ABS_MT_TOOL_TYPE"),  # Type of touching device
    (0x38, "ABS_MT_BLOB_ID"),  # Group a set of packets as a blob
    (0x39, "ABS_MT_TRACKING_ID"),  # Unique ID of initiated contact
    (0x3a, "ABS_MT_PRESSURE"),  # Pressure on contact area
    (0x3b, "ABS_MT_DISTANCE"),  # Contact hover distance
    (0x3c, "ABS_MT_TOOL_X"),  # Center X tool position
    (0x3d, "ABS_MT_TOOL_Y"),  # Center Y tool position
    (0x3f, "ABS_MAX"),
    (0x3f+1, "ABS_CNT"))

SWITCH_EVENTS = (
    (0x00, "SW_LID"),  # set = lid shut
    (0x01, "SW_TABLET_MODE"),  # set = tablet mode
    (0x02, "SW_HEADPHONE_INSERT"),  # set = inserted
    (0x03, "SW_RFKILL_ALL"),  # rfkill master switch, type "any"
    (0x04, "SW_MICROPHONE_INSERT"),  # set = inserted
    (0x05, "SW_DOCK"),  # set = plugged into dock
    (0x06, "SW_LINEOUT_INSERT"),  # set = inserted
    (0x07, "SW_JACK_PHYSICAL_INSERT"),  # set = mechanical switch set
    (0x08, "SW_VIDEOOUT_INSERT"),  # set = inserted
    (0x09, "SW_CAMERA_LENS_COVER"),  # set = lens covered
    (0x0a, "SW_KEYPAD_SLIDE"),  # set = keypad slide out
    (0x0b, "SW_FRONT_PROXIMITY"),  # set = front proximity sensor active
    (0x0c, "SW_ROTATE_LOCK"),  # set = rotate locked/disabled
    (0x0d, "SW_LINEIN_INSERT"),  # set = inserted
    (0x0e, "SW_MUTE_DEVICE"),  # set = device disabled
    (0x0f, "SW_MAX"),
    (0x0f+1, "SW_CNT"))

MISC_EVENTS = (
    (0x00, "MSC_SERIAL"),
    (0x01, "MSC_PULSELED"),
    (0x02, "MSC_GESTURE"),
    (0x03, "MSC_RAW"),
    (0x04, "MSC_SCAN"),
    (0x05, "MSC_TIMESTAMP"),
    (0x07, "MSC_MAX"),
    (0x07+1, "MSC_CNT"))

LEDS = (
    (0x00, "LED_NUML"),
    (0x01, "LED_CAPSL"),
    (0x02, "LED_SCROLLL"),
    (0x03, "LED_COMPOSE"),
    (0x04, "LED_KANA"),
    (0x05, "LED_SLEEP"),
    (0x06, "LED_SUSPEND"),
    (0x07, "LED_MUTE"),
    (0x08, "LED_MISC"),
    (0x09, "LED_MAIL"),
    (0x0a, "LED_CHARGING"),
    (0x0f, "LED_MAX"),
    (0x0f+1, "LED_CNT"))

AUTOREPEAT_VALUES = (
    (0x00, "REP_DELAY"),
    (0x01, "REP_PERIOD"),
    (0x01, "REP_MAX"),
    (0x01+1, "REP_CNT"))

SOUNDS = (
    (0x00, "SND_CLICK"),
    (0x01, "SND_BELL"),
    (0x02, "SND_TONE"),
    (0x07, "SND_MAX"),
    (0x07+1, "SND_CNT"))

# We have yet to support force feedback but probably should
# eventually:

FORCE_FEEDBACK = ()  # Motor in gamepad
FORCE_FEEDBACK_STATUS = ()  # Status of motor

POWER = ()  # Power switch

# These two are internal workings of evdev we probably will never care
# about.

MAX = ()
CURRENT = ()


EVENT_MAP = (
    ('types', EVENT_TYPES),
    ('type_codes', ((value, key) for key, value in EVENT_TYPES)),
    ('specials', SPECIAL_DEVICES),
    ('xpad', XINPUT_MAPPING),
    ('Sync', SYNCHRONIZATION_EVENTS),
    ('Key', KEYS_AND_BUTTONS),
    ('Relative', RELATIVE_AXES),
    ('Absolute', ABSOLUTE_AXES),
    ('Misc', MISC_EVENTS),
    ('Switch', SWITCH_EVENTS),
    ('LED', LEDS),
    ('Sound', SOUNDS),
    ('Repeat', AUTOREPEAT_VALUES),
    ('ForceFeedback', FORCE_FEEDBACK),
    ('Power', POWER),
    ('ForceFeedbackStatus', FORCE_FEEDBACK_STATUS),
    ('Max', MAX),
    ('Current', CURRENT))

WIN = True if platform.system() == 'Windows' else False


class PermissionDenied(IOError):
    """/dev/input not allowed by user.
    Common Linux problem."""
    pass


class UnpluggedError(RuntimeError):
    """The device requested is not plugged in."""
    pass


class UnknownEventType(IndexError):
    """We don't know what this event is."""
    pass


class UnknownEventCode(IndexError):
    """We don't know what this event is."""
    pass


class InputEvent(object):
    """A user event."""
    # pylint: disable=too-few-public-methods
    def __init__(self,
                 device,
                 event_info):
        self.device = device
        self.timestamp = event_info["timestamp"]
        self.code = event_info["code"]
        self.state = event_info["state"]
        self.ev_type = event_info["ev_type"]

# THING SING That thing can sing!
# SONG LONG A long, long song.
# Good-bye, Thing. You sing too long.
# pylint: disable=too-many-lines


class InputDevice(object):
    """A user input device."""
    def __init__(self, manager, device_path,
                 char_path_override=None):
        self.manager = manager
        self._device_path = device_path
        self.protocol, _, self.device_type = self._get_path_infomation()
        if char_path_override:
            self._character_device_path = char_path_override
        else:
            self._character_device_path = os.path.realpath(device_path)
        self._character_file = None
        if not WIN:
            with open("/sys/class/input/%s/device/name" %
                      self.get_char_name()) as name_file:
                self.name = name_file.read().strip()

    def _get_path_infomation(self):
        """Get useful infomation from the device path."""
        long_identifier = self._device_path.split('/')[4]
        protocol, remainder = long_identifier.split('-', 1)
        identifier, _, device_type = remainder.rsplit('-', 2)
        return (protocol, identifier, device_type)

    def get_char_name(self):

        """Get short version of char device name."""
        return self._character_device_path.split('/')[-1]

    def __str__(self):
        return self.name

    def __repr__(self):
        return '%s.%s("%s")' % (
            self.__module__,
            self.__class__.__name__,
            self._device_path)

    @property
    def _character_device(self):
        if not self._character_file:
            if WIN:
                self._character_file = io.BytesIO()
                return self._character_file
            try:
                self._character_file = io.open(
                    self._character_device_path, 'rb')
            except IOError as err:
                if err.errno == 13:
                    raise PermissionDenied(
                        "The user (that this program is being run as) does "
                        "not have permission to access the input events, "
                        "check groups and permissions, for example, on "
                        "Debian, the user needs to be in the input group.")
                else:
                    raise
        return self._character_file

    def __iter__(self, type_filter=None):
        event = self._do_iter(type_filter)
        if event:
            yield event

    def _do_iter(self, type_filter=None):
        while True:
            event = self._character_device.read(EVENT_SIZE)
            (tv_sec, tv_usec, ev_type, code, value) = struct.unpack(
                EVENT_FORMAT, event)
            event_type = self.manager.get_event_type(ev_type)
            if type_filter:
                if event_type != type_filter:
                    return

            eventinfo = {
                "ev_type": event_type,
                "state": value,
                "timestamp": tv_sec + (tv_usec / 1000000),
                "code": self.manager.get_event_string(event_type, code)
            }

            return InputEvent(self, eventinfo)

    def read(self):
        """Read the next input event."""
        return next(iter(self))


class Keyboard(InputDevice):
    """A keyboard or other key-like device."""
    pass


class Mouse(InputDevice):
    """A mouse or other pointing-like device."""
    pass


class XinputGamepad(ctypes.Structure):
    """Describes the current state of the Xbox 360 Controller.

    For full details see Microsoft's documentation:

    https://msdn.microsoft.com/en-us/library/windows/desktop/
    microsoft.directx_sdk.reference.xinput_gamepad%28v=vs.85%29.aspx

    """
    # pylint: disable=too-few-public-methods
    _fields_ = [
        ('buttons', ctypes.c_ushort),  # wButtons
        ('left_trigger', ctypes.c_ubyte),  # bLeftTrigger
        ('right_trigger', ctypes.c_ubyte),  # bLeftTrigger
        ('l_thumb_x', ctypes.c_short),  # sThumbLX
        ('l_thumb_y', ctypes.c_short),  # sThumbLY
        ('r_thumb_x', ctypes.c_short),  # sThumbRx
        ('r_thumb_y', ctypes.c_short),  # sThumbRy
    ]


class XinputState(ctypes.Structure):
    """Represents the state of a controller.

    For full details see Microsoft's documentation:

    https://msdn.microsoft.com/en-us/library/windows/desktop/
    microsoft.directx_sdk.reference.xinput_state%28v=vs.85%29.aspx

    """
    # pylint: disable=too-few-public-methods
    _fields_ = [
        ('packet_number', ctypes.c_ulong),  # dwPacketNumber
        ('gamepad', XinputGamepad),  # Gamepad
    ]


class XinputVibration(ctypes.Structure):
    """Specifies motor speed levels for the vibration function of a
    controller.

    For full details see Microsoft's documentation:

    https://msdn.microsoft.com/en-us/library/windows/desktop/
    microsoft.directx_sdk.reference.xinput_vibration%28v=vs.85%29.aspx

    """
    # pylint: disable=too-few-public-methods
    _fields_ = [("wLeftMotorSpeed", ctypes.c_ushort),
                ("wRightMotorSpeed", ctypes.c_ushort)]


class GamePad(InputDevice):
    """A gamepad or other joystick-like device."""
    def __init__(self, manager, device_path,
                 char_path_override=None):
        super(GamePad, self).__init__(manager,
                                      device_path,
                                      char_path_override)
        if WIN:
            if "Microsoft_Corporation_Controller" in self._device_path:
                self.name = "Microsoft X-Box 360 pad"
                identifier = self._get_path_infomation()[1]
                self.__device_number = int(identifier.split('_')[-1])
                self.__received_packets = 0
                self.__missed_packets = 0
                self.__last_state = self.__read_device()

    def __iter__(self, type_filter=None):
        if not WIN:
            event = super(GamePad, self)._do_iter(type_filter)
            if event:
                yield event

        else:
            while True:
                state = self.__read_device()
                if not state:
                    raise UnpluggedError(
                        "Gamepad %d is not connected" % self.__device_number)
                if state.packet_number != self.__last_state.packet_number:
                    # state has changed, handle the change
                    ievent = self.__handle_changed_state(state)
                    self.__last_state = state
                    yield ievent
                    self.__last_state = state

    @staticmethod
    def __get_timeval():
        """Get the time and make it into C style timeval."""
        frac, whole = math.modf(time.time())
        microseconds = math.floor(frac * 1000000)
        seconds = math.floor(whole)
        return seconds, microseconds

    def __create_event_object(self,
                              event_type,
                              code,
                              value,
                              timeval=None):
        if not timeval:
            timeval = self.__get_timeval()
        try:
            event_code = self.manager.codes['type_codes'][event_type]
        except KeyError:
            raise UnknownEventType(
                "We don't know what kind of event a %s is.",
                event_type)

        event = struct.pack(EVENT_FORMAT,
                            timeval[0],
                            timeval[1],
                            event_code,
                            code,
                            value)
        return event

    def __write_to_character_device(self, event_list, timeval=None):
        """Emulate the Linux character device on other platforms such as
        Windows."""
        # Remember the position of the stream
        pos = self._character_device.tell()
        # Go to the end of the stream
        self._character_device.seek(0, 2)
        # Write the new data to the end
        for event in event_list:
            self._character_device.write(event)
        # Add a sync marker
        sync = self.__create_event_object("Sync", 0, 0, timeval)
        self._character_device.write(sync)
        # Put the stream back to its original position
        self._character_device.seek(pos)

    def __handle_changed_state(self, state):
        """
        we need to pack a struct with the following five numbers:
        tv_sec, tv_usec, ev_type, code, value

        then write it using __write_to_character_device

        seconds, mircroseconds, ev_type, code, value
        time we just use now
        ev_type we look up
        code we look up
        value is 0 or 1 for the buttons
        axis value is maybe the same as Linux? Hope so!
        """
        timeval = self.__get_timeval()
        events = self.__get_button_events(state, timeval)
        axis_changes = self.__detect_axis_events(state)
        print(axis_changes)
        if events:
            self.__write_to_character_device(events, timeval)
        return "Hello Monkey"

    def __map_button(self, button):
        """Get the linux xpad code from the Windows xinput code."""
        _, start_code, start_value = button
        value = start_value
        code = self.manager.codes['xpad'][start_code]

        if button == 1 and start_value == 1:
            value = 0xFFFFFFFF
        elif button == 3 and start_value == 1:
            value = 0xFFFFFFFF
        return code, value

    def __get_button_events(self, state, timeval=None):
        """Get the button events from xinput."""
        changed_buttons = self.__detect_button_events(state)
        events = self.__emulate_buttons(changed_buttons, timeval)
        return events

    def __emulate_buttons(self, changed_buttons, timeval=None):
        """Make the button events use the Linux style format."""
        events = []
        for button in changed_buttons:
            code, value = self.__map_button(button)
            event = self.__create_event_object(
                "Key",
                code,
                value,
                timeval=timeval)
            events.append(event)

        print("events", events)
        return events

    @staticmethod
    def __gen_bit_values(number):
        """
        Return a zero or one for each bit of a numeric value up to the most
        significant 1 bit, beginning with the least significant bit.
        """
        number = int(number)
        while number:
            yield number & 0x1
            number >>= 1

    def __get_bit_values(self, number, size=32):
        """Get bit values as a list for a given number

        >>> get_bit_values(1) == [0]*31 + [1]
        True

        >>> get_bit_values(0xDEADBEEF)
        [1L, 1L, 0L, 1L, 1L, 1L, 1L,
        0L, 1L, 0L, 1L, 0L, 1L, 1L, 0L, 1L, 1L, 0L, 1L, 1L, 1L, 1L,
        1L, 0L, 1L, 1L, 1L, 0L, 1L, 1L, 1L, 1L]

        You may override the default word size of 32-bits to match your actual
        application.
        >>> get_bit_values(0x3, 2)
        [1L, 1L]

        >>> get_bit_values(0x3, 4)
        [0L, 0L, 1L, 1L]

        """
        res = list(self.__gen_bit_values(number))
        res.reverse()
        # 0-pad the most significant bit
        res = [0] * (size - len(res)) + res
        return res

    def __detect_button_events(self, state):
        changed = state.gamepad.buttons ^ self.__last_state.gamepad.buttons
        changed = self.__get_bit_values(changed, 16)
        buttons_state = self.__get_bit_values(state.gamepad.buttons, 16)
        changed.reverse()
        buttons_state.reverse()
        button_numbers = count(1)
        changed_buttons = list(
            filter(itemgetter(0),
                   list(zip(changed, button_numbers, buttons_state))))
        # returns for example [(1,15,1)] type, code, value?
        return changed_buttons

    @staticmethod
    def __translate_using_data_size(value, data_size):
        """Normalizes analog data to [0,1] for unsigned data and [-0.5,0.5]
        for signed data."""
        data_bits = 8 * data_size
        return float(value) / (2 ** data_bits - 1)

    def __detect_axis_events(self, state):
        # axis fields are everything but the buttons
        # pylint: disable=protected-access
        # Attribute name _fields_ is special name set by ctypes
        axis_fields = dict(XinputGamepad._fields_)
        axis_fields.pop('buttons')
        changed_axes = []
        for axis, ax_type in list(axis_fields.items()):
            old_val = getattr(self.__last_state.gamepad, axis)
            new_val = getattr(state.gamepad, axis)
            data_size = ctypes.sizeof(ax_type)
            old_val = self.__translate_using_data_size(old_val, data_size)
            new_val = self.__translate_using_data_size(new_val, data_size)

            # an attempt to add deadzones and dampen noise
            # done by feel rather than following
            # http://msdn.microsoft.com/en-gb/library/windows/
            # desktop/ee417001%28v=vs.85%29.aspx#dead_zone
            # ags, 2014-07-01
            if ((old_val != new_val and (
                    new_val > 0.08000000000000000
                    or new_val < -0.08000000000000000)
                 and abs(old_val - new_val) > 0.00000000500000000)
                    or (axis == 'right_trigger' or axis == 'left_trigger')
                    and new_val == 0
                    and abs(old_val - new_val) > 0.00000000500000000):
                changed_axes.append((axis, new_val))
        return changed_axes

    def __read_device(self):
        """Read the state of the gamepad."""
        state = XinputState()
        res = self.manager.xinput.XInputGetState(
            self.__device_number, ctypes.byref(state))
        if res == XINPUT_ERROR_SUCCESS:
            return state
        if res != XINPUT_ERROR_DEVICE_NOT_CONNECTED:
            raise RuntimeError(
                "Unknown error %d attempting to get state of device %d" % (
                    res, self.__device_number))
        # else return None (device is not connected)

    def set_vibration(self, left_motor, right_motor):
        "Control the speed of both motors seperately"
        if WIN:
            # Set up function argument types and return type
            xinput_set_state = self.manager.xinput.XInputSetState
            xinput_set_state.argtypes = [
                ctypes.c_uint, ctypes.POINTER(XinputVibration)]
            xinput_set_state.restype = ctypes.c_uint

            vibration = XinputVibration(
                int(left_motor * 65535), int(right_motor * 65535))
            xinput_set_state(self.__device_number, ctypes.byref(vibration))
        else:
            print("Not implemented yet. Coming soon.")


class OtherDevice(InputDevice):
    """A device of which its is type is either undetectable or has not
    been implemented yet.
    """
    pass


class DeviceManager(object):
    """Provides access to all connected and detectible user input
    devices."""

    def __init__(self):
        self.codes = {key: dict(value) for key, value in EVENT_MAP}
        self.keyboards = []
        self.mice = []
        self.gamepads = []
        self.other_devices = []
        self.all_devices = []
        self.xinput = None
        if WIN:
            self._find_devices_win()
        else:
            self._find_devices()
            self._update_all_devices()
        #  self._index = 0

    def _update_all_devices(self):
        """Update the all_devices list."""
        self.all_devices.extend(self.keyboards)
        self.all_devices.extend(self.mice)
        self.all_devices.extend(self.gamepads)
        self.all_devices.extend(self.other_devices)

    def _parse_device_path(self, device_path, char_path_override=None):
        """Parse each device and add to the approriate list."""
        try:
            device_type = device_path.rsplit('-', 1)[1]
        except IndexError:
            warn("The following device path was skipped as it could "
                 "not be parsed: %s" % device_path, RuntimeWarning)
            return

        if device_type == 'kbd':
            self.keyboards.append(Keyboard(self, device_path,
                                           char_path_override))
        elif device_type == 'mouse':
            self.mice.append(Mouse(self, device_path,
                                   char_path_override))
        elif device_type == 'joystick':
            self.gamepads.append(GamePad(self,
                                         device_path,
                                         char_path_override))
        else:
            self.other_devices.append(OtherDevice(self,
                                                  device_path,
                                                  char_path_override))

    def _find_xinput(self):
        """Find most recent xinput library."""
        for dll in XINPUT_DLL_NAMES:
            try:
                self.xinput = getattr(ctypes.windll, dll)
            except OSError:
                pass
            else:
                # We found an xinput driver
                break
        else:
            # We didn't find an xinput library
            warn("No xinput driver dll found, gamepads not supported.")

    def _find_devices_win(self):
        """Find devices on Windows."""
        self._find_xinput()
        self._detect_gamepads()

    def _detect_gamepads(self):
        """Find gamepads."""
        state = XinputState()
        # Windows allows up to 4 gamepads.
        for device_number in range(4):
            res = self.xinput.XInputGetState(
                device_number, ctypes.byref(state))
            if res == XINPUT_ERROR_SUCCESS:
                # We found a gamepad
                print("we found a gamepad.")
                device_path = (
                    "/dev/input/by_id/" +
                    "usb-Microsoft_Corporation_Controller_%s-event-joystick"
                    % device_number)
                self.gamepads.append(GamePad(self, device_path))
                continue
            if res != XINPUT_ERROR_DEVICE_NOT_CONNECTED:
                raise RuntimeError(
                    "Unknown error %d attempting to get state of device %d"
                    % (res, device_number))

    def _find_devices(self):
        """Find available devices."""
        # Start with everything given an id
        # I.e. those with fully correct kernel drivers
        for device_path in glob.glob('/dev/input/by-id/*-event-*'):
            self._parse_device_path(device_path)

        # We want a list of things we already found
        charnames = [device.get_char_name() for
                     device in self.all_devices]

        # Look for special devices
        for eventdir in glob.glob('/sys/class/input/event*'):
            char_name = os.path.split(eventdir)[1]
            if char_name in charnames:
                continue
            name_file = os.path.join(eventdir, 'device', 'name')
            with open(name_file) as name_file:
                device_name = name_file.read().strip()
                if device_name in self.codes['specials']:
                    self._parse_device_path(
                        self.codes['specials'][device_name],
                        os.path.join('/dev/input', char_name))

    def __iter__(self):
        return iter(self.all_devices)

    def __getitem__(self, index):
        try:
            return self.all_devices[index]
        except IndexError:
            raise IndexError("list index out of range")

    def get_event_type(self, raw_type):
        """Convert the code to a useful string name."""
        try:
            return self.codes['types'][raw_type]
        except KeyError:
            raise UnknownEventType("We don't know this event type")

    def get_event_string(self, evtype, code):
        """Get the string name of the event."""
        try:
            return self.codes[evtype][code]
        except KeyError:
            raise UnknownEventCode("We don't know this event.")


devices = DeviceManager()  # pylint: disable=invalid-name


def get_key():
    """Get a single keypress from a keyboard."""
    try:
        keyboard = devices.keyboards[0]
    except IndexError:
        raise UnpluggedError("No keyboard found.")
    return keyboard.read()


def get_mouse():
    """Get a single movement or click from a mouse."""
    try:
        mouse = devices.mice[0]
    except IndexError:
        raise UnpluggedError("No mice found.")
    return mouse.read()


def get_gamepad():
    """Get a single action from a gamepad."""
    try:
        gamepad = devices.gamepads[0]
    except IndexError:
        raise UnpluggedError("No gamepad found.")
    return gamepad.read()
