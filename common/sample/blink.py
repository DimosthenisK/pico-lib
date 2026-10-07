from onboard_led import OnboardLED

led = OnboardLED()
print("blinking")

while True:
    led.blink(0.5)
