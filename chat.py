"""
Main entry point for the local project chat application.

This file defines the Chat class, path safety checks, startup repository checks,
the CLI interface, and the interactive REPL for talking to local project files.
"""

import argparse
import glob
import json
import os
import shlex
from pathlib import PurePath, PurePosixPath, PureWindowsPath

import requests


PROVIDER_CONFIGS = {
    "groq": {
        "api_base_env": "GROQ_API_BASE",
        "api_key_env": "GROQ_API_KEY",
        "api_url": "https://api.groq.com/openai/v1/chat/completions",
        "model": "openai/gpt-oss-120b",
    },
    "openai": {
        "api_base_env": "OPENROUTER_API_BASE",
        "api_key_env": "OPENROUTER_API_KEY",
        "api_url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "openai/gpt-5",
    },
    "anthropic": {
        "api_base_env": "OPENROUTER_API_BASE",
        "api_key_env": "OPENROUTER_API_KEY",
        "api_url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "anthropic/claude-opus-4.6",
    },
    "google": {
        "api_base_env": "OPENROUTER_API_BASE",
        "api_key_env": "OPENROUTER_API_KEY",
        "api_url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "google/gemini-3.1-pro-preview",
    },
}


def is_path_safe(path: str) -> bool:
    """
    Return True only if a path is relative and contains no directory traversal.

    >>> is_path_safe("README.md")
    True
    >>> is_path_safe("tools/ls.py")
    True
    >>> is_path_safe("/etc/passwd")
    False
    >>> is_path_safe("../secret.txt")
    False
    >>> is_path_safe("a/../b.txt")
    False
    >>> is_path_safe(r"C:\\Windows\\System32")
    False
    """
    if not path:
        return True
    if os.path.isabs(path):
        return False
    if PurePosixPath(path).is_absolute() or PureWindowsPath(path).is_absolute():
        return False
    normalized_path = path.replace("\\", "/")
    return ".." not in PurePath(normalized_path).parts


def list_path_completions(prefix):
    """
    Return sorted path completions for the current token prefix.

    >>> "__pycache__" not in list_path_completions("")
    True
    >>> ".github" in list_path_completions(".g")
    True
    """
    if prefix:
        matches = glob.glob(f"{prefix}*")
    else:
        matches = glob.glob("*") + glob.glob(".*")
    cleaned = [match for match in sorted(set(matches)) if match not in {".", ".."}]
    return [match for match in cleaned if "__pycache__" not in match]


def complete_input(text, state, line_buffer=None, commands=None):
    """
    Return a single readline completion candidate for the current state.

    >>> complete_input("/l", 0, "/l", commands=["ls", "cat"])
    '/ls'
    >>> complete_input(".g", 0, "/ls .g") in {'.git', '.github'}
    True
    """
    active_commands = sorted(commands or [])
    buffer = text if line_buffer is None else line_buffer
    tokens = buffer.split()

    if buffer.startswith("/") and (len(tokens) <= 1 and not buffer.endswith(" ")):
        matches = [f"/{command}" for command in active_commands if command.startswith(text[1:])]
    else:
        matches = list_path_completions(text)

    if state < len(matches):
        return matches[state]
    return None


def configure_readline(commands):
    """
    Configure readline tab completion for slash commands and file paths.

    >>> configure_readline(["ls", "cat"]) in {True, False}
    True
    """
    try:
        import readline
    except ImportError:
        return False

    readline.set_completer_delims(" \t\n;")
    readline.set_completer(
        lambda text, state: complete_input(
            text,
            state,
            line_buffer=readline.get_line_buffer(),
            commands=commands,
        )
    )
    readline.parse_and_bind("tab: complete")
    return True


def validate_repo_startup():
    """
    Validate that the current directory looks like a git repository root.

    >>> import os, tempfile
    >>> with tempfile.TemporaryDirectory() as tmpdir:
    ...     old_cwd = os.getcwd()
    ...     os.chdir(tmpdir)
    ...     result = validate_repo_startup()
    ...     os.chdir(old_cwd)
    ...     result
    'Error: docchat must be run from a directory containing a .git folder'
    """
    if not os.path.isdir(".git"):
        return "Error: docchat must be run from a directory containing a .git folder"
    return None


class Chat:
    """
    A Chat manages a local file-aware conversation session with manual and automatic tool use.

    It stores messages, supports slash commands like `/ls` and `/cat`, validates
    repository startup requirements, and can either use deterministic local routing
    or call a configured provider with local tool orchestration.

    >>> chat = Chat()
    >>> isinstance(chat.messages, list)
    True
    >>> names = sorted(chat.tools.keys())
    >>> names[:4]
    ['calculate', 'cat', 'compact', 'doctests']
    >>> names[-3:]
    ['rm', 'write_file', 'write_files']
    """

    def __init__(self, provider="groq", debug=False):
        """
        Initialize a new Chat session.
        """
        from tools.calculate import TOOL_SPEC as CALCULATE_TOOL_SPEC
        from tools.calculate import run_calculate
        from tools.cat import TOOL_SPEC as CAT_TOOL_SPEC
        from tools.cat import run_cat
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
        from tools.rm import TOOL_SPEC as RM_TOOL_SPEC
        from tools.rm import run_rm
        from tools.write_file import TOOL_SPEC as WRITE_FILE_TOOL_SPEC
        from tools.write_file import run_write_file
        from tools.write_files import TOOL_SPEC as WRITE_FILES_TOOL_SPEC
        from tools.write_files import run_write_files

        self.provider = provider
        self.debug = debug
        self.messages = []
        self.pending_doctest_retry = False
        self.tools = {
            "ls": {
                "spec": LS_TOOL_SPEC,
                "runner": lambda path=".": run_ls(path),
                "manual_arguments": ["path"],
            },
            "cat": {
                "spec": CAT_TOOL_SPEC,
                "runner": run_cat,
                "manual_arguments": ["path"],
            },
            "grep": {
                "spec": GREP_TOOL_SPEC,
                "runner": run_grep,
                "manual_arguments": ["pattern", "path_glob"],
            },
            "calculate": {
                "spec": CALCULATE_TOOL_SPEC,
                "runner": run_calculate,
                "manual_arguments": ["expression"],
            },
            "compact": {
                "spec": COMPACT_TOOL_SPEC,
                "runner": lambda: run_compact(self),
                "manual_arguments": [],
            },
            "doctests": {
                "spec": DOCTESTS_TOOL_SPEC,
                "runner": run_doctests,
                "manual_arguments": ["path"],
            },
            "write_file": {
                "spec": WRITE_FILE_TOOL_SPEC,
                "runner": run_write_file,
                "manual_arguments": ["path", "contents", "commit_message"],
            },
            "write_files": {
                "spec": WRITE_FILES_TOOL_SPEC,
                "runner": run_write_files,
                "manual_arguments": ["files_json", "commit_message"],
            },
            "rm": {
                "spec": RM_TOOL_SPEC,
                "runner": run_rm,
                "manual_arguments": ["path"],
            },
            "pip_install": {
                "spec": PIP_INSTALL_TOOL_SPEC,
                "runner": run_pip_install,
                "manual_arguments": ["library_name"],
            },
        }

    def _debug_print(self, command, args):
        """
        Print a tool debug line if debug mode is enabled.

        >>> chat = Chat(debug=False)
        >>> chat._debug_print("ls", [".github"]) is None
        True
        """
        if self.debug:
            print(f"[tool] /{command}" + (f" {' '.join(args)}" if args else ""))

    def build_summary(self, messages=None):
        """
        Build a short summary of the provided chat messages.

        >>> chat = Chat()
        >>> summary = chat.build_summary([{"role": "user", "content": "hello"}])
        >>> summary.startswith("Summary of conversation:")
        True
        """
        active_messages = self.messages if messages is None else messages
        transcript = []
        for message in active_messages:
            transcript.append(f"{message['role']}: {message.get('content', '')}")
        summary_lines = transcript[:5]
        summary_body = "\n".join(summary_lines) if summary_lines else "No messages yet."
        return f"Summary of conversation:\n{summary_body}"

    def provider_settings(self):
        """
        Return the API settings for the selected provider.

        >>> Chat("groq").provider_settings()["model"]
        'openai/gpt-oss-120b'
        >>> Chat("google").provider_settings()["model"]
        'google/gemini-3.1-pro-preview'
        """
        config = PROVIDER_CONFIGS[self.provider]
        return {
            "api_url": os.environ.get(config["api_base_env"], config["api_url"]),
            "api_key": os.environ.get(config["api_key_env"]),
            "model": config["model"],
        }

    def has_provider_credentials(self):
        """
        Return True when the configured provider has an API key available.

        >>> Chat("groq").has_provider_credentials()
        False
        """
        return bool(self.provider_settings()["api_key"])

    def tool_schemas(self):
        """
        Return the tool schemas exposed to the language model.

        >>> len(Chat().tool_schemas()) >= 10
        True
        """
        return [tool["spec"] for tool in self.tools.values()]

    def load_agents_file(self):
        """
        Load AGENTS.md into the conversation using the cat tool when it exists.

        >>> import os, tempfile
        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     old_cwd = os.getcwd()
        ...     os.chdir(tmpdir)
        ...     _ = os.mkdir(".git")
        ...     _ = open("AGENTS.md", "w", encoding="utf-8").write("Be careful.")
        ...     chat = Chat()
        ...     loaded = chat.load_agents_file()
        ...     os.chdir(old_cwd)
        ...     loaded and "AGENTS.md" in chat.messages[0]["content"]
        True
        """
        if not os.path.isfile("AGENTS.md"):
            return False

        result = self.tools["cat"]["runner"]("AGENTS.md")
        self._append_tool_message("cat", ["AGENTS.md"], result)
        self.messages.append(
            {
                "role": "system",
                "content": "Follow the repository instructions from AGENTS.md:\n" + result,
            }
        )
        return True

    def _manual_args_to_kwargs(self, command, args):
        """
        Convert manual slash-command arguments into keyword arguments.

        >>> chat = Chat()
        >>> chat._manual_args_to_kwargs("ls", [])
        {'path': '.'}
        >>> chat._manual_args_to_kwargs("grep", ["def", "tools/*.py"])
        {'pattern': 'def', 'path_glob': 'tools/*.py'}
        >>> kwargs = chat._manual_args_to_kwargs(
        ...     "write_files",
        ...     ['[{"path":"a.txt","contents":"x"}]', 'msg'],
        ... )
        >>> kwargs["commit_message"]
        'msg'
        """
        if command == "ls":
            if len(args) > 1:
                return None
            return {"path": args[0] if args else "."}
        if command == "write_files":
            if len(args) != 2:
                return None
            return {"files": json.loads(args[0]), "commit_message": args[1]}

        argument_names = self.tools[command]["manual_arguments"]
        if len(args) != len(argument_names):
            return None
        return dict(zip(argument_names, args))

    def execute_tool_call(self, tool_call):
        """
        Parse and execute a single tool call.

        >>> chat = Chat()
        >>> tool_call = chat._make_tool_call("calculate", {"expression": "2 + 2"})
        >>> chat.execute_tool_call(tool_call)[1]
        '{"result": 4}'
        """
        function_info = tool_call["function"]
        function_name = function_info["name"]
        function_to_call = self.tools[function_name]["runner"]
        function_args = json.loads(function_info["arguments"])
        function_response = function_to_call(**function_args)
        arg_values = [str(value) for value in function_args.values()]
        return function_name, function_response, arg_values

    def _make_tool_call(self, name, arguments):
        """
        Create a local tool-call payload in the tool-calling shape.

        >>> chat = Chat()
        >>> chat._make_tool_call("ls", {"path": ".github"})["function"]["arguments"]
        '{"path": ".github"}'
        """
        return {
            "id": f"call_{name}",
            "type": "function",
            "function": {
                "name": name,
                "arguments": json.dumps(arguments),
            },
        }

    def run_manual_command(self, line: str) -> str:
        """
        Execute a slash command directly without calling the model.

        >>> chat = Chat()
        >>> isinstance(chat.run_manual_command("/ls"), str)
        True
        >>> chat.run_manual_command("/doesnotexist")
        "Error: unknown command 'doesnotexist'"
        """
        parts = shlex.split(line.strip())
        if not parts or not parts[0].startswith("/"):
            return "Error: invalid command"

        command = parts[0][1:]
        args = parts[1:]

        if command not in self.tools:
            return f"Error: unknown command '{command}'"

        try:
            kwargs = self._manual_args_to_kwargs(command, args)
        except json.JSONDecodeError:
            return f"Error: invalid JSON arguments for {command}"
        if kwargs is None:
            return self._wrong_argument_error(command)

        tool_call = self._make_tool_call(command, kwargs)
        self._debug_print(command, args)
        executed_command, result, executed_args = self.execute_tool_call(tool_call)
        self._append_tool_message(executed_command, executed_args, result)
        return result

    def _wrong_argument_error(self, command):
        """
        Return the error message for an invalid manual tool invocation.

        >>> chat = Chat()
        >>> chat._wrong_argument_error("cat")
        'Error: cat requires 1 argument'
        """
        counts = {
            "ls": "Error: ls accepts at most 1 argument",
            "cat": "Error: cat requires 1 argument",
            "grep": "Error: grep requires 2 arguments",
            "calculate": "Error: calculate requires 1 argument",
            "compact": "Error: compact accepts 0 arguments",
            "doctests": "Error: doctests requires 1 argument",
            "write_file": "Error: write_file requires 3 arguments",
            "write_files": "Error: write_files requires 2 arguments",
            "rm": "Error: rm requires 1 argument",
            "pip_install": "Error: pip_install requires 1 argument",
        }
        return counts[command]

    def _append_tool_message(self, command, args, result, tool_call_id=None):
        """
        Store a tool result in the current conversation.

        >>> chat = Chat()
        >>> chat._append_tool_message("ls", [".github"], "workflows")
        >>> chat.messages[-1]["role"]
        'tool'
        """
        message = {
            "role": "tool",
            "name": command,
            "content": f"/{command}" + (f" {' '.join(args)}" if args else "") + f"\n{result}",
        }
        if tool_call_id is not None:
            message["tool_call_id"] = tool_call_id
            message["content"] = str(result)
        self.messages.append(message)

    def _auto_choose_tool(self, message: str):
        """
        Build a deterministic tool call for common local project questions.

        >>> chat = Chat()
        >>> chat._auto_choose_tool("what files are in the .github folder?")["function"]["name"]
        'ls'
        >>> chat._auto_choose_tool("show me README.md")["function"]["name"]
        'cat'
        >>> chat._auto_choose_tool("find def in tools/*.py")["function"]["name"]
        'grep'
        >>> chat._auto_choose_tool("what is 2 + 2?")["function"]["name"]
        'calculate'
        """
        text = message.strip()
        lowered = text.lower()

        if "what files are in" in lowered and " folder" in lowered:
            fragment = text.split("what files are in", 1)[1].split("folder", 1)[0]
            candidate = fragment.strip().strip("?").strip("`'\" ")
            if candidate.lower().startswith("the "):
                candidate = candidate[4:]
            return self._make_tool_call("ls", {"path": candidate})

        if lowered.startswith("show me ") or lowered.startswith("open "):
            filename = text.split(maxsplit=2)[-1].strip()
            return self._make_tool_call("cat", {"path": filename})

        if lowered.startswith("find ") and " in " in text:
            body = text[5:]
            pattern, path_glob = body.split(" in ", 1)
            return self._make_tool_call(
                "grep",
                {"pattern": pattern.strip(), "path_glob": path_glob.strip()},
            )

        if lowered.startswith("what is "):
            expression = text[8:].rstrip("?").strip()
            if any(character.isdigit() for character in expression):
                return self._make_tool_call("calculate", {"expression": expression})
        return None

    def _render_tool_response(self, command, tool_result):
        """
        Convert a raw tool result into the assistant's user-facing response.

        >>> chat = Chat()
        >>> chat._render_tool_response("ls", "a\\nb")
        'The files in that folder are: a, b.'
        >>> chat._render_tool_response("grep", "")
        'No lines matched that pattern.'
        """
        if command == "ls":
            if tool_result.strip():
                items = [line.strip() for line in tool_result.splitlines() if line.strip()]
                if len(items) == 1:
                    return f"The only file in that folder is {items[0]}."
                return "The files in that folder are: " + ", ".join(items) + "."
            return "That folder appears to be empty."

        if command == "calculate":
            try:
                parsed = json.loads(tool_result)
            except json.JSONDecodeError:
                return tool_result
            if "result" in parsed:
                return str(parsed["result"])
            return f"Error: {parsed.get('error', 'Unknown calculation error')}"

        if command == "grep":
            return tool_result if tool_result else "No lines matched that pattern."

        return tool_result

    def _provider_messages(self):
        """
        Convert the stored transcript into provider-compatible messages.

        >>> chat = Chat()
        >>> chat.messages = [{"role": "tool", "content": "/ls\\nworkflows"}]
        >>> chat._provider_messages()[0]["role"]
        'assistant'
        """
        provider_messages = []
        for message in self.messages:
            role = message["role"]
            if role == "tool" and "tool_call_id" not in message:
                provider_messages.append(
                    {
                        "role": "assistant",
                        "content": "Manual tool output:\n" + message["content"],
                    }
                )
                continue

            entry = {"role": role, "content": message.get("content", "")}
            if "tool_calls" in message:
                entry["tool_calls"] = message["tool_calls"]
            if "tool_call_id" in message:
                entry["tool_call_id"] = message["tool_call_id"]
            if "name" in message and role == "tool":
                entry["name"] = message["name"]
            provider_messages.append(entry)
        return provider_messages

    def _provider_headers(self):
        """
        Return the request headers for the selected provider.

        >>> headers = Chat("openai")._provider_headers()
        >>> headers["Content-Type"]
        'application/json'
        """
        settings = self.provider_settings()
        headers = {"Content-Type": "application/json"}
        if settings["api_key"]:
            headers["Authorization"] = f"Bearer {settings['api_key']}"
        if self.provider != "groq":
            headers["HTTP-Referer"] = "https://github.com/MiaUrosevic/Lab-more-project"
            headers["X-Title"] = "lab-more-project-chat"
        return headers

    def _provider_payload(self):
        """
        Build the provider request payload for the current conversation.

        >>> payload = Chat("anthropic")._provider_payload()
        >>> payload["model"]
        'anthropic/claude-opus-4.6'
        """
        settings = self.provider_settings()
        return {
            "model": settings["model"],
            "messages": self._provider_messages(),
            "tools": self.tool_schemas(),
            "tool_choice": "auto",
            "temperature": 0.2,
            "max_tokens": 4096,
        }

    def _provider_request(self):
        """
        Send a chat completion request to the configured provider.

        >>> chat = Chat()
        >>> isinstance(chat._provider_payload(), dict)
        True
        """
        stub_response = os.environ.get("CHAT_PROVIDER_STUB_RESPONSE")
        if stub_response:
            return json.loads(stub_response)

        settings = self.provider_settings()
        response = requests.post(
            settings["api_url"],
            headers=self._provider_headers(),
            json=self._provider_payload(),
            timeout=60,
        )
        response.raise_for_status()
        return response.json()

    def _doctest_status(self, command, result):
        """
        Return the detected doctest status for a tool result.

        >>> chat = Chat()
        >>> chat._doctest_status("doctests", "Test passed.")
        'passed'
        >>> chat._doctest_status("write_file", "***Test Failed*** 1 failures.")
        'failed'
        """
        if command not in {"doctests", "write_file", "write_files"}:
            return None
        if "***Test Failed***" in result:
            return "failed"
        if "Test passed." in result:
            return "passed"
        return None

    def _update_doctest_retry_state(self, command, result):
        """
        Track whether the next provider turn must continue fixing doctests.

        >>> chat = Chat()
        >>> chat._update_doctest_retry_state("doctests", "***Test Failed***")
        >>> chat.pending_doctest_retry
        True
        >>> chat._update_doctest_retry_state("doctests", "Test passed.")
        >>> chat.pending_doctest_retry
        False
        """
        status = self._doctest_status(command, result)
        if status == "failed":
            self.pending_doctest_retry = True
        elif status == "passed":
            self.pending_doctest_retry = False

    def _send_with_provider(self):
        """
        Run the provider loop until a final assistant response is returned.

        >>> chat = Chat()
        >>> chat.messages = [{"role": "user", "content": "hello"}]
        >>> isinstance(chat._provider_messages(), list)
        True
        """
        for _ in range(8):
            response_data = self._provider_request()
            response_message = response_data["choices"][0]["message"]
            tool_calls = response_message.get("tool_calls") or []

            if tool_calls:
                self.messages.append(
                    {
                        "role": "assistant",
                        "content": response_message.get("content") or "",
                        "tool_calls": tool_calls,
                    }
                )
                for tool_call in tool_calls:
                    command, tool_result, arg_values = self.execute_tool_call(tool_call)
                    self._debug_print(command, arg_values)
                    self._append_tool_message(
                        command,
                        arg_values,
                        tool_result,
                        tool_call_id=tool_call["id"],
                    )
                    self._update_doctest_retry_state(command, tool_result)
                continue

            if self.pending_doctest_retry:
                self.messages.append(
                    {
                        "role": "system",
                        "content": (
                            "Doctests are still failing. Use write_file, write_files, rm, "
                            "and doctests again until the doctests pass before answering."
                        ),
                    }
                )
                continue

            assistant_text = response_message.get("content") or ""
            self.messages.append({"role": "assistant", "content": assistant_text})
            return assistant_text

        return "Error: provider exceeded the maximum number of tool-calling turns"

    def _send_with_deterministic_router(self, message):
        """
        Route the message through the deterministic local tool logic.

        >>> chat = Chat()
        >>> chat._send_with_deterministic_router("what is 5 + 7?")
        '12'
        """
        tool_call = self._auto_choose_tool(message)

        if tool_call is not None:
            self.messages.append({"role": "assistant", "tool_calls": [tool_call]})
            command, tool_result, arg_values = self.execute_tool_call(tool_call)
            self._debug_print(command, arg_values)
            self._append_tool_message(command, arg_values, tool_result)
            rendered = self._render_tool_response(command, tool_result)
            self.messages.append({"role": "assistant", "content": rendered})
            return rendered

        fallback = (
            "I could not automatically determine the right tool for that request yet. "
            "Try a slash command like /ls, /cat, /grep, /calculate, /doctests, "
            "/write_file, /write_files, /rm, /pip_install, or /compact."
        )
        self.messages.append({"role": "assistant", "content": fallback})
        return fallback

    def send_message(self, message: str) -> str:
        """
        Send a message and return a response.

        This version uses deterministic local routing by default and upgrades to
        real provider-backed tool calling when the selected provider is configured
        with API credentials.

        >>> chat = Chat()
        >>> isinstance(chat.send_message("what files are in the .github folder?"), str)
        True
        """
        self.messages.append({"role": "user", "content": message})

        if self.has_provider_credentials():
            try:
                return self._send_with_provider()
            except requests.RequestException as error:
                warning = f"Provider request failed: {error}. Falling back to local routing."
                self.messages.append({"role": "assistant", "content": warning})

        return self._send_with_deterministic_router(message)


def initialize_chat(chat):
    """
    Validate startup requirements and preload AGENTS.md when present.

    >>> chat = Chat()
    >>> error = initialize_chat(chat)
    >>> error in {
    ...     None,
    ...     'Error: docchat must be run from a directory containing a .git folder',
    ... }
    True
    """
    error = validate_repo_startup()
    if error is not None:
        return error
    chat.load_agents_file()
    return None


def parse_args(argv=None):
    """
    Parse command-line arguments.

    >>> args = parse_args(["hello"])
    >>> args.message
    'hello'
    >>> args = parse_args(["--debug", "--provider", "groq", "hi"])
    >>> (args.debug, args.provider, args.message)
    (True, 'groq', 'hi')
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("message", nargs="?", help="Optional one-shot message")
    parser.add_argument("--debug", action="store_true", help="Print tool-use calls")
    parser.add_argument(
        "--provider",
        default="groq",
        choices=["groq", "openai", "anthropic", "google"],
        help="Select the LLM provider",
    )
    return parser.parse_args(argv)


def repl(chat: Chat):
    """
    Run the interactive REPL until interrupted.
    """
    configure_readline(chat.tools.keys())
    while True:
        try:
            line = input("chat> ")
            if not line.strip():
                continue
            if line[0] == "/":
                print(chat.run_manual_command(line))
            else:
                print(chat.send_message(line))
        except KeyboardInterrupt:
            print()
            break
        except EOFError:
            print()
            break


def main(argv=None):
    """
    Run the CLI program.

    >>> main(["what is 2 + 2?"]) is None
    4
    True
    """
    args = parse_args(argv)
    chat = Chat(provider=args.provider, debug=args.debug)
    startup_error = initialize_chat(chat)
    if startup_error is not None:
        print(startup_error)
        return None

    if args.message:
        print(chat.send_message(args.message))
    else:
        repl(chat)


if __name__ == "__main__":
    main()
