import subprocess
import sys


def test_cli_message_runs():
    result = subprocess.run(
        [sys.executable, "chat.py", "what is 2 + 2?"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "4" in result.stdout


def test_cli_debug_runs():
    result = subprocess.run(
        [sys.executable, "chat.py", "--debug", "what is 2 + 2?"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "[tool] /calculate 2 + 2" in result.stdout
    assert "4" in result.stdout


def test_cli_provider_runs():
    result = subprocess.run(
        [sys.executable, "chat.py", "--provider", "groq", "what is 2 + 2?"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "4" in result.stdout
