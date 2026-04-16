from unittest.mock import patch
from chat import Chat, is_path_safe, main, repl


def test_is_path_safe():
    assert is_path_safe("README.md") is True
    assert is_path_safe("/etc/passwd") is False
    assert is_path_safe("../x") is False
    assert is_path_safe("a/../b.txt") is False


def test_unknown_manual_command():
    chat = Chat()
    assert chat.run_manual_command("/notreal") == "Error: unknown command 'notreal'"


def test_manual_ls_returns_string():
    chat = Chat()
    result = chat.run_manual_command("/ls")
    assert isinstance(result, str)


def test_manual_cat_wrong_args():
    chat = Chat()
    assert chat._tool_cat() == "Error: cat requires 1 argument"


def test_manual_grep_wrong_args():
    chat = Chat()
    assert chat._tool_grep("x") == "Error: grep requires 2 arguments"


def test_manual_calculate_wrong_args():
    chat = Chat()
    assert chat._tool_calculate() == "Error: calculate requires 1 argument"


def test_auto_choose_ls():
    chat = Chat()
    assert chat._auto_choose_tool(
        "what files are in the .github folder?"
    ) == ("ls", [".github"])


def test_auto_choose_cat():
    chat = Chat()
    assert chat._auto_choose_tool("show me README.md") == ("cat", ["README.md"])


def test_auto_choose_grep():
    chat = Chat()
    assert chat._auto_choose_tool(
        "find def run_ls in tools/*.py"
    ) == ("grep", ["def run_ls", "tools/*.py"])


def test_auto_choose_calculate():
    chat = Chat()
    assert chat._auto_choose_tool("what is 5 + 7?") == ("calculate", ["5 + 7"])


def test_auto_choose_none():
    chat = Chat()
    assert chat._auto_choose_tool("tell me something interesting") is None


def test_send_message_calculate():
    chat = Chat()
    assert chat.send_message("what is 5 + 7?") == "12"


def test_send_message_unknown():
    chat = Chat()
    result = chat.send_message("tell me something interesting")
    assert "I could not automatically determine" in result


def test_send_message_ls_empty_branch():
    chat = Chat()
    with patch.object(chat, "_tool_ls", return_value=""):
        chat.tools["ls"] = chat._tool_ls
        result = chat.send_message("what files are in the .github folder?")
        assert result == "That folder appears to be empty."


def test_send_message_ls_multiple_branch():
    chat = Chat()
    with patch.object(chat, "_tool_ls", return_value="a\nb"):
        chat.tools["ls"] = chat._tool_ls
        result = chat.send_message("what files are in the .github folder?")
        assert result == "The files in that folder are: a, b."


def test_manual_compact():
    chat = Chat()
    chat.messages.append({"role": "user", "content": "hello"})
    result = chat.run_manual_command("/compact")
    assert result.startswith("Summary of conversation:")


def test_main_one_shot():
    assert main(["what is 2 + 2?"]) is None


def test_repl_keyboard_interrupt(capsys):
    chat = Chat()
    with patch("builtins.input", side_effect=KeyboardInterrupt):
        repl(chat)
    captured = capsys.readouterr()
    assert captured.out == "\n"


def test_repl_slash_command(capsys):
    chat = Chat()
    with patch("builtins.input", side_effect=["/calculate 2+2", KeyboardInterrupt]):
        repl(chat)
    captured = capsys.readouterr()
    assert "4" in captured.out


def test_repl_normal_message(capsys):
    chat = Chat()
    with patch("builtins.input", side_effect=["what is 2 + 2?", KeyboardInterrupt]):
        repl(chat)
    captured = capsys.readouterr()
    assert "4" in captured.out
