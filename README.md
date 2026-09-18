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

Install the Go role and SSH-key collection dependencies on the controller:

```sh
just deps
```

SSH credentials come from your SSH configuration/agent. Use `--private-key`
for an explicit key and `--ask-become-pass` if sudo requires a password.
No private key path is committed here.

## Repository layout

```text
ansible.cfg
justfile
requirements.yml
pb_setup.yml
pb_fan_speed.yml
pb_ssh_keys.yml
pb_erlang_cookie.yml
pb_sync.yml
pb_mirror.yml
pb_elixir_app.yml
inventory/
  hosts.yml
  group_vars/
    all.yml
    nodes.yml
    fan_controller.yml
roles/
  locales/
  packages/
  asdf/
  cluster_ssh/
  fan_controller/
  ssh_keys/
  erlang_cookie/
  sync/
  mirror/
  elixir_app/
tests/
.github/workflows/
```

Playbooks select hosts and roles. Local roles contain the implementation and
defaults; inventory group variables hold the cluster's package lists, toolchain
versions, and fan settings. Ansible discovers `roles/` beside the playbooks.
`requirements.yml` pins the external Go role and `ansible.posix` collection
installed by `just deps`.

## Playbooks

| Command | Playbook | Hosts | Behavior |
| --- | --- | --- | --- |
| `just setup` | `pb_setup.yml` | Pis 1–6 | Generates the SSH locale, installs common packages, Go 1.25.5, asdf v0.18.0, Erlang, and Elixir, and lets the nodes SSH to each other. |
| `just fan_speed` | `pb_fan_speed.yml` | Pi 1 | Installs the GPIO dependency and starts/enables the shared fan service at the configured speed. |
| `just ssh_keys` | `pb_ssh_keys.yml` | Pis 1–6 | Adds a configured public SSH key to selected existing accounts. |
| `just erlang_cookie` | `pb_erlang_cookie.yml` | Pis 1–6 | Writes the same Erlang cookie to the selected account's home. |
| `just sync` | `pb_sync.yml` | Pis 1–6 | Mirrors a local folder to every node, deleting node files that are absent locally. |
| `just mirror` | `pb_mirror.yml` | Pis 1–6 | Mirrors a directory from one node to all other nodes, deleting files absent on the source node. |
| `just elixir_app` | `pb_elixir_app.yml` | Pis 1–6, one at a time | Runs an already unpacked Elixir release as a systemd service. |

`just` lists available commands. All playbook recipes accept additional Ansible arguments,
including quoted values with spaces:

```sh
just setup --limit nanocluster2
just setup --check --diff
just fan_speed -e fan_controller_speed=50
```

On first provisioning, run `just fan_speed` before `just setup` so cooling is
active during language compilation. Setup itself does not configure the fan.
Without `just`, run `ansible-playbook pb_setup.yml` or `ansible-playbook pb_fan_speed.yml`.

### Common packages and runtimes

`inventory/group_vars/nodes.yml` defines the package and language lists. Packages
include Git, rsync, just, tmux, Emacs, NFS client utilities, disk/network tools, and the build,
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

### SSH between nodes

Setup ends with the `cluster_ssh` role: every node gets a passphrase-less
`~/.ssh/id_ed25519` for `pi` if it has none, every node's public key is added to
every node's `authorized_keys`, and every node's host key is pinned in
`known_hosts` under its inventory address (`nc2.localdomain` and so on), which
the nodes resolve through the router's DNS. Afterwards `ssh nc2.localdomain`
works from any node without prompts, which `just mirror` relies on. Only nodes in the play
exchange keys, so re-run setup after adding a node. Run this step alone with:

```sh
just setup --tags cluster_ssh
```

### Shared fan

The default is a fixed **100% PWM duty cycle**, BCM GPIO **13**, at **50 Hz**.
This is not temperature-based control. The service starts at boot and restarts
when the script or its configuration changes. Its process releases GPIO on stop.

```sh
just fan_speed -e fan_controller_speed=50
```

For a persistent setting, edit `inventory/group_vars/fan_controller.yml` and set
`fan_controller_speed: 50`. Pin, frequency, and dependency packages are configurable
as well; see the fan role README. Extra vars apply only to that invocation.

## Shared Erlang cookie

Set `erlang_cookie_value` in `inventory/group_vars/all.yml`, then run:

```sh
just erlang_cookie
```

This writes the same value to `/home/pi/.erlang.cookie` on all active nodes,
owned by `pi` with mode `0400` (owner read only). Task output and diffs hide the
cookie. Repeated runs reuse the configured value; changing it replaces the file.
This is a separate playbook; run it after setup.

`erlang_cookie_user` defaults to the SSH user (`pi`) and can target another
existing account. To keep the cookie out of tracked inventory, remove its inline
value and supply `erlang_cookie_value` through an Ansible Vault vars file:
`just erlang_cookie -e @cookie.vault --ask-vault-pass`.

Restart any running Erlang/Elixir nodes after changing their cookie; the role
only writes the file. See [Erlang's authentication documentation](https://www.erlang.org/doc/system/distributed.html#security).

## Shared folder

`just sync` mirrors `~/nanocluster-sync` on this computer to `/home/pi/sync` on
every active node with rsync. Anything under the destination that does not exist
locally is **deleted**, so each node's copy always matches the local folder.
Hidden files are included; `.DS_Store` files are excluded by default and left alone.

Both paths and the exclude list live in `inventory/group_vars/nodes.yml`
(`sync_source`, `sync_destination`, `sync_excludes`). Preview a run first:

```sh
just sync -e '{"sync_rsync_opts": ["--dry-run"]}'
```

The role refuses to run when the local folder is missing or empty, or when the
destination is `/`, a top-level directory, or a home directory. To intentionally
clear the nodes' copies, empty the local folder and pass
`-e sync_allow_empty_source=true`. macOS's built-in rsync is sufficient; the
nodes get rsync from the common package list. See the sync role README.

## Mirror between nodes

`just mirror` copies a directory from one node to all other nodes without going
through this computer: rsync runs on the source node and pushes to each peer.
Files on the other nodes that the source node no longer has are **deleted**.
The defaults in `inventory/group_vars/nodes.yml` mirror `/home/pi/shared` from
`nanocluster1` to the same path elsewhere (`mirror_source_host`,
`mirror_source_path`, optional `mirror_destination`, `mirror_excludes`).

SSH access between nodes comes from `just setup` (see "SSH between nodes"),
so run setup first. The same guards as `just sync` apply, and a preview works the
same way:

```sh
just mirror -e '{"mirror_rsync_opts": ["--dry-run"]}'
```

## Elixir release as a service

`just elixir_app` installs a systemd unit for an Elixir release that is already
unpacked on each node, for example after `mix release` and copying the tarball
with `just sync`. Set at least the service name and the release directory in
`inventory/group_vars/nodes.yml`; a commented example is included there:

```yaml
elixir_app_name: myapp
elixir_app_release_path: /opt/myapp/current
elixir_app_environment:
  PHX_SERVER: "true"
  PORT: "4000"
```

The role writes `/etc/myapp/env` with those variables plus generated defaults
for clustering: `RELEASE_DISTRIBUTION=name`, `RELEASE_NODE=myapp@<hostname>.localdomain`,
`RELEASE_COOKIE` from `erlang_cookie_value`, `RELEASE_TMP` under `/var/lib/myapp`,
and a UTF-8 `LANG`. Any of them can be overridden by key. The service runs as the
SSH user by default (`elixir_app_user`) and must be able to read the release.

The play runs one node at a time so a clustered application keeps serving during
restarts; pass `-e elixir_app_serial=6` to change that. A run restarts the
service only when the unit, the environment, or the deployed release changed.
Repoint the `current` symlink to a new version and re-run the play to roll it
out. See the elixir_app role README for all options.

## SSH key access

Paste your public key into `ssh_keys_public_key` in
`inventory/group_vars/all.yml`. The supplied `christophe@bloempot` key is already
configured there, with `ssh_keys_users: [pi]` targeting `pi` on all six nodes.
Add other existing usernames to that list if needed. Apply it with:

```sh
just deps
just ssh_keys
```

Use an existing working SSH key or append `--ask-pass` to bootstrap with password
authentication. Append `--ask-become-pass` if sudo requires a password. The role
preserves other keys and password login, and does not create accounts. The private
key stays on your computer. An unconfigured run stops with instructions.

After provisioning, test a new connection with the matching private key:

```sh
ssh -i ~/.ssh/id_rsa pi@nc1.localdomain
```

Use your actual key path in place of the example. Add a custom private key to your
SSH agent or select it in your SSH configuration for VS Code terminals and Ansible.

## SSH terminals in VS Code

Open the repository folder in VS Code, then use **Tasks: Run Task** in the Command
Palette and select **SSH: all nodes**. This opens six separate terminal sessions,
connecting as `pi` to `nc1.localdomain` through `nc6.localdomain` in parallel.
Select **SSH: nanocluster1** (or another node) to open just one session.

The tasks use your usual SSH configuration and agent. Each node has a dedicated
terminal; type `exit` to disconnect. Pi 7 is excluded while unplugged. If inventory
addresses or the SSH user change, update `.vscode/tasks.json` to match.

### SSH login warnings

If SSH prints `cannot change locale (en_US.UTF-8)`, generate the missing locale on
all active nodes, then reconnect:

```sh
just setup --tags locales
```

To repair only Pi 1, add `--limit nanocluster1`. Normal setup includes this role.
Other installed locales and the system's default language are preserved.

The default-password warning is separate. While logged in as `pi`, run `passwd`
on each node and follow the prompts to choose a new password. Passwords are not
managed by these playbooks.

## Local validation

These checks do not connect to the Pis:

```sh
ansible-inventory --graph
just setup --syntax-check
just fan_speed --syntax-check
just ssh_keys --syntax-check
just erlang_cookie --syntax-check
just sync --syntax-check
just mirror --syntax-check
just elixir_app --syntax-check
just setup --list-hosts
just fan_speed --list-hosts
ansible-lint --offline
python3 -m unittest discover -s tests -v
```

The tests use simulated GPIO, a fake asdf executable, and temporary user homes.
They cover fan argument validation and cleanup, and actual Ansible plugin tasks
for installation, repeat runs, version changes, and preserving unrelated tools.
Cookie tests cover shared values, ownership and permissions, repeat runs,
rotation, invalid values, and hidden output even with `--diff`.
Sync tests mirror temporary directories and cover deletion, excludes, repeat
runs, and the guards against empty or missing sources and unsafe destinations.
Mirror tests do the same for node-to-node copies without SSH, and cluster SSH
tests exchange generated keys between temporary directories.
Elixir app tests render the unit and environment files for a fake release and
cover defaults, overrides, quoting, repeat runs, version changes, and validation.
They do not validate physical wiring or OS package availability on the Pis.
