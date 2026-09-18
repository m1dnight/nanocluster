# erlang_setup

Prepare an existing account on every node for Erlang distribution by writing two
files in its home directory:

- `.erlang.cookie`: the shared `erlang_setup_cookie`, mode `0400`. Set the value
  once in shared inventory or a vault file so every node uses the same cookie.
  The value must contain 1–255 printable ASCII characters without whitespace.
  Cookie tasks suppress output and diffs.
- `.hosts.erlang`: one quoted host name per line, which `net_adm:world/0` and
  `net_adm:names/1` use to find nodes. By default it lists every member of the
  `erlang_setup_hosts_group` inventory group (`nodes`) by its `ansible_host`,
  e.g. `'nc1.localdomain'.`. Set `erlang_setup_hosts` to list names explicitly.

`erlang_setup_user` defaults to `ansible_user` (falling back to `pi`). The role
looks up the account's home and primary group and writes the files with account
ownership. Run with sudo when managing another account's home.

Changing the cookie replaces the file, but running Erlang/Elixir nodes keep
their old cookie until restarted; this role does not restart applications.
Start nodes with names matching the hosts file, for example
`iex --name app@nc1.localdomain`, so that `Node.connect/1` and
`:net_adm.world/0` work.

Run separately with `just erlang_setup`; this role is not included in `just setup`.
