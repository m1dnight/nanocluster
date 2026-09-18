"""Exchange generated SSH keys between temporary directories without connecting to Pis."""

import os
from pathlib import Path
import pwd
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("ansible-playbook") and shutil.which("ssh-keygen"),
                     "ansible-playbook and ssh-keygen are required")
class ClusterSshTests(unittest.TestCase):
    def test_keys_are_generated_once_and_exchanged(self):
        with tempfile.TemporaryDirectory(prefix="nanocluster-cluster-ssh-test-") as tmp:
            directory = Path(tmp)
            account = pwd.getpwuid(os.getuid())
            names = ("node1", "node2", "node3")
            hosts = {}
            for name in names:
                ssh_dir = directory / name / ".ssh"
                ssh_dir.mkdir(parents=True)
                host_key = directory / name / "ssh_host_ed25519_key"
                subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(host_key)], check=True)
                hosts[name] = {
                    "cluster_ssh_directory": str(ssh_dir),
                    "cluster_ssh_host_key_file": str(host_key) + ".pub",
                    "cluster_ssh_address": f"{name}.test",
                }
            # node1 already has a key and an unrelated authorized entry; both must survive.
            existing_key = directory / "node1" / ".ssh" / "id_ed25519"
            subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(existing_key)], check=True)
            existing_public = (existing_key.with_suffix(".pub")).read_text().strip()
            unrelated = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPN9dGVzdGtleXRlc3RrZXl0ZXN0a2V5dGVzdGtleXRlc3Q laptop"
            (directory / "node1" / ".ssh" / "authorized_keys").write_text(unrelated + "\n")

            inventory = directory / "hosts.yml"
            inventory.write_text(yaml.safe_dump({"all": {"hosts": hosts}}))
            playbook = directory / "test.yml"
            playbook.write_text(yaml.safe_dump([{
                "name": "Exchange keys between temporary directories",
                "hosts": "all",
                "gather_facts": False,
                "connection": "local",
                "vars": {"ansible_python_interpreter": sys.executable,
                         "cluster_ssh_user": account.pw_name},
                "roles": [str(ROOT / "roles/cluster_ssh")],
            }]))
            env = dict(os.environ, ANSIBLE_LOCAL_TEMP=str(directory / "ansible-tmp"),
                       ANSIBLE_REMOTE_TEMP=str(directory / "remote-tmp"),
                       ANSIBLE_NOCOLOR="1", ANSIBLE_VERBOSITY="0")

            def execute():
                result = subprocess.run(
                    ["ansible-playbook", "-i", str(inventory), str(playbook)],
                    cwd=ROOT, env=env, text=True, capture_output=True, timeout=120,
                )
                output = result.stdout + result.stderr
                self.assertEqual(result.returncode, 0, output)
                return output

            execute()
            public_keys = {name: (directory / name / ".ssh" / "id_ed25519.pub").read_text().strip()
                           for name in names}
            self.assertEqual(public_keys["node1"], existing_public)
            host_keys = {name: " ".join((directory / name / "ssh_host_ed25519_key.pub").read_text().split()[:2])
                         for name in names}
            for name in names:
                authorized = (directory / name / ".ssh" / "authorized_keys").read_text().splitlines()
                for public_key in public_keys.values():
                    self.assertIn(public_key, authorized)
                known = (directory / name / ".ssh" / "known_hosts").read_text()
                for other, host_key in host_keys.items():
                    self.assertIn(f"{other}.test {host_key}", known)
            self.assertIn(unrelated, (directory / "node1" / ".ssh" / "authorized_keys").read_text())

            self.assertEqual(execute().count("changed=0"), 3)
            self.assertEqual((existing_key.with_suffix(".pub")).read_text().strip(), existing_public)


if __name__ == "__main__":
    unittest.main()
