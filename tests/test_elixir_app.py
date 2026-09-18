"""Render the Elixir release service files for a fake release without systemd or Pis."""

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
class ElixirAppTests(unittest.TestCase):
    def test_render_defaults_overrides_repeat_release_change_and_validation(self):
        with tempfile.TemporaryDirectory(prefix="nanocluster-elixir-app-test-") as tmp:
            directory = Path(tmp)
            account = pwd.getpwuid(os.getuid())
            bin_dir = directory / "bin"
            bin_dir.mkdir()
            getent = bin_dir / "getent"
            getent.write_text(
                f"#!{sys.executable}\n"
                "import os, pwd, sys\n"
                "p = pwd.getpwuid(os.getuid())\n"
                "assert sys.argv[1:] == ['passwd', p.pw_name]\n"
                "print(f'{p.pw_name}:x:{p.pw_uid}:{p.pw_gid}:test:{p.pw_dir}:/bin/sh')\n"
            )
            getent.chmod(0o755)

            def make_release(version):
                release = directory / "releases" / version
                (release / "bin").mkdir(parents=True)
                (release / "releases").mkdir()
                launcher = release / "bin" / "myapp"
                launcher.write_text("#!/bin/sh\nexit 0\n")
                launcher.chmod(0o755)
                (release / "releases" / "start_erl.data").write_text(f"15.2.1 {version}\n")
                return release

            current = directory / "current"
            current.symlink_to(make_release("0.1.0"))
            hosts = {}
            for name in ("node1", "node2"):
                root = directory / name
                (root / "systemd").mkdir(parents=True)
                hosts[name] = {
                    "elixir_app_config_dir": str(root / "etc"),
                    "elixir_app_state_dir": str(root / "var"),
                    "elixir_app_systemd_dir": str(root / "systemd"),
                }
            inventory = directory / "hosts.yml"
            inventory.write_text(yaml.safe_dump({"all": {"hosts": hosts}}))
            playbook = directory / "test.yml"
            playbook.write_text(yaml.safe_dump([{
                "name": "Render the Elixir release service for a fake release",
                "hosts": "all",
                "gather_facts": False,
                "connection": "local",
                "vars": {
                    "ansible_python_interpreter": sys.executable,
                    "elixir_app_user": account.pw_name,
                    "elixir_app_node_name": "myapp@testhost.localdomain",
                    "elixir_app_manage_service": False,
                    "erlang_cookie_value": "test_cookie_value",
                },
                "environment": {"PATH": str(bin_dir) + os.pathsep + os.environ["PATH"]},
                "roles": [str(ROOT / "roles/elixir_app")],
            }]))
            env = dict(os.environ, ANSIBLE_LOCAL_TEMP=str(directory / "ansible-tmp"),
                       ANSIBLE_REMOTE_TEMP=str(directory / "remote-tmp"),
                       ANSIBLE_NOCOLOR="1", ANSIBLE_VERBOSITY="0")
            base = {"elixir_app_name": "myapp", "elixir_app_release_path": str(current)}

            def execute(variables, success=True):
                result = subprocess.run(
                    ["ansible-playbook", "-i", str(inventory), str(playbook), "--diff",
                     "-e", yaml.safe_dump({**base, **variables}, default_flow_style=True)],
                    cwd=ROOT, env=env, text=True, capture_output=True, timeout=120,
                )
                output = result.stdout + result.stderr
                self.assertEqual(result.returncode == 0, success, output)
                return output

            environment = {"PORT": "4000", "LANG": "en_US.UTF-8", "SECRET": 'say "hi" \\ there'}
            output = execute({"elixir_app_environment": environment})
            self.assertNotIn("test_cookie_value", output)
            self.assertNotIn('say "hi"', output)
            for name, variables in hosts.items():
                root = directory / name
                unit = (root / "systemd" / "myapp.service").read_text()
                self.assertIn(f"ExecStart={current}/bin/myapp start\n", unit)
                self.assertIn(f"User={account.pw_name}\n", unit)
                self.assertIn(f"EnvironmentFile={root / 'etc' / 'env'}\n", unit)
                env_file = root / "etc" / "env"
                self.assertEqual(stat.S_IMODE(env_file.stat().st_mode), 0o640)
                lines = [line for line in env_file.read_text().splitlines() if not line.startswith("#")]
                self.assertEqual(lines, [
                    'LANG="en_US.UTF-8"',
                    'PORT="4000"',
                    'RELEASE_COOKIE="test_cookie_value"',
                    'RELEASE_DISTRIBUTION="name"',
                    'RELEASE_NODE="myapp@testhost.localdomain"',
                    f'RELEASE_TMP="{root / "var" / "tmp"}"',
                    'SECRET="say \\"hi\\" \\\\ there"',
                ])
                self.assertTrue((root / "var" / "tmp").is_dir())
                self.assertEqual((root / "etc" / "release").read_text(),
                                 f"{(directory / 'releases' / '0.1.0').resolve()} 15.2.1 0.1.0\n")

            self.assertEqual(execute({"elixir_app_environment": environment}).count("changed=0"), 2)

            # Repointing the symlink to a new version changes only the release marker.
            current.unlink()
            current.symlink_to(make_release("0.2.0"))
            self.assertEqual(execute({"elixir_app_environment": environment}).count("changed=1"), 2)
            for name in hosts:
                self.assertEqual((directory / name / "etc" / "release").read_text(),
                                 f"{(directory / 'releases' / '0.2.0').resolve()} 15.2.1 0.2.0\n")

            # Validation stops before rendering.
            execute({"elixir_app_name": "MyApp"}, success=False)
            execute({"elixir_app_release_path": str(directory / "missing")}, success=False)
            execute({"elixir_app_environment": {"1BAD": "x"}}, success=False)
            execute({"elixir_app_environment": {"MULTI": "a\nb"}}, success=False)


if __name__ == "__main__":
    unittest.main()
