Inputs
======

    .. image:: https://raw.githubusercontent.com/zeth/inputs/master/devices.png

Install
-------

Install through pypi::

    pip install inputs

Or download it from github::

    git clone https://github.com/zeth/inputs.git
    cd inputs
    python setup.py install

About
-----

The inputs module provides an easy way for your Python program to
listen for user input.

Currently supported platforms are the Raspberry Pi, Linux, Windows and
the Apple Mac.

Python versions supported are all versions of Python 3 and your
granddad's Python 2.7.

To get started quickly, just use the following::

    from inputs import devices

For other examples, keep reading.

Inputs is in pure Python and there are no dependencies on Raspberry
Pi, Linux or Windows. On the Mac, inputs needs PyObjC which Apple
installs by default in the system Python. To get PyObjC for your own
user-installed Python go to:

    http://pythonhosted.org/pyobjc/

To get involved, please visit the github project at:

    https://github.com/zeth/inputs


Why Inputs?
-----------

Obviously high level graphical libraries such as PyGame and PyQT will
provide user input support in a very friendly way. However, the inputs
module does not require your program to use any particular graphical
toolkit, or even have a monitor at all.

In the Embedded Linux, Raspberry Pi or Internet of Things type
situation, it is quite common not to have an X-server installed or
running.

This module may also be useful where a computer needs to run a
particular application full screen but you would want to listen out in
the background for a particular set of user inputs, e.g. to bring up
an admin panel in a digital signage setup.

It is still early days. Android should be tested soon and hopefully
also BSD. Optional Asyncio-based event loop support will probably be
included eventually.

This module is a single file, so if you cannot or are not allowed to
use setuptools for some reason, just copy the file inputs.py into your
project.

The inputs module is very simple. The majority of the file is just
constants, so that no matter what platform you are on, input devices
will report the same codes to your program.

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
simply give you the latest events (key press, mouse movement/press or
gamepad activity) from the first connected device in the category, for
example:

>>> from inputs import get_gamepad
>>> while 1:
...     events = get_gamepad()
...     for event in events:
...         print(event.ev_type, event.code, event.state)

>>> from inputs import get_key
>>> while 1:
...     events = get_key()
...     for event in events:
...         print(event.ev_type, event.code, event.state)

>>> from inputs import get_mouse
>>> while 1:
...     events = get_mouse()
...     for event in events:
...         print(event.ev_type, event.code, event.state)

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

On Linux and Raspberry Pi, the guide button (also known as home or
mode or the fancy branded button) is exposed as BTN_MODE.

On Windows, I haven't bothered to support it yet. It is not officially
exposed to applications and using it unofficially requires every user
to turn Game DVR off in the Windows Xbox app settings.

On macOS,

Raspberry Pi Sense HAT
----------------------

The microcontroller on the Raspberry Pi Sense HAT presents the
joystick to the operating system as a keyboard, so find it there under
keyboards. If you worry about this, you are over-thinking things.

Windows permissions
-------------------

By default Windows doesn't stop inputs. However, if you have some
third-party security software you may need to white-list Python. Try
it and find out.

Linux permissions
-----------------

On the Raspberry Pi's Raspbian everything just works.

However, each Linux distribution is different. Some will work straight
away, for some you need to fiddle with permissions.

Linux distributions often (quite rightly) assume that applications are
installed through their package manager and given the relevant
permissions to access the input devices. However, inputs.py is brand
new and not yet packaged by any Linux distribution.

Therefore, if the inputs module works as root (e.g. using sudo) but
not as your normal user, then you usually need to add yourself to an
inputs group or similar.

Mac permissions
---------------

On the Mac, until you write a proper installer for your program, you
will probably have to use the settings application to allow your
program to access the input devices.

    .. image:: https://raw.githubusercontent.com/zeth/inputs/master/macsecurity.png

The first time you use inputs, it will not have any output, then you
will either get the above settings window pop up automatically, or you
will need to find your way there.

Credits
-------

Inputs is by Zeth, all mistakes are mine.

Thanks to Dave Jones for stick.py which is not only the basis for
Sense HAT stick support in this module but more importantly also
taught me an easier way to parse the Evdev event format in Python:

    https://github.com/RPi-Distro/python-sense-hat/blob/master/sense_hat/stick.py

    https://github.com/waveform80/pisense/blob/master/pisense/stick.py

Thanks to Andy (r4dian) and Jason R. Coombs whose existing (MIT
licenced) Python examples for Xbox 360 controller support on Windows
helped me understand xinput greatly. Xbox 360 controller support on
Windows here is based on their work:

    https://github.com/r4dian/Xbox-360-Controller-for-Python

    http://pydoc.net/Python/jaraco.input/1.0.1/jaraco.input.win32.xinput/
