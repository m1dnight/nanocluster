# packages

Manage packages on Debian-family hosts. Gather facts and run this role with sudo.

| Variable | Default | Purpose |
| --- | --- | --- |
| `packages_add_list` | `[]` | Packages to ensure are installed. |
| `packages_remove_list` | `[]` | Packages to remove; must not overlap the install list. |
| `packages_cache_valid_time` | `3600` | Apt cache lifetime in seconds. |
| `packages_upgrade` | `false` | Opt in to `apt-get dist-upgrade`. |
| `packages_autoremove` | `false` | Opt in to purging unused dependencies after other operations. |

Install/remove operations use whole lists rather than one apt invocation per
package. Ordinary provisioning is repeatable; explicit maintenance follows the
current repositories and can change packages on later runs. No automatic reboot
is performed.
