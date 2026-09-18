"""Run the real plugin tasks against a fake asdf, entirely in a temp directory."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "collections/ansible_collections/m1dnight/nanocluster/roles/asdf/tasks/plugin.yml"
FAKE_ASDF = '''
import json
import os
from pathlib import Path
import sys
root = Path(os.environ["ASDF_DATA_DIR"])
args = sys.argv[1:]
with (root / "calls.jsonl").open("a") as log:
    log.write(json.dumps(args) + "\\n")
if args[:2] == ["plugin", "add"]:
    (root / "plugins" / args[2]).mkdir(parents=True)
elif args[0] == "latest":
    print("27.3")
elif args[0] == "install":
    (root / "installs" / args[1] / args[2]).mkdir(parents=True)
else:
    sys.exit("Unexpected asdf command")
'''


@unittest.skipUnless(shutil.which("ansible-playbook"), "ansible-playbook is required")
class AsdfPluginTests(unittest.TestCase):
    def test_install_repeat_and_version_change_preserve_other_tools(self):
        with tempfile.TemporaryDirectory(prefix="nanocluster-asdf-test-") as tmp:
            home = Path(tmp)
            data = home / ".asdf"
            data.mkdir()
            executable = data / "asdf"
            executable.write_text(f"#!{sys.executable}\n" + FAKE_ASDF)
            executable.chmod(0o755)
            versions = home / ".tool-versions"
            versions.write_text("python 3.12.8\nerlang 26.2\n")
            playbook = home / "test.yml"
            env = dict(os.environ, ANSIBLE_LOCAL_TEMP=str(home / "ansible-tmp"),
                       ANSIBLE_REMOTE_TEMP=str(home / "remote-tmp"),
                       ANSIBLE_NOCOLOR="1", ANSIBLE_VERBOSITY="0")

            def execute(version):
                playbook.write_text(yaml.safe_dump([{
                    "name": "Exercise local asdf plugin tasks",
                    "hosts": "localhost",
                    "gather_facts": False,
                    "connection": "local",
                    "vars": {
                        "ansible_python_interpreter": sys.executable,
                        "ansible_facts": {"user_dir": str(home), "env": {"PATH": os.environ["PATH"]}},
                        "asdf_directory": str(data),
                        "asdf_plugin": {"name": "erlang", "version": version},
                    },
                    "tasks": [{"name": "Run plugin tasks", "ansible.builtin.include_tasks": str(TASKS)}],
                }]))
                result = subprocess.run(
                    ["ansible-playbook", "-i", "localhost,", str(playbook)],
                    cwd=ROOT, env=env, text=True, capture_output=True, timeout=60,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                return result.stdout

            execute("latest")
            self.assertEqual(versions.read_text(), "python 3.12.8\nerlang 27.3\n")
            self.assertRegex(execute("latest"), r"changed=0\s")
            calls = [json.loads(line) for line in (data / "calls.jsonl").read_text().splitlines()]
            self.assertEqual(calls.count(["plugin", "add", "erlang"]), 1)
            self.assertEqual(calls.count(["latest", "erlang"]), 2)
            self.assertEqual(calls.count(["install", "erlang", "27.3"]), 1)
            execute("27.2")
            self.assertEqual(versions.read_text(), "python 3.12.8\nerlang 27.2\n")
            self.assertRegex(execute("27.2"), r"changed=0\s")


if __name__ == "__main__":
    unittest.main()
