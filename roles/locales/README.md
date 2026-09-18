# locales

Generate the UTF-8 locale needed by SSH sessions on Debian-family nodes. Gather
facts and run this role with sudo. `locales_name` defaults to `en_US.UTF-8`.

The role installs `locales`, enables the requested entry in `/etc/locale.gen`, and
runs `locale-gen --keep-existing` when the entry changes or the compiled locale
is missing. It compares against `locale -a`, which reports UTF-8 as `utf8`.
Other generated locales and the system's default language remain unchanged.

Commands use `LC_ALL=C` while bootstrapping so generation does not depend on the
locale being repaired. Reconnect SSH after applying the role. No reboot is needed.

Run just this role on all active nodes with `just setup --tags locales`.
See Debian's [locale-gen documentation](https://manpages.debian.org/bookworm/locales/locale-gen.8.en.html).
