"""
This file defines the Chat class, path safety checks, the CLI interface,
and the interactive REPL for talking to local project files with tools.
"""

import argparse
import os
import shlex
from pathlib import PurePath


# very weird to include this function here
# and it causes your imports elsewhere to behave
# weirdly as well;
# this needs to be fixed for next project;
# easy way to do it is move this function to its
# own file in the tools folder,
# then all of those tools important this function;
# then you can move your imports below to the top
# level where they belong
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
    """
    if not path:
        return True
    if os.path.isabs(path):
        return False
    return ".." not in PurePath(path).parts


class Chat:
    """
    A Chat manages a local file-aware conversation session with manual and automatic tool use.

    It stores messages, supports slash commands like /ls and /cat, and can automatically
    choose a tool for simple file-related questions. The design is intentionally simple so
    it is easy to test and extend with real provider API calls later.


    # these test cases do actually test anything
    """

    def __init__(self, provider="groq", debug=False):
        """
        Initialize a new Chat session.
        """
        # you don't actually do anything with this
        # provider information ever
        self.provider = provider
        self.debug = debug
        self.messages = []
        self.tools = {
            "ls": self._tool_ls,
            "cat": self._tool_cat,
            "grep": self._tool_grep,
            "calculate": self._tool_calculate,
            "compact": self._tool_compact,
        }

    def _debug_print(self, command, args):
        """
        Print a tool debug line if debug mode is enabled.

        # this is not a good test case;
        # you should actually show me the output of the function
        #
        >>> chat = Chat(debug=False)
        >>> chat._debug_print("ls", [".github"]) is None

        better is:
        >>> chat._debug_print("ls", [".github"])
        and add correct output here
        """
        if self.debug:
            print(f"[tool] /{command}" + (f" {' '.join(args)}" if args else ""))

    def _tool_ls(self, *args):
        """
        Run the ls tool.
        """
        # again, this is super janky;
        # making the fix above with the safe path function
        # will let you not have these janky methods;
        # fix this for next submission
        from tools.ls import run_ls
        path = args[0] if args else "."
        return run_ls(path)

    def _tool_cat(self, *args):
        """
        Run the cat tool.
        """
        from tools.cat import run_cat
        if len(args) != 1:
            return "Error: cat requires 1 argument"
        return run_cat(args[0])

    def _tool_grep(self, *args):
        """
        Run the grep tool.
        """
        from tools.grep import run_grep
        if len(args) != 2:
            return "Error: grep requires 2 arguments"
        return run_grep(args[0], args[1])

    def _tool_calculate(self, *args):
        """
        Run the calculate tool.
        """
        from tools.calculate import run_calculate
        if len(args) != 1:
            return "Error: calculate requires 1 argument"
        return run_calculate(args[0])

    def _tool_compact(self, *args):
        """
        Run the compact tool.
        """
        from tools.compact import run_compact
        return run_compact(self)

    def run_manual_command(self, line: str) -> str:
        """
        Execute a slash command directly without calling the model.

        # not good test cases;
        # you need to actually show me the output of these functions

        >>> chat = Chat()
        >>> isinstance(chat.run_manual_command("/ls"), str)
        True
        >>> chat.run_manual_command("/doesnotexist")
        "Error: unknown command 'doesnotexist'"
        """
        parts = shlex.split(line.strip())
        command = parts[0][1:]
        args = parts[1:]

        if command not in self.tools:
            return f"Error: unknown command '{command}'"

        self._debug_print(command, args)
        result = self.tools[command](*args)
        self.messages.append(
            {
                "role": "tool",
                "content": f"/{command}" + (f" {' '.join(args)}" if args else "") + f"\n{result}",
            }
        )
        return result

    def send_message(self, message: str) -> str:
        """
        Send a message and return a response.

        This starter version uses deterministic automatic tool routing for common
        project questions so the required manual/automatic tool behavior can be tested
        reliably. You can later replace this with real provider API calls.

        >>> chat = Chat()
        >>> isinstance(chat.send_message("what files are in the .github folder?"), str)
        True
        """
        self.messages.append({"role": "user", "content": message})

        # this is not how tool use is supposed to work
        # you are supposed to let the LLM choose
        # which tool to call (like we did in class)
        # and not have to hard code certain patterns;
        # this needs to be fixed for the next project
        tool_call = self._auto_choose_tool(message)
        if tool_call is not None:
            command, args = tool_call
            self._debug_print(command, args)
            tool_result = self.tools[command](*args)
            self.messages.append(
                {
                    "role": "tool",
                    "content": f"/{command}" + (f" {' '.join(args)}" if args else "") +
                    f"\n{tool_result}"
                }
            )

            if command == "ls":
                if tool_result.strip():
                    items = [line.strip() for line in tool_result.splitlines() if line.strip()]
                    if len(items) == 1:
                        return f"The only file in that folder is {items[0]}."
                    return "The files in that folder are: " + ", ".join(items) + "."
                return "That folder appears to be empty."
            if command == "cat":
                return tool_result
            if command == "grep":
                return tool_result if tool_result else "No lines matched that pattern."
            if command == "calculate":
                return tool_result

        return (
            "I could not automatically determine the right tool for that request yet. "
            "Try a slash command like /ls, /cat, /grep, /calculate, or /compact."
        )


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
    while True:
        try:
            line = input("chat> ")
            if not line.strip():
                continue
            if line.startswith("/"):
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

    # your previous doctest was too complicated
    >>> main(["what is 2 + 2?"])
    4
    """
    args = parse_args(argv)
    chat = Chat(provider=args.provider, debug=args.debug)

    if args.message:
        print(chat.send_message(args.message))
    else:
        repl(chat)


if __name__ == "__main__":
    main()
