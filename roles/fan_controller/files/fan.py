"""Keep the shared fan at a configured PWM duty cycle until stopped."""

import argparse
import signal


def duty_cycle(value):
    """Accept only finite percentages, including both endpoints."""
    try:
        result = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("duty cycle must be a number") from exc
    if not 0 <= result <= 100:
        raise argparse.ArgumentTypeError("duty cycle must be between 0 and 100")
    return result


def positive_integer(value):
    result = int(value)
    if result <= 0:
        raise argparse.ArgumentTypeError("frequency must be positive")
    return result


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("duty_cycle", type=duty_cycle)
    parser.add_argument("--pin", type=int, choices=range(28), default=13)
    parser.add_argument("--frequency", type=positive_integer, default=50)
    return parser.parse_args(argv)


def stop(_signum, _frame):
    raise SystemExit(0)


def run(args, gpio):
    pwm = None
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    try:
        gpio.setmode(gpio.BCM)
        gpio.setup(args.pin, gpio.OUT)
        pwm = gpio.PWM(args.pin, args.frequency)
        pwm.start(args.duty_cycle)
        print(f"Fan running at {args.duty_cycle:g}% duty cycle on BCM {args.pin}.", flush=True)
        while True:
            signal.pause()
    finally:
        if pwm is not None:
            pwm.stop()
        gpio.cleanup(args.pin)


def main():
    args = parse_args()
    # Parse and validate before touching hardware; --help also works without GPIO.
    import RPi.GPIO as gpio

    run(args, gpio)


if __name__ == "__main__":
    main()
