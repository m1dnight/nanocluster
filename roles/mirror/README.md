# mirror

Mirror a directory from one node (the source host) to every other node with
rsync, deleting files on the other nodes that the source host no longer has.
Unlike the `sync` role, the data never passes through this computer: rsync runs
on the source host and pushes directly to each node over SSH.

SSH access between the nodes comes from the `cluster_ssh` role in `just setup`,
which gives `pi` on every node a key that every other node accepts. Run that first;
otherwise rsync fails with "Permission denied". Nodes are reached by their
inventory address (`ansible_host`, overridable through `mirror_address`).

Variables:

- `mirror_source_host`: inventory hostname of the node with the master copy.
- `mirror_source_path`: absolute directory on that node. Its contents, including
  hidden files, are mirrored.
- `mirror_destination` (default: same path): absolute directory on the other nodes.
- `mirror_delete` (default `true`), `mirror_excludes`, `mirror_allow_empty_source`,
  `mirror_rsync_opts`: as in the `sync` role.

Safety checks run before any transfer: the source must be an existing non-empty
directory on the source host, and the destination may not be `/`, a top-level
directory, or a home directory. Check mode creates directories but
skips the transfer; pass `--dry-run` through `mirror_rsync_opts` to preview it.
Repeat runs report no change when nothing differs. Requires rsync on every node
and the `ansible.posix` collection.
