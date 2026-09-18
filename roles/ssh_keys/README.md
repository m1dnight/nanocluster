# ssh_keys

Add an OpenSSH public key from inventory to existing accounts on the nodes. Run with
sudo. Requires the `ansible.posix` collection installed by `just deps`.

Set both variables before running:

- `ssh_keys_public_key`: paste the OpenSSH public key text here.
- `ssh_keys_users`: list of existing target usernames on every selected node.

Set these in `inventory/group_vars/all.yml`. It currently contains the public key
for `christophe@bloempot` and targets `pi` on every active node. The role's own
defaults are empty, so an unconfigured run stops before changing accounts.
The role checks that the selected accounts exist and uses their actual home
directories. It manages `.ssh`/`authorized_keys` permissions and adds the key
without removing other keys. Repeated runs do not add duplicate entries.

The private key stays on your computer. The role does not create users, change
passwords, or disable password authentication. Bootstrap it using a working SSH
key or `--ask-pass`, and add `--ask-become-pass` if sudo needs a password.

This role is run separately with `just ssh_keys` and is not part of `just setup`.
It uses [ansible.posix.authorized_key](https://docs.ansible.com/projects/ansible/latest/collections/ansible/posix/authorized_key_module.html).
