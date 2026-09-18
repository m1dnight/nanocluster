# asdf

Build asdf and configure language runtimes for the connecting user. Gather facts
as that user and run the role without global privilege escalation. Its Go role
dependency and legacy system profile removal use sudo explicitly.

Prerequisites: Git, make, a compiler, and plugin-specific build/download packages.
`setup.yml` installs these and supplies the pinned Linux ARM64 Go version
and checksum to the `geerlingguy.go` dependency. Go lives at `/usr/local/go`.

| Variable | Default | Purpose |
| --- | --- | --- |
| `asdf_version` | `v0.18.0` | Git tag or commit to build. |
| `asdf_directory` | `~/.asdf` for the connecting user | Source, plugins, shims, and installed runtimes. Must be a subdirectory of that user's home. |
| `asdf_plugins` | `[]` | Ordered list of `{name, version, repository?}` dictionaries. |
| `asdf_cleanup` | `false` | Explicitly delete the entire installation, including all runtimes, before rebuilding. |

Supported version selections are an exact release or `latest`. Place Erlang
before Elixir so Erlang's shims/default version are available during Elixir setup.
Pin exact releases to keep all nodes reproducible across separate runs.

The role rebuilds when the checkout changes or the executable is missing. Existing
plugins and runtime directories are reused. Each `latest` is resolved once per
host/run for both installation and selection. Only the selected plugin's entry in
`~/.tool-versions` is changed; other tools remain intact.

The role manages blocks in `.profile` and `.bashrc` with `ASDF_DATA_DIR` and shims
first on PATH, and removes its old `/etc/profile.d/asdf-path.sh`. Other shell types
need equivalent setup. Plugin/runtime commands are skipped during check mode.

Version-selection behavior follows the [asdf documentation](https://asdf-vm.com/manage/versions.html).
