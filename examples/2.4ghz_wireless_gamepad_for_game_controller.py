"""
This example demonstrates how to control a tracked robot / RC car using this exact controller:
https://www.aliexpress.us/item/3256806561829206.html

The example just assumes a left motor and a right motor.
The controls are simulated in this example with print statements.

Note:
For this exact controller, the right joystick doesn't map properly.
I think it's a controller issue rather than an Inputs issue.
up/down/left/right for the right joystick show as button presses.
The left joystick works more like you'd expect.
"""


from inputs import get_gamepad

while True:
    events = get_gamepad()
    for event in events:
        desired_codes = ["BTN_TRIGGER","BTN_THUMB2","ABS_Y"]
        if event.code not in desired_codes:
            continue

        if event.code == "BTN_TRIGGER":
            if event.state == 0:
                print("right motor: Stop")
            elif event.state == 1:
                print("right motor: forward")
        elif event.code == "BTN_THUMB2":
            if event.state == 0:
                print("right motor: stop")
            elif event.state == 1:
                print("right motor: reverse")
        elif event.code == "ABS_Y":
            if event.state == 128:
                print("left motor: stop")
            elif event.state < 128:
                print("left motor: forward")
            elif event.state > 128:
                print("left motor: reverse")
