# m1dnight.nanocluster

Local roles used by the nanocluster playbooks. Requires ansible-core >=2.17.

- `packages`: shared Debian package installation and optional maintenance.
- `asdf`: build asdf and manage per-user language plugins and versions.
- `fan_controller`: run the shared fan's PWM service on the attached Pi.

The repository's `setup.yml` configures every active node, while `fan_speed.yml`
configures the shared fan on Pi 1. Run them with `just setup` and `just fan_speed`.

Each role has a README and argument specification. See the repository README for
inventory, dependencies, execution order, and local validation commands.
