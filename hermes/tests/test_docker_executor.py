import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from docker_executor import SandboxError, read_allowed  # noqa: E402
from supervisor import Supervisor  # noqa: E402


class DockerExecutorTests(unittest.TestCase):
    def setUp(self):
        scratch = ROOT / "local" / "test-tmp"
        scratch.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temporary.cleanup)
        self.data = Path(self.temporary.name) / "datos"
        (self.data / "permitidos").mkdir(parents=True)
        (self.data / "privados").mkdir()
        (self.data / "permitidos" / "nota.txt").write_text("permitido", encoding="utf-8")
        (self.data / "privados" / "secreto.txt").write_text("privado", encoding="utf-8")

    @patch("docker_executor.subprocess.run")
    def test_container_receives_only_readonly_allowed_directory(self, run):
        run.return_value = Mock(returncode=0, stdout="permitido")
        self.assertEqual(read_allowed(self.data, "nota.txt"), "permitido")
        args = run.call_args.args[0]
        self.assertIn("none", args)
        self.assertIn("--read-only", args)
        self.assertIn("--memory", args)
        self.assertIn("--cpus", args)
        mounts = [args[i + 1] for i, value in enumerate(args[:-1]) if value == "--mount"]
        self.assertEqual(len(mounts), 1)
        self.assertIn("target=/lab/permitidos,readonly", mounts[0])
        self.assertNotIn("privados", mounts[0])

    @patch("docker_executor.subprocess.run")
    def test_secure_read_fails_closed_when_docker_unavailable(self, run):
        run.side_effect = OSError("docker apagado")
        supervisor = Supervisor(self.data, docker_secure=True)
        outcome = supervisor.execute("to-be", "read_file", "permitidos/nota.txt")
        self.assertFalse(outcome["audit"]["allowed"])
        self.assertIsNone(outcome["result"])

    def test_private_file_never_reaches_container(self):
        with patch("docker_executor.subprocess.run") as run:
            supervisor = Supervisor(self.data, docker_secure=True)
            outcome = supervisor.execute("to-be", "read_file", "privados/secreto.txt")
            self.assertFalse(outcome["audit"]["allowed"])
            run.assert_not_called()

    def test_unlisted_file_is_rejected(self):
        (self.data / "permitidos" / "otro.txt").write_text("x", encoding="utf-8")
        with self.assertRaises(SandboxError):
            read_allowed(self.data, "otro.txt")


if __name__ == "__main__":
    unittest.main()
