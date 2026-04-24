"""Unit tests for tool modules and their safety behavior."""

import json
import os
from unittest.mock import patch

from git import Repo

from chat import Chat
from tools.calculate import TOOL_SPEC as CALCULATE_TOOL_SPEC
from tools.calculate import run_calculate
from tools.cat import TOOL_SPEC as CAT_TOOL_SPEC
from tools.cat import read_text_file, run_cat
from tools.compact import TOOL_SPEC as COMPACT_TOOL_SPEC
from tools.compact import run_compact
from tools.doctests import TOOL_SPEC as DOCTESTS_TOOL_SPEC
from tools.doctests import run_doctests
from tools.grep import TOOL_SPEC as GREP_TOOL_SPEC
from tools.grep import run_grep
from tools.ls import TOOL_SPEC as LS_TOOL_SPEC
from tools.ls import run_ls
from tools.pip_install import TOOL_SPEC as PIP_INSTALL_TOOL_SPEC
from tools.pip_install import run_pip_install
from tools.repo_utils import is_repo_path_safe
from tools.rm import TOOL_SPEC as RM_TOOL_SPEC
from tools.rm import run_rm
from tools.write_file import TOOL_SPEC as WRITE_FILE_TOOL_SPEC
from tools.write_file import run_write_file
from tools.write_files import TOOL_SPEC as WRITE_FILES_TOOL_SPEC
from tools.write_files import run_write_files


def test_tool_specs_have_expected_names():
    """Expose the expected tool names to the automatic tool caller."""
    assert LS_TOOL_SPEC["function"]["name"] == "ls"
    assert CAT_TOOL_SPEC["function"]["name"] == "cat"
    assert GREP_TOOL_SPEC["function"]["name"] == "grep"
    assert CALCULATE_TOOL_SPEC["function"]["name"] == "calculate"
    assert COMPACT_TOOL_SPEC["function"]["name"] == "compact"
    assert DOCTESTS_TOOL_SPEC["function"]["name"] == "doctests"
    assert WRITE_FILE_TOOL_SPEC["function"]["name"] == "write_file"
    assert WRITE_FILES_TOOL_SPEC["function"]["name"] == "write_files"
    assert RM_TOOL_SPEC["function"]["name"] == "rm"
    assert PIP_INSTALL_TOOL_SPEC["function"]["name"] == "pip_install"


def test_repo_path_safe():
    """Reject writes and deletes inside .git."""
    assert is_repo_path_safe("chat.py") is True
    assert is_repo_path_safe(".git/config") is False


def test_ls_unsafe():
    """Reject unsafe ls paths."""
    assert run_ls("..") == "Error: unsafe path"


def test_ls_normal():
    """Return a string listing for normal ls calls."""
    result = run_ls(".")
    assert isinstance(result, str)


def test_cat_unsafe():
    """Reject unsafe cat paths."""
    assert run_cat("..") == "Error: unsafe path"


def test_read_text_file():
    """Read plain UTF-8 text files."""
    assert "Main entry point" in read_text_file("chat.py")


def test_read_text_file_windows_utf16(tmp_path):
    """Fall back to UTF-16 decoding on Windows."""
    file_path = tmp_path / "utf16.txt"
    file_path.write_text("hello", encoding="utf-16")
    with patch("platform.system", return_value="Windows"):
        assert read_text_file(str(file_path)) == "hello"


def test_read_text_file_decode_error():
    """Raise the final decode error when all supported encodings fail."""
    decode_error = UnicodeDecodeError(
        "utf-8",
        b"\xff",
        0,
        1,
        "invalid start byte",
    )
    with patch("platform.system", return_value="Windows"):
        with patch("builtins.open", side_effect=[decode_error, decode_error]):
            try:
                read_text_file("bad.txt")
            except UnicodeDecodeError as error:
                assert error is decode_error
            else:
                raise AssertionError("Expected UnicodeDecodeError")


def test_cat_missing_file():
    """Return an error for missing files."""
    assert "Error:" in run_cat("not_a_real_file_123.txt")


def test_cat_chat_file():
    """Read the main chat module successfully."""
    assert "Main entry point" in run_cat("chat.py")


def test_cat_decode_error_branch():
    """Catch read errors raised by the shared file loader."""
    with patch(
        "tools.cat.read_text_file",
        side_effect=UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte"),
    ):
        assert "Error:" in run_cat("chat.py")


def test_grep_unsafe():
    """Reject unsafe grep globs."""
    assert run_grep("x", "..") == "Error: unsafe path"


def test_grep_match():
    """Find matching lines across the tool modules."""
    assert "def run_ls" in run_grep("def run_ls", "tools/*.py")


def test_grep_no_match():
    """Return an empty string when grep finds nothing."""
    assert run_grep("^zzzzzz_not_found_12345$", "tools/*.py") == ""


def test_doctests_tool():
    """Run verbose doctests for a Python file."""
    output = run_doctests("tools/calculate.py")
    assert "Test passed." in output


def test_doctests_tool_unsafe():
    """Reject unsafe doctest paths."""
    assert run_doctests("..") == "Error: unsafe path"


def test_calculate_basic():
    """Return JSON for successful calculations."""
    assert json.loads(run_calculate("3 * 4")) == {"result": 12}


def test_calculate_error():
    """Return JSON for calculation failures."""
    assert "error" in json.loads(run_calculate("hello"))


def test_compact():
    """Rewrite a chat history into a compact summary."""
    chat = Chat()
    chat.messages = [{"role": "user", "content": "hello"}]
    result = run_compact(chat)
    assert result.startswith("Summary of conversation:")
    assert chat.messages[0]["role"] == "system"


def test_grep_exception_branch():
    """Skip unreadable files while continuing the search."""
    with patch("glob.glob", return_value=["fakefile.txt"]):
        with patch("tools.grep.read_text_file", side_effect=Exception("boom")):
            assert run_grep("x", "*.txt") == ""


def test_write_file(tmp_path):
    """Write one file, commit it, and keep UTF-8 contents."""
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        Repo.init(tmp_path)
        result = run_write_file("demo.txt", "hello", "write demo")
        assert "Committed" in result
        assert (tmp_path / "demo.txt").read_text(encoding="utf-8") == "hello"
    finally:
        os.chdir(old_cwd)


def test_write_files_runs_doctests(tmp_path):
    """Run doctests after writing Python files."""
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        Repo.init(tmp_path)
        result = run_write_files(
            [{"path": "demo.py", "contents": '"""\n>>> 2 + 2\n4\n"""'}],
            "write demo python",
        )
        assert "$ doctests demo.py" in result
        assert "Test passed." in result
    finally:
        os.chdir(old_cwd)


def test_write_files_creates_parent_directories(tmp_path):
    """Create missing parent directories before writing nested files."""
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        Repo.init(tmp_path)
        result = run_write_files(
            [{"path": "nested/demo.txt", "contents": "hello"}],
            "write nested file",
        )
        assert "Committed" in result
        assert (tmp_path / "nested" / "demo.txt").read_text(encoding="utf-8") == "hello"
    finally:
        os.chdir(old_cwd)


def test_write_files_unsafe():
    """Reject unsafe paths before writing files."""
    assert run_write_files([{"path": "..", "contents": "x"}], "bad") == "Error: unsafe path"


def test_rm_tool(tmp_path):
    """Delete tracked files and commit the removal."""
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        repo = Repo.init(tmp_path)
        (tmp_path / "demo.txt").write_text("hello", encoding="utf-8")
        repo.index.add(["demo.txt"])
        _ = repo.index.commit("init")
        result = run_rm("demo.txt")
        assert "Committed" in result
        assert not (tmp_path / "demo.txt").exists()
    finally:
        os.chdir(old_cwd)


def test_rm_tool_no_match():
    """Return a clear error when rm finds nothing."""
    assert run_rm("definitely-not-real.txt").startswith("Error: no files matched")


def test_rm_tool_directory_only_match(tmp_path):
    """Ignore directory matches and report when no files were removed."""
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        Repo.init(tmp_path)
        (tmp_path / "folder").mkdir()
        assert run_rm("folder") == "Error: no files matched folder"
    finally:
        os.chdir(old_cwd)


def test_rm_tool_rejects_unsafe_glob_match():
    """Reject any unsafe resolved matches before attempting deletion."""
    with patch("glob.glob", return_value=["../danger.txt"]):
        assert run_rm("*.txt") == "Error: unsafe path"


def test_rm_tool_unsafe():
    """Reject unsafe rm paths."""
    assert run_rm("..") == "Error: unsafe path"


def test_pip_install_tool():
    """Run pip_install through subprocess."""
    completed = MockCompletedProcess("ok")
    with patch("subprocess.run", return_value=completed):
        assert run_pip_install("requests") == "ok"


class MockCompletedProcess:
    """Minimal completed process object for subprocess tool tests."""

    def __init__(self, stdout, stderr=""):
        """Store fake process output."""
        self.stdout = stdout
        self.stderr = stderr
