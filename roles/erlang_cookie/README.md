# erlang_cookie

Write the shared `erlang_cookie_value` to an existing user's `~/.erlang.cookie`.
Set the value once in shared inventory or an extra-vars file so every node uses
the same cookie. The role does not generate or rotate it automatically.

`erlang_cookie_user` defaults to `ansible_user` (falling back to `pi`). The role
looks up that account's home and primary group, then writes the file with account
ownership and mode `0400`. Run with sudo when managing another account's home.

The value must contain 1–255 printable ASCII characters without whitespace.
Cookie validation and writing suppress task output; file diffs are disabled.
Changing the value replaces the file. Restart running Erlang/Elixir nodes to
load the new cookie; this role does not restart applications.

Run separately with `just erlang_cookie`; this role is not included in
`just setup`.
