"""Exercise folder mirroring between temporary directories without connecting to Pis."""

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
class SyncTests(unittest.TestCase):
    def test_mirror_delete_excludes_repeat_and_guards(self):
        with tempfile.TemporaryDirectory(prefix="nanocluster-sync-test-") as tmp:
            directory = Path(tmp)
            source = directory / "source"
            (source / "sub").mkdir(parents=True)
            (source / "a.txt").write_text("a\n")
            (source / ".hidden").write_text("h\n")
            (source / "sub" / "b.txt").write_text("b\n")
            destinations = [directory / name / "sync" for name in ("node1", "node2")]
            for destination in destinations:
                (destination / "keep").mkdir(parents=True)
                (destination / "stale.txt").write_text("old\n")
                (destination / "keep" / "k.txt").write_text("k\n")
            inventory = directory / "hosts.yml"
            inventory.write_text(yaml.safe_dump({"all": {"hosts": {
                destination.parent.name: {"sync_destination": str(destination)}
                for destination in destinations
            }}}))
            playbook = directory / "test.yml"
            playbook.write_text(yaml.safe_dump([{
                "name": "Exercise folder mirroring into temporary directories",
                "hosts": "all",
                "gather_facts": False,
                "connection": "local",
                "vars": {"ansible_python_interpreter": sys.executable},
                "roles": [str(ROOT / "roles/sync")],
            }]))
            env = dict(os.environ, ANSIBLE_LOCAL_TEMP=str(directory / "ansible-tmp"),
                       ANSIBLE_REMOTE_TEMP=str(directory / "remote-tmp"),
                       ANSIBLE_NOCOLOR="1", ANSIBLE_VERBOSITY="0")

            def execute(variables, success=True):
                result = subprocess.run(
                    ["ansible-playbook", "-i", str(inventory), str(playbook),
                     "-e", yaml.safe_dump(variables, default_flow_style=True)],
                    cwd=ROOT, env=env, text=True, capture_output=True, timeout=120,
                )
                output = result.stdout + result.stderr
                self.assertEqual(result.returncode == 0, success, output)
                return output

            def listing(destination):
                return sorted(str(path.relative_to(destination))
                              for path in destination.rglob("*") if path.is_file())

            # Excluded paths survive; everything else mirrors the source.
            execute({"sync_source": str(source), "sync_excludes": ["keep"]})
            for destination in destinations:
                self.assertEqual(listing(destination), [".hidden", "a.txt", "keep/k.txt", "sub/b.txt"])

            # Without excludes the stale directory is deleted, and the repeat run changes nothing.
            execute({"sync_source": str(source)})
            for destination in destinations:
                self.assertEqual(listing(destination), [".hidden", "a.txt", "sub/b.txt"])
            self.assertEqual(execute({"sync_source": str(source)}).count("changed=0"), 2)

            # Guards: empty source, missing source, and dangerous destinations stop before any change.
            empty = directory / "empty"
            empty.mkdir()
            execute({"sync_source": str(empty)}, success=False)
            execute({"sync_source": str(directory / "missing")}, success=False)
            for bad in ("/", "/home", "/home/pi", "relative/path"):
                execute({"sync_source": str(source), "sync_destination": bad}, success=False)
            for destination in destinations:
                self.assertEqual(listing(destination), [".hidden", "a.txt", "sub/b.txt"])

            # Explicitly allowing an empty source clears the copies.
            execute({"sync_source": str(empty), "sync_allow_empty_source": True})
            for destination in destinations:
                self.assertEqual(listing(destination), [])


if __name__ == "__main__":
    unittest.main()
