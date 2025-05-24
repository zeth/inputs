"""Constants for input devices."""

SPECIAL_DEVICES = (
    (
        "Raspberry Pi Sense HAT Joystick",
        "/dev/input/by-id/gpio-Raspberry_Pi_Sense_HAT_Joystick-event-kbd",
    ),
    (
        "Nintendo Wii Remote",
        "/dev/input/by-id/bluetooth-Nintendo_Wii_Remote-event-joystick",
    ),
    (
        "FT5406 memory based driver",
        "/dev/input/by-id/gpio-Raspberry_Pi_Touchscreen_Display-event-mouse",
    ),
)

XINPUT_MAPPING = (
    (1, 0x11),
    (2, 0x11),
    (3, 0x10),
    (4, 0x10),
    (5, 0x13A),
    (6, 0x13B),
    (7, 0x13D),
    (8, 0x13E),
    (9, 0x136),
    (10, 0x137),
    (13, 0x130),
    (14, 0x131),
    (15, 0x134),
    (16, 0x133),
    (17, 0x11),
    ("l_thumb_x", 0x00),
    ("l_thumb_y", 0x01),
    ("left_trigger", 0x02),
    ("r_thumb_x", 0x03),
    ("r_thumb_y", 0x04),
    ("right_trigger", 0x05),
)

XINPUT_DLL_NAMES = (
    "XInput1_4.dll",
    "XInput9_1_0.dll",
    "XInput1_3.dll",
    "XInput1_2.dll",
    "XInput1_1.dll",
)

XINPUT_ERROR_DEVICE_NOT_CONNECTED = 1167
XINPUT_ERROR_SUCCESS = 0

XBOX_STYLE_LED_CONTROL = {
    0: "off",
    1: "all blink, then previous setting",
    2: "1/top-left blink, then on",
    3: "2/top-right blink, then on",
    4: "3/bottom-left blink, then on",
    5: "4/bottom-right blink, then on",
    6: "1/top-left on",
    7: "2/top-right on",
    8: "3/bottom-left on",
    9: "4/bottom-right on",
    10: "rotate",
    11: "blink, based on previous setting",
    12: "slow blink, based on previous setting",
    13: "rotate with two lights",
    14: "persistent slow all blink",
    15: "blink once, then previous setting",
}

DEVICE_PROPERTIES = (
    (0x00, "INPUT_PROP_POINTER"),  # needs a pointer
    (0x01, "INPUT_PROP_DIRECT"),  # direct input devices
    (0x02, "INPUT_PROP_BUTTONPAD"),  # has button(s) under pad
    (0x03, "INPUT_PROP_SEMI_MT"),  # touch rectangle only
    (0x04, "INPUT_PROP_TOPBUTTONPAD"),  # softbuttons at top of pad
    (0x05, "INPUT_PROP_POINTING_STICK"),  # is a pointing stick
    (0x06, "INPUT_PROP_ACCELEROMETER"),  # has accelerometer
    (0x1F, "INPUT_PROP_MAX"),
    (0x1F + 1, "INPUT_PROP_CNT"),
)

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
    (0x1F, "Max"),
    (0x1F + 1, "Current"),
)

SYNCHRONIZATION_EVENTS = (
    (0, "SYN_REPORT"),
    (1, "SYN_CONFIG"),
    (2, "SYN_MT_REPORT"),
    (3, "SYN_DROPPED"),
    (0xF, "SYN_MAX"),
    (0xF + 1, "SYN_CNT"),
)

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
    (0x12A, "BTN_BASE5"),
    (0x12B, "BTN_BASE6"),
    (0x12F, "BTN_DEAD"),
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
    (0x13A, "BTN_SELECT"),
    (0x13B, "BTN_START"),
    (0x13C, "BTN_MODE"),
    (0x13D, "BTN_THUMBL"),
    (0x13E, "BTN_THUMBR"),
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
    (0x14A, "BTN_TOUCH"),
    (0x14B, "BTN_STYLUS"),
    (0x14C, "BTN_STYLUS2"),
    (0x14D, "BTN_TOOL_DOUBLETAP"),
    (0x14E, "BTN_TOOL_TRIPLETAP"),
    (0x14F, "BTN_TOOL_QUADTAP"),  # Four fingers on trackpad
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
    (0x16A, "KEY_PROGRAM"),  # Media Select Program Guide
    (0x16B, "KEY_CHANNEL"),
    (0x16C, "KEY_FAVORITES"),
    (0x16D, "KEY_EPG"),
    (0x16E, "KEY_PVR"),  # Media Select Home
    (0x16F, "KEY_MHP"),
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
    (0x17A, "KEY_TV2"),  # Media Select Cable
    (0x17B, "KEY_VCR"),  # Media Select VCR
    (0x17C, "KEY_VCR2"),  # VCR Plus
    (0x17D, "KEY_SAT"),  # Media Select Satellite
    (0x17E, "KEY_SAT2"),
    (0x17F, "KEY_CD"),  # Media Select CD
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
    (0x18A, "KEY_DIRECTORY"),
    (0x18B, "KEY_LIST"),
    (0x18C, "KEY_MEMO"),  # Media Select Messages
    (0x18D, "KEY_CALENDAR"),
    (0x18E, "KEY_RED"),
    (0x18F, "KEY_GREEN"),
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
    (0x19A, "KEY_SHUFFLE"),
    (0x19B, "KEY_BREAK"),
    (0x19C, "KEY_PREVIOUS"),
    (0x19D, "KEY_DIGITS"),
    (0x19E, "KEY_TEEN"),
    (0x19F, "KEY_TWEN"),
    (0x1A0, "KEY_VIDEOPHONE"),  # Media Select Video Phone
    (0x1A1, "KEY_GAMES"),  # Media Select Games
    (0x1A2, "KEY_ZOOMIN"),  # AC Zoom In
    (0x1A3, "KEY_ZOOMOUT"),  # AC Zoom Out
    (0x1A4, "KEY_ZOOMRESET"),  # AC Zoom
    (0x1A5, "KEY_WORDPROCESSOR"),  # AL Word Processor
    (0x1A6, "KEY_EDITOR"),  # AL Text Editor
    (0x1A7, "KEY_SPREADSHEET"),  # AL Spreadsheet
    (0x1A8, "KEY_GRAPHICSEDITOR"),  # AL Graphics Editor
    (0x1A9, "KEY_PRESENTATION"),  # AL Presentation App
    (0x1AA, "KEY_DATABASE"),  # AL Database App
    (0x1AB, "KEY_NEWS"),  # AL Newsreader
    (0x1AC, "KEY_VOICEMAIL"),  # AL Voicemail
    (0x1AD, "KEY_ADDRESSBOOK"),  # AL Contacts/Address Book
    (0x1AE, "KEY_MESSENGER"),  # AL Instant Messaging
    (0x1AF, "KEY_DISPLAYTOGGLE"),  # Turn display (LCD) on and off
    (0x1B0, "KEY_SPELLCHECK"),  # AL Spell Check
    (0x1B1, "KEY_LOGOFF"),  # AL Logoff
    (0x1B2, "KEY_DOLLAR"),
    (0x1B3, "KEY_EURO"),
    (0x1B4, "KEY_FRAMEBACK"),  # Consumer - transport controls
    (0x1B5, "KEY_FRAMEFORWARD"),
    (0x1B6, "KEY_CONTEXT_MENU"),  # GenDesc - system context menu
    (0x1B7, "KEY_MEDIA_REPEAT"),  # Consumer - transport control
    (0x1B8, "KEY_10CHANNELSUP"),  # 10 channels up (10+)
    (0x1B9, "KEY_10CHANNELSDOWN"),  # 10 channels down (10-)
    (0x1BA, "KEY_IMAGES"),  # AL Image Browser
    (0x1C0, "KEY_DEL_EOL"),
    (0x1C1, "KEY_DEL_EOS"),
    (0x1C2, "KEY_INS_LINE"),
    (0x1C3, "KEY_DEL_LINE"),
    (0x1D0, "KEY_FN"),
    (0x1D1, "KEY_FN_ESC"),
    (0x1D2, "KEY_FN_F1"),
    (0x1D3, "KEY_FN_F2"),
    (0x1D4, "KEY_FN_F3"),
    (0x1D5, "KEY_FN_F4"),
    (0x1D6, "KEY_FN_F5"),
    (0x1D7, "KEY_FN_F6"),
    (0x1D8, "KEY_FN_F7"),
    (0x1D9, "KEY_FN_F8"),
    (0x1DA, "KEY_FN_F9"),
    (0x1DB, "KEY_FN_F10"),
    (0x1DC, "KEY_FN_F11"),
    (0x1DD, "KEY_FN_F12"),
    (0x1DE, "KEY_FN_1"),
    (0x1DF, "KEY_FN_2"),
    (0x1E0, "KEY_FN_D"),
    (0x1E1, "KEY_FN_E"),
    (0x1E2, "KEY_FN_F"),
    (0x1E3, "KEY_FN_S"),
    (0x1E4, "KEY_FN_B"),
    (0x1F1, "KEY_BRL_DOT1"),
    (0x1F2, "KEY_BRL_DOT2"),
    (0x1F3, "KEY_BRL_DOT3"),
    (0x1F4, "KEY_BRL_DOT4"),
    (0x1F5, "KEY_BRL_DOT5"),
    (0x1F6, "KEY_BRL_DOT6"),
    (0x1F7, "KEY_BRL_DOT7"),
    (0x1F8, "KEY_BRL_DOT8"),
    (0x1F9, "KEY_BRL_DOT9"),
    (0x1FA, "KEY_BRL_DOT10"),
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
    (0x20A, "KEY_NUMERIC_STAR"),
    (0x20B, "KEY_NUMERIC_POUND"),
    (0x20C, "KEY_NUMERIC_A"),  # Phone key A - HUT Telephony 0xb9
    (0x20D, "KEY_NUMERIC_B"),
    (0x20E, "KEY_NUMERIC_C"),
    (0x20F, "KEY_NUMERIC_D"),
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
    (0x21A, "KEY_CAMERA_RIGHT"),
    (0x21B, "KEY_ATTENDANT_ON"),
    (0x21C, "KEY_ATTENDANT_OFF"),
    (0x21D, "KEY_ATTENDANT_TOGGLE"),  # Attendant call on or off
    (0x21E, "KEY_LIGHTS_TOGGLE"),  # Reading light on or off
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
    (0x2C0, "BTN_TRIGGER_HAPPY"),
    (0x2C0, "BTN_TRIGGER_HAPPY1"),
    (0x2C1, "BTN_TRIGGER_HAPPY2"),
    (0x2C2, "BTN_TRIGGER_HAPPY3"),
    (0x2C3, "BTN_TRIGGER_HAPPY4"),
    (0x2C4, "BTN_TRIGGER_HAPPY5"),
    (0x2C5, "BTN_TRIGGER_HAPPY6"),
    (0x2C6, "BTN_TRIGGER_HAPPY7"),
    (0x2C7, "BTN_TRIGGER_HAPPY8"),
    (0x2C8, "BTN_TRIGGER_HAPPY9"),
    (0x2C9, "BTN_TRIGGER_HAPPY10"),
    (0x2CA, "BTN_TRIGGER_HAPPY11"),
    (0x2CB, "BTN_TRIGGER_HAPPY12"),
    (0x2CC, "BTN_TRIGGER_HAPPY13"),
    (0x2CD, "BTN_TRIGGER_HAPPY14"),
    (0x2CE, "BTN_TRIGGER_HAPPY15"),
    (0x2CF, "BTN_TRIGGER_HAPPY16"),
    (0x2D0, "BTN_TRIGGER_HAPPY17"),
    (0x2D1, "BTN_TRIGGER_HAPPY18"),
    (0x2D2, "BTN_TRIGGER_HAPPY19"),
    (0x2D3, "BTN_TRIGGER_HAPPY20"),
    (0x2D4, "BTN_TRIGGER_HAPPY21"),
    (0x2D5, "BTN_TRIGGER_HAPPY22"),
    (0x2D6, "BTN_TRIGGER_HAPPY23"),
    (0x2D7, "BTN_TRIGGER_HAPPY24"),
    (0x2D8, "BTN_TRIGGER_HAPPY25"),
    (0x2D9, "BTN_TRIGGER_HAPPY26"),
    (0x2DA, "BTN_TRIGGER_HAPPY27"),
    (0x2DB, "BTN_TRIGGER_HAPPY28"),
    (0x2DC, "BTN_TRIGGER_HAPPY29"),
    (0x2DD, "BTN_TRIGGER_HAPPY30"),
    (0x2DE, "BTN_TRIGGER_HAPPY31"),
    (0x2DF, "BTN_TRIGGER_HAPPY32"),
    (0x2E0, "BTN_TRIGGER_HAPPY33"),
    (0x2E1, "BTN_TRIGGER_HAPPY34"),
    (0x2E2, "BTN_TRIGGER_HAPPY35"),
    (0x2E3, "BTN_TRIGGER_HAPPY36"),
    (0x2E4, "BTN_TRIGGER_HAPPY37"),
    (0x2E5, "BTN_TRIGGER_HAPPY38"),
    (0x2E6, "BTN_TRIGGER_HAPPY39"),
    (0x2E7, "BTN_TRIGGER_HAPPY40"),
    (0x2FF, "KEY_MAX"),
    (0x2FF + 1, "KEY_CNT"),
)

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
    (0x0F, "REL_MAX"),
    (0x0F + 1, "REL_CNT"),
)

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
    (0x0A, "ABS_BRAKE"),
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
    (0x1A, "ABS_TILT_X"),
    (0x1B, "ABS_TILT_Y"),
    (0x1C, "ABS_TOOL_WIDTH"),
    (0x20, "ABS_VOLUME"),
    (0x28, "ABS_MISC"),
    (0x2F, "ABS_MT_SLOT"),  # MT slot being modified
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
    (0x3A, "ABS_MT_PRESSURE"),  # Pressure on contact area
    (0x3B, "ABS_MT_DISTANCE"),  # Contact hover distance
    (0x3C, "ABS_MT_TOOL_X"),  # Center X tool position
    (0x3D, "ABS_MT_TOOL_Y"),  # Center Y tool position
    (0x3F, "ABS_MAX"),
    (0x3F + 1, "ABS_CNT"),
)

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
    (0x0A, "SW_KEYPAD_SLIDE"),  # set = keypad slide out
    (0x0B, "SW_FRONT_PROXIMITY"),  # set = front proximity sensor active
    (0x0C, "SW_ROTATE_LOCK"),  # set = rotate locked/disabled
    (0x0D, "SW_LINEIN_INSERT"),  # set = inserted
    (0x0E, "SW_MUTE_DEVICE"),  # set = device disabled
    (0x0F, "SW_MAX"),
    (0x0F + 1, "SW_CNT"),
)

MISC_EVENTS = (
    (0x00, "MSC_SERIAL"),
    (0x01, "MSC_PULSELED"),
    (0x02, "MSC_GESTURE"),
    (0x03, "MSC_RAW"),
    (0x04, "MSC_SCAN"),
    (0x05, "MSC_TIMESTAMP"),
    (0x07, "MSC_MAX"),
    (0x07 + 1, "MSC_CNT"),
)

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
    (0x0A, "LED_CHARGING"),
    (0x0F, "LED_MAX"),
    (0x0F + 1, "LED_CNT"),
)

LED_TYPE_CODES = (
    ("numlock", 0x00),
    ("capslock", 0x01),
    ("scrolllock", 0x02),
    ("compose", 0x03),
    ("kana", 0x04),
    ("sleep", 0x05),
    ("suspend", 0x06),
    ("mute", 0x07),
    ("misc", 0x08),
    ("mail", 0x09),
    ("charging", 0x0A),
    ("max", 0x0F),
    ("cnt", 0x0F + 1),
)

AUTOREPEAT_VALUES = (
    (0x00, "REP_DELAY"),
    (0x01, "REP_PERIOD"),
    (0x01, "REP_MAX"),
    (0x01 + 1, "REP_CNT"),
)

SOUNDS = (
    (0x00, "SND_CLICK"),
    (0x01, "SND_BELL"),
    (0x02, "SND_TONE"),
    (0x07, "SND_MAX"),
    (0x07 + 1, "SND_CNT"),
)

WIN_KEYBOARD_CODES = {
    0x0100: 1,
    0x0101: 0,
    0x104: 1,
    0x105: 0,
}

WIN_MOUSE_CODES = {
    0x0201: (0x110, 1, 589825),  # WM_LBUTTONDOWN --> BTN_LEFT
    0x0202: (0x110, 0, 589825),  # WM_LBUTTONUP   --> BTN_LEFT
    0x0204: (0x111, 1, 589826),  # WM_RBUTTONDOWN --> BTN_RIGHT
    0x0205: (0x111, 0, 589826),  # WM_RBUTTONUP   --> BTN_RIGHT
    0x0207: (0x112, 1, 589827),  # WM_MBUTTONDOWN --> BTN_MIDDLE
    0x0208: (0x112, 0, 589827),  # WM_MBUTTONU    --> BTN_MIDDLE
    0x020B: (0x113, 1, 589828),  # WM_XBUTTONDOWN --> BTN_SIDE
    0x020C: (0x113, 0, 589828),  # WM_XBUTTONUP   --> BTN_SIDE
    0x020B2: (0x114, 1, 589829),  # WM_XBUTTONDOWN --> BTN_EXTRA
    0x020C2: (0x114, 0, 589829),  # WM_XBUTTONUP   --> BTN_EXTRA
}

# THING SING That thing can sing!
# SONG LONG A long, long song.
# Good-bye, Thing. You sing too long.
# pylint: disable=too-many-lines

WINCODES = (
    (0x01, 0x110),  # Left mouse button
    (0x02, 0x111),  # Right mouse button
    (0x03, 0),  # Control-break processing
    (0x04, 0x112),  # Middle mouse button (three-button mouse)
    (0x05, 0x113),  # X1 mouse button
    (0x06, 0x114),  # X2 mouse button
    (0x07, 0),  # Undefined
    (0x08, 14),  # BACKSPACE key
    (0x09, 15),  # TAB key
    (0x0A, 0),  # Reserved
    (0x0B, 0),  # Reserved
    (0x0C, 0x163),  # CLEAR key
    (0x0D, 28),  # ENTER key
    (0x0E, 0),  # Undefined
    (0x0F, 0),  # Undefined
    (0x10, 42),  # SHIFT key
    (0x11, 29),  # CTRL key
    (0x12, 56),  # ALT key
    (0x13, 119),  # PAUSE key
    (0x14, 58),  # CAPS LOCK key
    (0x15, 90),  # IME Kana mode
    (0x15, 91),  # IME Hanguel mode (maintained for compatibility; use
    # VK_HANGUL)
    (0x15, 91),  # IME Hangul mode
    (0x16, 0),  # Undefined
    (0x17, 92),  # IME Junja mode - These all need to be fixed
    (0x18, 93),  # IME final mode - By someone who
    (0x19, 94),  # IME Hanja mode - Knows how
    (0x19, 95),  # IME Kanji mode - Japanese Keyboards work
    (0x1A, 0),  # Undefined
    (0x1B, 1),  # ESC key
    (0x1C, 0),  # IME convert
    (0x1D, 0),  # IME nonconvert
    (0x1E, 0),  # IME accept
    (0x1F, 0),  # IME mode change request
    (0x20, 57),  # SPACEBAR
    (0x21, 104),  # PAGE UP key
    (0x22, 109),  # PAGE DOWN key
    (0x23, 107),  # END key
    (0x24, 102),  # HOME key
    (0x25, 105),  # LEFT ARROW key
    (0x26, 103),  # UP ARROW key
    (0x27, 106),  # RIGHT ARROW key
    (0x28, 108),  # DOWN ARROW key
    (0x29, 0x161),  # SELECT key
    (0x2A, 210),  # PRINT key
    (0x2B, 28),  # EXECUTE key
    (0x2C, 99),  # PRINT SCREEN key
    (0x2D, 110),  # INS key
    (0x2E, 111),  # DEL key
    (0x2F, 138),  # HELP key
    (0x30, 11),  # 0 key
    (0x31, 2),  # 1 key
    (0x32, 3),  # 2 key
    (0x33, 4),  # 3 key
    (0x34, 5),  # 4 key
    (0x35, 6),  # 5 key
    (0x36, 7),  # 6 key
    (0x37, 8),  # 7 key
    (0x38, 9),  # 8 key
    (0x39, 10),  # 9 key
    #  (0x3A-40, 0),  # Undefined
    (0x41, 30),  # A key
    (0x42, 48),  # B key
    (0x43, 46),  # C key
    (0x44, 32),  # D key
    (0x45, 18),  # E key
    (0x46, 33),  # F key
    (0x47, 34),  # G key
    (0x48, 35),  # H key
    (0x49, 23),  # I key
    (0x4A, 36),  # J key
    (0x4B, 37),  # K key
    (0x4C, 38),  # L key
    (0x4D, 50),  # M key
    (0x4E, 49),  # N key
    (0x4F, 24),  # O key
    (0x50, 25),  # P key
    (0x51, 16),  # Q key
    (0x52, 19),  # R key
    (0x53, 31),  # S key
    (0x54, 20),  # T key
    (0x55, 22),  # U key
    (0x56, 47),  # V key
    (0x57, 17),  # W key
    (0x58, 45),  # X key
    (0x59, 21),  # Y key
    (0x5A, 44),  # Z key
    (0x5B, 125),  # Left Windows key (Natural keyboard)
    (0x5C, 126),  # Right Windows key (Natural keyboard)
    (0x5D, 139),  # Applications key (Natural keyboard)
    (0x5E, 0),  # Reserved
    (0x5F, 142),  # Computer Sleep key
    (0x60, 82),  # Numeric keypad 0 key
    (0x61, 79),  # Numeric keypad 1 key
    (0x62, 80),  # Numeric keypad 2 key
    (0x63, 81),  # Numeric keypad 3 key
    (0x64, 75),  # Numeric keypad 4 key
    (0x65, 76),  # Numeric keypad 5 key
    (0x66, 77),  # Numeric keypad 6 key
    (0x67, 71),  # Numeric keypad 7 key
    (0x68, 72),  # Numeric keypad 8 key
    (0x69, 73),  # Numeric keypad 9 key
    (0x6A, 55),  # Multiply key
    (0x6B, 78),  # Add key
    (0x6C, 96),  # Separator key
    (0x6D, 74),  # Subtract key
    (0x6E, 83),  # Decimal key
    (0x6F, 98),  # Divide key
    (0x70, 59),  # F1 key
    (0x71, 60),  # F2 key
    (0x72, 61),  # F3 key
    (0x73, 62),  # F4 key
    (0x74, 63),  # F5 key
    (0x75, 64),  # F6 key
    (0x76, 65),  # F7 key
    (0x77, 66),  # F8 key
    (0x78, 67),  # F9 key
    (0x79, 68),  # F10 key
    (0x7A, 87),  # F11 key
    (0x7B, 88),  # F12 key
    (0x7C, 183),  # F13 key
    (0x7D, 184),  # F14 key
    (0x7E, 185),  # F15 key
    (0x7F, 186),  # F16 key
    (0x80, 187),  # F17 key
    (0x81, 188),  # F18 key
    (0x82, 189),  # F19 key
    (0x83, 190),  # F20 key
    (0x84, 191),  # F21 key
    (0x85, 192),  # F22 key
    (0x86, 192),  # F23 key
    (0x87, 194),  # F24 key
    #  (0x88-8F, 0),  # Unassigned
    (0x90, 69),  # NUM LOCK key
    (0x91, 70),  # SCROLL LOCK key
    #  (0x92-96, 0),  # OEM specific
    #  (0x97-9F, 0),  # Unassigned
    (0xA0, 42),  # Left SHIFT key
    (0xA1, 54),  # Right SHIFT key
    (0xA2, 29),  # Left CONTROL key
    (0xA3, 97),  # Right CONTROL key
    (0xA4, 125),  # Left MENU key
    (0xA5, 126),  # Right MENU key
    (0xA6, 158),  # Browser Back key
    (0xA7, 159),  # Browser Forward key
    (0xA8, 173),  # Browser Refresh key
    (0xA9, 128),  # Browser Stop key
    (0xAA, 217),  # Browser Search key
    (0xAB, 0x16C),  # Browser Favorites key
    (0xAC, 150),  # Browser Start and Home key
    (0xAD, 113),  # Volume Mute key
    (0xAE, 114),  # Volume Down key
    (0xAF, 115),  # Volume Up key
    (0xB0, 163),  # Next Track key
    (0xB1, 165),  # Previous Track key
    (0xB2, 166),  # Stop Media key
    (0xB3, 164),  # Play/Pause Media key
    (0xB4, 155),  # Start Mail key
    (0xB5, 0x161),  # Select Media key
    (0xB6, 148),  # Start Application 1 key
    (0xB7, 149),  # Start Application 2 key
    #  (0xB8-B9, 0),  # Reserved
    (0xBA, 39),  # Used for miscellaneous characters; it can vary by keyboard.
    (0xBB, 13),  # For any country/region, the '+' key
    (0xBC, 51),  # For any country/region, the ',' key
    (0xBD, 12),  # For any country/region, the '-' key
    (0xBE, 52),  # For any country/region, the '.' key
    (0xBF, 53),  # Slash
    (0xC0, 40),  # Apostrophe
    #  (0xC1-D7, 0),  # Reserved
    #  (0xD8-DA, 0),  # Unassigned
    (0xDB, 26),  # [
    (0xDC, 86),  # \
    (0xDD, 27),  # ]
    (0xDE, 43),  # '
    (0xDF, 119),  # VK_OFF - What's that?
    (0xE0, 0),  # Reserved
    (0xE1, 0),  # OEM Specific
    (0xE2, 43),  # Either the angle bracket key or the backslash key
    # on the RT 102-key keyboard (0xE3-E4, 0), # OEM
    # specific
    (0xE5, 0),  # IME PROCESS key
    (0xE6, 0),  # OEM specific
    (0xE7, 0),  # Used to pass Unicode characters as if they were
    # keystrokes. The VK_PACKET key is the low word of a
    # 32-bit Virtual Key value used for non-keyboard input
    # methods. For more information, see Remark in
    # KEYBDINPUT, SendInput, WM_KEYDOWN, and WM_KEYUP
    (0xE8, 0),  # Unassigned
    #  (0xE9-F5, 0),  # OEM specific
    (0xF6, 0),  # Attn key
    (0xF7, 0),  # CrSel key
    (0xF8, 0),  # ExSel key
    (0xF9, 222),  # Erase EOF key
    (0xFA, 207),  # Play key
    (0xFB, 0x174),  # Zoom key
    (0xFC, 0),  # Reserved
    (0xFD, 0x19B),  # PA1 key
    (0xFE, 0x163),  # Clear key
    (0xFF, 185),
)

MAC_EVENT_CODES = (
    # NSLeftMouseDown Quartz.kCGEventLeftMouseDown
    (1, ("Key", 0x110, 1, 589825)),
    # NSLeftMouseUp Quartz.kCGEventLeftMouseUp
    (2, ("Key", 0x110, 0, 589825)),
    # NSRightMouseDown Quartz.kCGEventRightMouseDown
    (3, ("Key", 0x111, 1, 589826)),
    # NSRightMouseUp Quartz.kCGEventRightMouseUp
    (4, ("Key", 0x111, 0, 589826)),
    (5, (None, 0, 0, 0)),  # NSMouseMoved Quartz.kCGEventMouseMoved
    (6, (None, 0, 0, 0)),  # NSLeftMouseDragged Quartz.kCGEventLeftMouseDragged
    # NSRightMouseDragged Quartz.kCGEventRightMouseDragged
    (7, (None, 0, 0, 0)),
    (8, (None, 0, 0, 0)),  # NSMouseEntered
    (9, (None, 0, 0, 0)),  # NSMouseExited
    (10, (None, 0, 0, 0)),  # NSKeyDown
    (11, (None, 0, 0, 0)),  # NSKeyUp
    (12, (None, 0, 0, 0)),  # NSFlagsChanged
    (13, (None, 0, 0, 0)),  # NSAppKitDefined
    (14, (None, 0, 0, 0)),  # NSSystemDefined
    (15, (None, 0, 0, 0)),  # NSApplicationDefined
    (16, (None, 0, 0, 0)),  # NSPeriodic
    (17, (None, 0, 0, 0)),  # NSCursorUpdate
    (22, (None, 0, 0, 0)),  # NSScrollWheel Quartz.kCGEventScrollWheel
    (23, (None, 0, 0, 0)),  # NSTabletPoint Quartz.kCGEventTabletPointer
    (24, (None, 0, 0, 0)),  # NSTabletProximity Quartz.kCGEventTabletProximity
    (25, (None, 0, 0, 0)),  # NSOtherMouseDown Quartz.kCGEventOtherMouseDown
    (25.2, ("Key", 0x112, 1, 589827)),  # BTN_MIDDLE
    (25.3, ("Key", 0x113, 1, 589828)),  # BTN_SIDE
    (25.4, ("Key", 0x114, 1, 589829)),  # BTN_EXTRA
    (26, (None, 0, 0, 0)),  # NSOtherMouseUp Quartz.kCGEventOtherMouseUp
    (26.2, ("Key", 0x112, 0, 589827)),  # BTN_MIDDLE
    (26.3, ("Key", 0x113, 0, 589828)),  # BTN_SIDE
    (26.4, ("Key", 0x114, 0, 589829)),  # BTN_EXTRA
    (27, (None, 0, 0, 0)),  # NSOtherMouseDragged
    (29, (None, 0, 0, 0)),  # NSEventTypeGesture
    (30, (None, 0, 0, 0)),  # NSEventTypeMagnify
    (31, (None, 0, 0, 0)),  # NSEventTypeSwipe
    (18, (None, 0, 0, 0)),  # NSEventTypeRotate
    (19, (None, 0, 0, 0)),  # NSEventTypeBeginGesture
    (20, (None, 0, 0, 0)),  # NSEventTypeEndGesture
    (27, (None, 0, 0, 0)),  # Quartz.kCGEventOtherMouseDragged
    (32, (None, 0, 0, 0)),  # NSEventTypeSmartMagnify
    (33, (None, 0, 0, 0)),  # NSEventTypeQuickLook
    (34, (None, 0, 0, 0)),  # NSEventTypePressure
)

MAC_KEYS = (
    (0x00, 30),  # kVK_ANSI_A
    (0x01, 31),  # kVK_ANSI_S    (0x02, 32),  # kVK_ANSI_D
    (0x03, 33),  # kVK_ANSI_F
    (0x04, 35),  # kVK_ANSI_H
    (0x05, 34),  # kVK_ANSI_G
    (0x06, 44),  # kVK_ANSI_Z
    (0x07, 45),  # kVK_ANSI_X
    (0x08, 46),  # kVK_ANSI_C
    (0x09, 47),  # kVK_ANSI_V
    (0x0B, 48),  # kVK_ANSI_B
    (0x0C, 16),  # kVK_ANSI_Q
    (0x0D, 17),  # kVK_ANSI_W
    (0x0E, 18),  # kVK_ANSI_E
    (0x0F, 33),  # kVK_ANSI_R
    (0x10, 21),  # kVK_ANSI_Y
    (0x11, 20),  # kVK_ANSI_T
    (0x12, 2),  # kVK_ANSI_1
    (0x13, 3),  # kVK_ANSI_2
    (0x14, 4),  # kVK_ANSI_3
    (0x15, 5),  # kVK_ANSI_4
    (0x16, 7),  # kVK_ANSI_6
    (0x17, 6),  # kVK_ANSI_5
    (0x18, 13),  # kVK_ANSI_Equal
    (0x19, 10),  # kVK_ANSI_9
    (0x1A, 8),  # kVK_ANSI_7
    (0x1B, 12),  # kVK_ANSI_Minus
    (0x1C, 9),  # kVK_ANSI_8
    (0x1D, 11),  # kVK_ANSI_0
    (0x1E, 27),  # kVK_ANSI_RightBracket
    (0x1F, 24),  # kVK_ANSI_O
    (0x20, 22),  # kVK_ANSI_U
    (0x21, 26),  # kVK_ANSI_LeftBracket
    (0x22, 23),  # kVK_ANSI_I
    (0x23, 25),  # kVK_ANSI_P
    (0x25, 38),  # kVK_ANSI_L
    (0x26, 36),  # kVK_ANSI_J
    (0x27, 40),  # kVK_ANSI_Quote
    (0x28, 37),  # kVK_ANSI_K
    (0x29, 39),  # kVK_ANSI_Semicolon
    (0x2A, 43),  # kVK_ANSI_Backslash
    (0x2B, 51),  # kVK_ANSI_Comma
    (0x2C, 53),  # kVK_ANSI_Slash
    (0x2D, 49),  # kVK_ANSI_N
    (0x2E, 50),  # kVK_ANSI_M
    (0x2F, 52),  # kVK_ANSI_Period
    (0x32, 41),  # kVK_ANSI_Grave
    (0x41, 83),  # kVK_ANSI_KeypadDecimal
    (0x43, 55),  # kVK_ANSI_KeypadMultiply
    (0x45, 78),  # kVK_ANSI_KeypadPlus
    (0x47, 69),  # kVK_ANSI_KeypadClear
    (0x4B, 98),  # kVK_ANSI_KeypadDivide
    (0x4C, 96),  # kVK_ANSI_KeypadEnter
    (0x4E, 74),  # kVK_ANSI_KeypadMinus
    (0x51, 117),  # kVK_ANSI_KeypadEquals
    (0x52, 82),  # kVK_ANSI_Keypad0
    (0x53, 79),  # kVK_ANSI_Keypad1
    (0x54, 80),  # kVK_ANSI_Keypad2
    (0x55, 81),  # kVK_ANSI_Keypad3
    (0x56, 75),  # kVK_ANSI_Keypad4
    (0x57, 76),  # kVK_ANSI_Keypad5
    (0x58, 77),  # kVK_ANSI_Keypad6
    (0x59, 71),  # kVK_ANSI_Keypad7
    (0x5B, 72),  # kVK_ANSI_Keypad8
    (0x5C, 73),  # kVK_ANSI_Keypad9
    (0x24, 28),  # kVK_Return
    (0x30, 15),  # kVK_Tab
    (0x31, 57),  # kVK_Space
    (0x33, 111),  # kVK_Delete
    (0x35, 1),  # kVK_Escape
    (0x37, 125),  # kVK_Command
    (0x38, 42),  # kVK_Shift
    (0x39, 58),  # kVK_CapsLock
    (0x3A, 56),  # kVK_Option
    (0x3B, 29),  # kVK_Control
    (0x3C, 54),  # kVK_RightShift
    (0x3D, 100),  # kVK_RightOption
    (0x3E, 126),  # kVK_RightControl
    (0x36, 126),  # Right Meta
    (0x3F, 0x1D0),  # kVK_Function
    (0x40, 187),  # kVK_F17
    (0x48, 115),  # kVK_VolumeUp
    (0x49, 114),  # kVK_VolumeDown
    (0x4A, 113),  # kVK_Mute
    (0x4F, 188),  # kVK_F18
    (0x50, 189),  # kVK_F19
    (0x5A, 190),  # kVK_F20
    (0x60, 63),  # kVK_F5
    (0x61, 64),  # kVK_F6
    (0x62, 65),  # kVK_F7
    (0x63, 61),  # kVK_F3
    (0x64, 66),  # kVK_F8
    (0x65, 67),  # kVK_F9
    (0x67, 87),  # kVK_F11
    (0x69, 183),  # kVK_F13
    (0x6A, 186),  # kVK_F16
    (0x6B, 184),  # kVK_F14
    (0x6D, 68),  # kVK_F10
    (0x6F, 88),  # kVK_F12
    (0x71, 185),  # kVK_F15
    (0x72, 138),  # kVK_Help
    (0x73, 102),  # kVK_Home
    (0x74, 104),  # kVK_PageUp
    (0x75, 111),  # kVK_ForwardDelete
    (0x76, 62),  # kVK_F4
    (0x77, 107),  # kVK_End
    (0x78, 60),  # kVK_F2
    (0x79, 109),  # kVK_PageDown
    (0x7A, 59),  # kVK_F1
    (0x7B, 105),  # kVK_LeftArrow
    (0x7C, 106),  # kVK_RightArrow
    (0x7D, 108),  # kVK_DownArrow
    (0x7E, 103),  # kVK_UpArrow
    (0x0A, 170),  # kVK_ISO_Section
    (0x5D, 124),  # kVK_JIS_Yen
    (0x5E, 92),  # kVK_JIS_Underscore
    (0x5F, 95),  # kVK_JIS_KeypadComma
    (0x66, 94),  # kVK_JIS_Eisu
    (0x68, 90),  # kVK_JIS_Kana
)


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
    ("types", EVENT_TYPES),
    ("type_codes", ((value, key) for key, value in EVENT_TYPES)),
    ("wincodes", WINCODES),
    ("specials", SPECIAL_DEVICES),
    ("xpad", XINPUT_MAPPING),
    ("Sync", SYNCHRONIZATION_EVENTS),
    ("Key", KEYS_AND_BUTTONS),
    ("Relative", RELATIVE_AXES),
    ("Absolute", ABSOLUTE_AXES),
    ("Misc", MISC_EVENTS),
    ("Switch", SWITCH_EVENTS),
    ("LED", LEDS),
    ("LED_type_codes", LED_TYPE_CODES),
    ("Sound", SOUNDS),
    ("Repeat", AUTOREPEAT_VALUES),
    ("ForceFeedback", FORCE_FEEDBACK),
    ("Power", POWER),
    ("ForceFeedbackStatus", FORCE_FEEDBACK_STATUS),
    ("Max", MAX),
    ("Current", CURRENT),
)

# Evdev style paths for the Mac

APPKIT_KB_PATH = "/dev/input/by-id/usb-AppKit_Keyboard-event-kbd"
QUARTZ_MOUSE_PATH = "/dev/input/by-id/usb-Quartz_Mouse-event-mouse"
APPKIT_MOUSE_PATH = "/dev/input/by-id/usb-AppKit_Mouse-event-mouse"
