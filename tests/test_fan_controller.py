"""Exercise fan validation and shutdown without Raspberry Pi hardware."""

import contextlib
import importlib.util
import io
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

SCRIPT = Path(__file__).resolve().parents[1] / (
    "roles/fan_controller/files/fan.py"
)
spec = importlib.util.spec_from_file_location("fan", SCRIPT)
fan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fan)


class FanControllerTests(unittest.TestCase):
    def test_percentage_boundaries_and_defaults(self):
        for speed in ("0", "20.5", "100"):
            with self.subTest(speed=speed):
                args = fan.parse_args([speed])
                self.assertEqual(args.duty_cycle, float(speed))
                self.assertEqual((args.pin, args.frequency), (13, 50))

    def test_invalid_arguments_are_rejected(self):
        for args in (["-1"], ["101"], ["nan"], ["inf"], ["abc"],
                     ["20", "--pin", "28"], ["20", "--frequency", "0"]):
            with self.subTest(args=args), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as result:
                    fan.parse_args(args)
                self.assertEqual(result.exception.code, 2)

    def test_shutdown_stops_pwm_and_releases_pin(self):
        gpio = Mock()
        output = io.StringIO()
        args = fan.parse_args(["37.5", "--pin", "18", "--frequency", "100"])
        with patch.object(fan.signal, "signal"), patch.object(
            fan.signal, "pause", side_effect=lambda: fan.stop(15, None)
        ), contextlib.redirect_stdout(output):
            with self.assertRaises(SystemExit) as result:
                fan.run(args, gpio)
        self.assertEqual(result.exception.code, 0)
        gpio.PWM.assert_called_once_with(18, 100)
        gpio.PWM.return_value.start.assert_called_once_with(37.5)
        gpio.PWM.return_value.stop.assert_called_once_with()
        gpio.cleanup.assert_called_once_with(18)
        self.assertIn("37.5%", output.getvalue())

    def test_pwm_failure_releases_gpio(self):
        gpio = Mock()
        gpio.PWM.return_value.start.side_effect = RuntimeError("hardware error")
        with patch.object(fan.signal, "signal"), self.assertRaises(RuntimeError):
            fan.run(fan.parse_args(["100"]), gpio)
        gpio.PWM.return_value.stop.assert_called_once_with()
        gpio.cleanup.assert_called_once_with(13)


if __name__ == "__main__":
    unittest.main()
