# sync

Mirror one folder from this computer to the same directory on every node using
rsync. Files present on a node but missing from the source are deleted, so the
node's copy always matches the local folder. Requires the `ansible.posix`
collection and rsync on both sides (macOS ships a compatible openrsync; the
Pis have rsync from the common package list).

Variables:

- `sync_source`: local folder to mirror. `~` is expanded. Its contents, including
  hidden files, are copied; the folder itself is not nested in the destination.
- `sync_destination`: absolute path on each node, for example `/home/pi/sync`.
  Created when missing. Ownership follows the connecting user.
- `sync_delete` (default `true`): delete destination files absent from the source.
- `sync_excludes` (default `[]`): rsync patterns that are neither copied nor deleted.
- `sync_allow_empty_source` (default `false`): permit an empty source, which
  clears every node's copy.
- `sync_rsync_opts` (default `[]`): extra rsync options such as `--dry-run`.

Safety checks run before any file is touched: the source must be an existing
non-empty directory on the controller, and the destination may not be `/`,
a top-level directory such as `/home`, or a home directory such as `/home/pi`.
Permissions and timestamps are preserved (`--archive`). Repeat runs report no
change when nothing differs.

Run with `just sync`; the role is not part of `just setup`. It uses
[ansible.posix.synchronize](https://docs.ansible.com/projects/ansible/latest/collections/ansible/posix/synchronize_module.html)
without sudo, so the destination must be writable by the SSH user.
