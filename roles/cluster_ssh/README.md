# cluster_ssh

Let the nodes log in to each other as `pi` without passwords or prompts, so that
roles such as `mirror` can run rsync directly between nodes. Part of `just setup`;
run it alone with `just setup --tags cluster_ssh`.

On every node in the play the role:

1. Generates `~/.ssh/id_ed25519` without a passphrase when no such key exists.
   An existing key is kept as is.
2. Adds the public key of every node in the play to `~/.ssh/authorized_keys`.
   Other entries, such as your own key from the `ssh_keys` role, are preserved.
3. Pins every node's ed25519 host key in `~/.ssh/known_hosts` under its
   inventory address (`ansible_host`, e.g. `nc2.localdomain`), so the first
   connection needs no confirmation. The nodes must resolve those names.

The keys and host keys are read from the nodes during the play through
`hostvars`, so only nodes in the play trust each other. With `--limit`, the
limited nodes exchange keys among themselves only. Re-run the full play after
adding a node. Removing a node's access means deleting its line from the other
nodes' `authorized_keys`; this role does not revoke keys.

Every node can then reach every other one as `pi`; treat the cluster as one
trust domain.
