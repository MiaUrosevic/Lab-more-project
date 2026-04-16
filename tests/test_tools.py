from unittest.mock import patch
from tools.ls import run_ls
from tools.cat import run_cat
from tools.grep import run_grep
from tools.calculate import run_calculate
from tools.compact import run_compact


def test_ls_unsafe():
    assert run_ls("..") == "Error: unsafe path"


def test_ls_normal():
    result = run_ls(".")
    assert isinstance(result, str)


def test_cat_unsafe():
    assert run_cat("..") == "Error: unsafe path"


def test_cat_missing_file():
    assert "Error:" in run_cat("not_a_real_file_123.txt")


def test_cat_chat_file():
    assert "Main entry point" in run_cat("chat.py")


def test_grep_unsafe():
    assert run_grep("x", "..") == "Error: unsafe path"


def test_grep_match():
    assert "def run_ls" in run_grep("def run_ls", "tools/*.py")


def test_grep_no_match():
    assert run_grep("^zzzzzz_not_found_12345$", "tools/*.py") == ""


def test_calculate_basic():
    assert run_calculate("3 * 4") == "12"


def test_calculate_error():
    assert "Error:" in run_calculate("hello")


def test_compact():
    class DummyChat:
        def __init__(self):
            self.messages = [{"role": "user", "content": "hello"}]
            self.provider = "groq"
            self.debug = False

    chat = DummyChat()
    result = run_compact(chat)
    assert result.startswith("Summary of conversation:")
    assert chat.messages[0]["role"] == "system"


def test_grep_exception_branch():
    with patch("glob.glob", return_value=["fakefile.txt"]):
        with patch("builtins.open", side_effect=Exception("boom")):
            assert run_grep("x", "*.txt") == ""
