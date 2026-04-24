"""Integration tests for the CLI and real project directories."""

import json
import os
import subprocess
import sys
from git import Repo
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CHAT_SCRIPT = REPO_ROOT / "chat.py"


def test_cli_message_runs():
    """Return a one-shot calculation answer from the CLI."""
    result = subprocess.run(
        [sys.executable, str(CHAT_SCRIPT), "what is 2 + 2?"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "4"


def test_cli_debug_runs():
    """Show debug output for automatic tool calls."""
    result = subprocess.run(
        [sys.executable, str(CHAT_SCRIPT), "--debug", "what is 2 + 2?"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 0
    assert "[tool] /calculate 2 + 2" in result.stdout
    assert result.stdout.strip().endswith("4")


def test_cli_provider_runs():
    """Accept the provider flag while still answering normally."""
    result = subprocess.run(
        [sys.executable, str(CHAT_SCRIPT), "--provider", "groq", "what is 2 + 2?"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "4"


def test_cli_openai_provider_stub():
    """Use the provider code path in a subprocess with a stubbed API response."""
    env = {
        **os.environ,
        "OPENROUTER_API_KEY": "test-token",
        "CHAT_PROVIDER_STUB_RESPONSE": json.dumps(
            {
                "choices": [
                    {
                        "message": {
                            "content": "Stub provider response.",
                        }
                    }
                ]
            }
        ),
    }
    result = subprocess.run(
        [sys.executable, str(CHAT_SCRIPT), "--provider", "openai", "tell me about this repo"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        env=env,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == "Stub provider response."


def test_repl_manual_command_runs():
    """Run slash commands directly through the interactive REPL."""
    result = subprocess.run(
        [sys.executable, str(CHAT_SCRIPT)],
        input="/ls .github\n",
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 0
    assert "workflows" in result.stdout


def test_submodules_are_checked_out():
    """Populate the assignment's test_projects submodules in the repository."""
    for folder_name in [
        "webscraping_project",
        "markdown_compiler",
        "Mia.Urosevic.github.io",
    ]:
        project_dir = REPO_ROOT / "test_projects" / folder_name
        assert project_dir.exists()
        assert any(project_dir.iterdir())


def test_repo_includes_agents_file():
    """Ship a root AGENTS.md file for repository-specific agent instructions."""
    assert (REPO_ROOT / "AGENTS.md").exists()


def test_chat_runs_in_markdown_submodule():
    """Run the chat tool inside a previous project submodule."""
    project_dir = REPO_ROOT / "test_projects" / "markdown_compiler"
    result = subprocess.run(
        [sys.executable, str(CHAT_SCRIPT), "show me README.md"],
        capture_output=True,
        text=True,
        cwd=project_dir,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout.strip()


def test_cli_requires_git_directory(tmp_path):
    """Stop immediately when launched outside a git repository."""
    result = subprocess.run(
        [sys.executable, str(CHAT_SCRIPT), "what is 2 + 2?"],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        check=False,
    )
    assert result.returncode == 0
    assert (
        result.stdout.strip()
        == "Error: docchat must be run from a directory containing a .git folder"
    )


def test_cli_loads_agents_file(tmp_path):
    """Preload AGENTS.md so provider-backed runs can see repository instructions."""
    Repo.init(tmp_path)
    (tmp_path / "AGENTS.md").write_text("Always mention safety first.", encoding="utf-8")
    env = {
        **os.environ,
        "OPENROUTER_API_KEY": "test-token",
        "CHAT_PROVIDER_STUB_RESPONSE": json.dumps(
            {
                "choices": [
                    {
                        "message": {
                            "content": "Stub provider response.",
                        }
                    }
                ]
            }
        ),
    }
    result = subprocess.run(
        [sys.executable, str(CHAT_SCRIPT), "--provider", "openai", "hello"],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env=env,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == "Stub provider response."
