# Nanocluster provisioning

Six active Raspberry Pis share the same Linux and development-tool baseline.
Pi 1 additionally controls the shared fan. Pi 7 is unplugged and commented out
in the inventory. The only groups are `nodes` and `fan_controller`.

## Requirements

- A controller with ansible-core 2.17 or newer, `just`, and SSH access to the nodes.
- Linux ARM64 nodes with a Debian-family OS, Python 3, and sudo access for `pi`.
- DNS or SSH configuration resolving `nc1.localdomain` through `nc6.localdomain`.
- Internet access for apt packages, Go, and asdf/plugins/runtimes.
- Fan hardware compatible with the RPi.GPIO API on Pi 1. The default package is
  `python3-rpi.gpio`; confirm compatibility with your Pi model and OS image.

Install the Go role dependency on the controller:

```sh
just deps
```

SSH credentials come from your SSH configuration/agent. Use `--private-key`
for an explicit key and `--ask-become-pass` if sudo requires a password.
No private key path is committed here.

## Playbooks

| Command | Playbook | Hosts | Behavior |
| --- | --- | --- | --- |
| `just setup` | `setup.yml` | Pis 1–6 | Installs common packages, Go 1.25.5, asdf v0.18.0, Erlang, and Elixir. |
| `just fan_speed` | `fan_speed.yml` | Pi 1 | Installs the GPIO dependency and starts/enables the shared fan service at the configured speed. |

`just` lists available commands. Both recipes accept additional Ansible arguments,
including quoted values with spaces:

```sh
just setup --limit nanocluster2
just setup --check --diff
just fan_speed -e fan_controller_speed=50
```

On first provisioning, run `just fan_speed` before `just setup` so cooling is
active during language compilation. Setup itself does not configure the fan.
Without `just`, run `ansible-playbook setup.yml` or `ansible-playbook fan_speed.yml`.

### Common packages and runtimes

`inventory/group_vars/nodes.yml` defines the package and language lists. Packages
include Git, tmux, Emacs, NFS client utilities, disk/network tools, and the build,
SSL, wxWidgets, and documentation libraries used to compile Erlang.

The Go dependency runs with sudo and installs into `/usr/local/go`. asdf and its
plugins/runtimes belong to the connecting user, normally `/home/pi/.asdf`.
The role configures `.profile` and `.bashrc`, puts shims first on PATH, and updates
only managed entries in `~/.tool-versions`. Reopen the shell after provisioning.

Erlang and Elixir currently use `latest`. The role resolves each requested latest
version once per host/run, installs it only when absent, and selects that exact
version. New upstream releases can therefore change the installed versions on
later runs. Replace `latest` with exact releases for reproducible provisioning.
Existing unused versions are retained. The asdf plugin/version tasks are skipped
in check mode because the executable and plugins may not yet exist.

Normal provisioning does not upgrade every OS package or purge unused packages.
To upgrade OS packages on every active node, run:

```sh
just setup \
  -e '{"packages_upgrade": true, "packages_autoremove": true}'
```

Add `--limit nanocluster2` to maintain one node at a time. OS package maintenance
does not automatically reboot for kernel upgrades.

### Shared fan

The default is a fixed **100% PWM duty cycle**, BCM GPIO **13**, at **50 Hz**.
This is not temperature-based control. The service starts at boot and restarts
when the script or its configuration changes. Its process releases GPIO on stop.

```sh
just fan_speed -e fan_controller_speed=50
```

For a persistent setting, create `inventory/group_vars/fan_controller.yml` with
`fan_controller_speed: 50`. Pin, frequency, and dependency packages are configurable
as well; see the fan role README. Extra vars apply only to that invocation.

## Local validation

These checks do not connect to the Pis:

```sh
ansible-inventory --graph
just setup --syntax-check
just fan_speed --syntax-check
just setup --list-hosts
just fan_speed --list-hosts
ansible-lint --offline
python3 -m unittest discover -s tests -v
```

The tests use simulated GPIO and a fake asdf executable in a temporary directory.
They cover fan argument validation and cleanup, and actual Ansible plugin tasks
for installation, repeat runs, version changes, and preserving unrelated tools.
They do not validate physical wiring or OS package availability on the Pis.
