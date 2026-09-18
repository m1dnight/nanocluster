"""Exercise Erlang cookie and hosts file provisioning in temporary homes without connecting to Pis."""

import os
from pathlib import Path
import pwd
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("ansible-playbook"), "ansible-playbook is required")
class ErlangSetupTests(unittest.TestCase):
    def test_shared_cookie_permissions_repeat_rotation_and_hidden_output(self):
        with tempfile.TemporaryDirectory(prefix="nanocluster-cookie-test-") as tmp:
            directory = Path(tmp)
            account = pwd.getpwuid(os.getuid())
            homes = [directory / name for name in ("node1", "node2")]
            for home in homes:
                home.mkdir()
            bin_dir = directory / "bin"
            bin_dir.mkdir()
            getent = bin_dir / "getent"
            getent.write_text(
                f"#!{sys.executable}\n"
                "import os, pwd, sys\n"
                "p = pwd.getpwuid(os.getuid())\n"
                "assert sys.argv[1:] == ['passwd', p.pw_name]\n"
                "print(f'{p.pw_name}:x:{p.pw_uid}:{p.pw_gid}:test:'"
                " + os.environ['COOKIE_TEST_HOME'] + ':/bin/sh')\n"
            )
            getent.chmod(0o755)
            inventory = directory / "hosts.yml"
            inventory.write_text(yaml.safe_dump({"all": {"children": {"nodes": {"hosts": {
                home.name: {"cookie_test_home": str(home), "ansible_host": f"{home.name}.test"}
                for home in homes
            }}}}}))
            playbook = directory / "test.yml"
            playbook.write_text(yaml.safe_dump([{
                "name": "Exercise cookie provisioning in temporary homes",
                "hosts": "all",
                "gather_facts": False,
                "connection": "local",
                "become": False,
                "vars": {
                    "ansible_python_interpreter": sys.executable,
                    "erlang_setup_user": account.pw_name,
                },
                "environment": {
                    "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"],
                    "COOKIE_TEST_HOME": "{{ cookie_test_home }}",
                },
                "roles": [str(ROOT / "roles/erlang_setup")],
            }]))
            env = dict(os.environ, ANSIBLE_LOCAL_TEMP=str(directory / "ansible-tmp"),
                       ANSIBLE_REMOTE_TEMP=str(directory / "remote-tmp"),
                       ANSIBLE_NOCOLOR="1", ANSIBLE_VERBOSITY="0")

            def execute(cookie, success=True):
                variables = directory / "vars.yml"
                variables.write_text(yaml.safe_dump({"erlang_setup_cookie": cookie}))
                result = subprocess.run(
                    ["ansible-playbook", "-i", str(inventory), str(playbook),
                     "--diff", "-e", "@" + str(variables)],
                    cwd=ROOT, env=env, text=True, capture_output=True, timeout=60,
                )
                output = result.stdout + result.stderr
                self.assertNotIn(cookie, output)
                self.assertEqual(result.returncode == 0, success, output)
                return output

            original = "test_cookie_001"
            execute(original)
            for home in homes:
                cookie_file = home / ".erlang.cookie"
                self.assertEqual(cookie_file.read_text(), original + "\n")
                metadata = cookie_file.stat()
                self.assertEqual(stat.S_IMODE(metadata.st_mode), 0o400)
                self.assertEqual(metadata.st_uid, account.pw_uid)
                self.assertEqual(metadata.st_gid, account.pw_gid)
                hosts_file = home / ".hosts.erlang"
                self.assertEqual(hosts_file.read_text(), "'node1.test'.\n'node2.test'.\n")
                self.assertEqual(stat.S_IMODE(hosts_file.stat().st_mode), 0o644)
            self.assertEqual(execute(original).count("changed=0"), 2)
            replacement = "test_cookie_002"
            self.assertNotIn(original, execute(replacement))
            execute("invalid cookie with spaces", success=False)
            for home in homes:
                self.assertEqual((home / ".erlang.cookie").read_text(), replacement + "\n")


if __name__ == "__main__":
    unittest.main()
