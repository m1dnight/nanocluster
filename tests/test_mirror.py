"""Exercise node-to-node mirroring between temporary directories without SSH or Pis."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("ansible-playbook") and shutil.which("rsync"),
                     "ansible-playbook and rsync are required")
class MirrorTests(unittest.TestCase):
    def test_mirror_delete_excludes_repeat_and_guards(self):
        with tempfile.TemporaryDirectory(prefix="nanocluster-mirror-test-") as tmp:
            directory = Path(tmp)
            source = directory / "source"
            (source / "sub").mkdir(parents=True)
            (source / "a.txt").write_text("a\n")
            (source / ".hidden").write_text("h\n")
            (source / "sub" / "b.txt").write_text("b\n")
            destinations = [directory / name / "shared" for name in ("node1", "node2")]
            for destination in destinations:
                (destination / "keep").mkdir(parents=True)
                (destination / "stale.txt").write_text("old\n")
                (destination / "keep" / "k.txt").write_text("k\n")
            inventory = directory / "hosts.yml"
            hosts = {"src": {}}
            hosts.update({destination.parent.name: {"mirror_destination": str(destination)}
                          for destination in destinations})
            inventory.write_text(yaml.safe_dump({"all": {"hosts": hosts}}))
            playbook = directory / "test.yml"
            playbook.write_text(yaml.safe_dump([{
                "name": "Exercise mirroring into temporary directories",
                "hosts": "all",
                "gather_facts": False,
                "connection": "local",
                "vars": {"ansible_python_interpreter": sys.executable, "mirror_ssh": False},
                "roles": [str(ROOT / "roles/mirror")],
            }]))
            env = dict(os.environ, ANSIBLE_LOCAL_TEMP=str(directory / "ansible-tmp"),
                       ANSIBLE_REMOTE_TEMP=str(directory / "remote-tmp"),
                       ANSIBLE_NOCOLOR="1", ANSIBLE_VERBOSITY="0")
            base = {"mirror_source_host": "src", "mirror_source_path": str(source)}

            def execute(variables, success=True):
                result = subprocess.run(
                    ["ansible-playbook", "-i", str(inventory), str(playbook),
                     "-e", yaml.safe_dump({**base, **variables}, default_flow_style=True)],
                    cwd=ROOT, env=env, text=True, capture_output=True, timeout=120,
                )
                output = result.stdout + result.stderr
                self.assertEqual(result.returncode == 0, success, output)
                return output

            def listing(destination):
                return sorted(str(path.relative_to(destination))
                              for path in destination.rglob("*") if path.is_file())

            # Excluded paths survive; everything else mirrors the source host.
            execute({"mirror_excludes": ["keep"]})
            for destination in destinations:
                self.assertEqual(listing(destination), [".hidden", "a.txt", "keep/k.txt", "sub/b.txt"])

            # Without excludes the stale directory is deleted; the repeat run changes nothing anywhere.
            execute({})
            for destination in destinations:
                self.assertEqual(listing(destination), [".hidden", "a.txt", "sub/b.txt"])
            self.assertEqual(execute({}).count("changed=0"), 3)
            self.assertEqual(listing(source), [".hidden", "a.txt", "sub/b.txt"])

            # A preview changes nothing.
            (source / "c.txt").write_text("c\n")
            execute({"mirror_rsync_opts": ["--dry-run"]})
            for destination in destinations:
                self.assertEqual(listing(destination), [".hidden", "a.txt", "sub/b.txt"])
            (source / "c.txt").unlink()

            # Guards stop before any change.
            empty = directory / "empty"
            empty.mkdir()
            execute({"mirror_source_path": str(empty)}, success=False)
            execute({"mirror_source_path": str(directory / "missing")}, success=False)
            execute({"mirror_source_host": "nowhere"}, success=False)
            execute({"mirror_source_path": "relative/path"}, success=False)
            for bad in ("/", "/home", "/home/pi"):
                execute({"mirror_destination": bad}, success=False)
            for destination in destinations:
                self.assertEqual(listing(destination), [".hidden", "a.txt", "sub/b.txt"])

            # Explicitly allowing an empty source clears the other nodes.
            execute({"mirror_source_path": str(empty), "mirror_allow_empty_source": True})
            for destination in destinations:
                self.assertEqual(listing(destination), [])


if __name__ == "__main__":
    unittest.main()
