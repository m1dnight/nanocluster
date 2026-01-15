import RPi.GPIO as GPIO
import signal
import sys

# Get duty cycle from command line argument
if len(sys.argv) != 2:
    print("Usage: fan_control.py <duty_cycle>")
    sys.exit(1)

try:
    duty_cycle = float(sys.argv[1])
    if not 0 <= duty_cycle <= 100:
        print("Error: duty_cycle must be between 0 and 100")
        sys.exit(1)
except ValueError:
    print("Error: duty_cycle must be a number")
    sys.exit(1)

GPIO.setmode(GPIO.BCM)
GPIO.setup(13, GPIO.OUT)
pwm = GPIO.PWM(13, 50)
pwm.start(duty_cycle)

def cleanup(sig, frame):
    pwm.stop()
    GPIO.cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

print("Fan running at 20% duty cycle. Press Ctrl+C to stop.")
signal.pause()  # Keep running forever