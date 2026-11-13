"""Routing and terminal-state regressions for supported peer agents."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "peer_agent", Path(__file__).resolve().parents[1] / "scripts" / "peer_agent.py"
)
peer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(peer)


class AgentSupportTests(unittest.TestCase):
    def test_process_and_pane_detection(self):
        for command, agent in [
            ("/opt/bin/agy --continue", "agy"),
            ("node /opt/bin/codex", "codex"),
            ("/opt/claude/versions/2.1.272", "claude"),
            ("python3 unrelated.py", None),
        ]:
            with self.subTest(command=command):
                self.assertEqual(peer.command_agent(command), agent)
        for command, agent in [("agy", "agy"), ("codex", "codex"),
                               ("2.1.272", "claude"), ("zsh", None)]:
            self.assertEqual(peer.pane_agent(command), agent)

    def test_agy_busy_is_not_reused(self):
        panes = "%2\tagy\tagy\t/tmp\n%3\tagy\tagy\t/tmp"
        with patch.object(peer, "tmux", return_value=panes), patch.object(
            peer, "capture", side_effect=["Generating...\nesc to cancel", "? for shortcuts"]
        ):
            self.assertEqual(peer.find_idle_pane("agy", Path("/tmp"), "%1"), ("%3", ["%2"]))

    def test_submit_refuses_busy_agy_before_pasting(self):
        with patch.object(peer, "pane_info", return_value={"in_mode": "0"}), patch.object(
            peer, "capture", return_value="Generating...\nesc to cancel"
        ), patch.object(peer, "tmux") as tmux:
            with self.assertRaises(SystemExit) as error:
                peer.submit("%2", "brief", Path("/unused/result"))
            self.assertEqual(error.exception.code, 2)
            tmux.assert_not_called()

    def test_launch_uses_agy_override(self):
        with patch.dict(peer.os.environ, {"PEER_AGENT_AGY_CMD": "agy --model example"}), patch.object(
            peer, "wait_for", return_value=True
        ), patch.object(peer, "capture", return_value="? for shortcuts"), patch.object(
            peer.time, "sleep"
        ), patch.object(peer, "tmux") as tmux:
            peer.start_agent("%2", "agy")
            tmux.assert_any_call("send-keys", "-t", "%2", "-l", "agy --model example")
            tmux.assert_any_call("send-keys", "-t", "%2", "Enter")

    def test_cli_accepts_agy(self):
        args = peer.parse_args(["send", "--agent", "agy", "--message-file", "-"])
        self.assertEqual(args.agent, "agy")


if __name__ == "__main__":
    unittest.main()
