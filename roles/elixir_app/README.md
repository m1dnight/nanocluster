# elixir_app

Run an Elixir release that is already unpacked on the node as a systemd service.
The role does not build or copy the release; it expects `bin/<launcher>` and
`releases/start_erl.data` under `elixir_app_release_path`, which is normally a
symlink such as `/opt/myapp/current` pointing at the active version. Run with sudo.

Required:

- `elixir_app_name`: service name, e.g. `myapp`. The unit becomes `myapp.service`.
- `elixir_app_release_path`: absolute release directory on the node.

Common options:

- `elixir_app_environment`: dict of environment variables written to
  `/etc/<name>/env` (mode `0640`, readable by the service account's group).
  Values are double-quoted for systemd; task output hides them.
- `elixir_app_user`: existing account that runs the service; defaults to the SSH
  user. It must be able to read the release directory.
- `elixir_app_release_name`: launcher name under `bin/` when it differs from the service name.
- `elixir_app_state` / `elixir_app_enabled`: desired state after the run.

Generated environment defaults, each overridable through `elixir_app_environment`:

| Variable | Default |
| --- | --- |
| `LANG` | `C.UTF-8` |
| `RELEASE_DISTRIBUTION` | `name` |
| `RELEASE_NODE` | `<name>@<hostname>.localdomain` |
| `RELEASE_COOKIE` | `erlang_cookie_value` when defined |
| `RELEASE_TMP` | `/var/lib/<name>/tmp` |

The service runs `bin/<launcher> start` in the foreground under systemd with
`Restart=on-failure`, and stops with `bin/<launcher> stop`. The role restarts the
service when the unit, the environment file, or the deployed release changes.
The release is detected through the resolved launcher path and the version in
`releases/start_erl.data`, so repointing the symlink or unpacking a new version
and re-running the play performs the restart.

Repeated runs report no change. `elixir_app_manage_service: false` renders the
files without touching systemd, which the tests use.
