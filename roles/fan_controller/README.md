# fan_controller

Install a fixed-duty-cycle fan service on the Pi with physical controller access.
Gather facts and use sudo. Requires systemd and a Debian-family OS providing a
compatible implementation of the RPi.GPIO API. Confirm the GPIO backend supports
your Pi model; the default `python3-rpi.gpio` package is not a universal Pi 5 backend.

| Variable | Default | Purpose |
| --- | --- | --- |
| `fan_controller_path` | `/opt` | Script directory. |
| `fan_controller_script_name` | `fan.py` | Script filename. |
| `fan_controller_speed` | `100.0` | PWM duty cycle, 0–100 percent. |
| `fan_controller_gpio_pin` | `13` | BCM GPIO number. |
| `fan_controller_pwm_frequency` | `50` | PWM frequency in Hz. |
| `fan_controller_packages` | `[python3, python3-rpi.gpio]` | Runtime and GPIO dependency packages. |

The role installs the dependencies, validates settings, and enables
`fan-control.service`. Script or unit changes trigger a systemd reload and service
restart. The script logs the actual configured percentage and releases GPIO on
SIGINT, SIGTERM, or an exception. Systemd retries failures after five seconds.

The controller maintains a fixed speed; it does not read temperatures. Pin and
frequency defaults preserve the original wiring assumptions. Zero duty cycle
stops PWM drive. Check actual cooling on the hardware after changing settings.
