"""
The write_files tool writes or patches multiple files, commits them, and runs doctests.
"""

import os

from tools.doctests import run_doctests
from tools.repo_utils import is_repo_path_safe, stage_and_commit


TOOL_SPEC = {
    "type": "function",
    "function": {
        "name": "write_files",
        "description": (
            "Write or patch multiple files, commit them, and run doctests for "
            "Python files."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "files": {
                    "type": "array",
                    "description": (
                        "A list of file objects containing a path and either "
                        "contents or diff."
                    ),
                    "items": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "contents": {"type": "string"},
                            "diff": {"type": "string"},
                        },
                        "required": ["path"],
                        "anyOf": [
                            {"required": ["contents"]},
                            {"required": ["diff"]},
                        ],
                    },
                },
                "commit_message": {
                    "type": "string",
                    "description": "The git commit message suffix to use after [docchat].",
                },
            },
            "required": ["files", "commit_message"],
        },
    },
}


def _diff_line_text(line):
    """
    Return the content portion of a diff line with a trailing newline restored.

    >>> _diff_line_text("-hello")
    'hello\\n'
    >>> _diff_line_text("+world")
    'world\\n'
    """
    return line[1:] + "\n"


def _parse_diff_hunks(diff_text):
    """
    Parse a simple unified diff into hunks without trusting line numbers.

    >>> hunks = _parse_diff_hunks("@@\\n-old\\n+new")
    >>> hunks
    [[('-old', 'old\\n'), ('+new', 'new\\n')]]
    >>> _parse_diff_hunks("")
    []
    """
    hunks = []
    current_hunk = []

    for raw_line in diff_text.splitlines():
        if raw_line.startswith(("---", "+++", "diff --git", "index ")):
            continue
        if raw_line.startswith("@@"):
            if current_hunk:
                hunks.append(current_hunk)
                current_hunk = []
            continue
        if raw_line.startswith((" ", "+", "-")):
            current_hunk.append((raw_line, _diff_line_text(raw_line)))

    if current_hunk:
        hunks.append(current_hunk)
    return hunks


def _find_sequence(lines, sequence, start_index=0):
    """
    Find the first matching slice of lines at or after the given start index.

    >>> _find_sequence(["a\\n", "b\\n", "c\\n"], ["b\\n"])
    1
    >>> _find_sequence(["a\\n", "b\\n"], ["x\\n"]) is None
    True
    """
    if not sequence:
        return start_index
    last_start = len(lines) - len(sequence) + 1
    for index in range(start_index, max(last_start, start_index)):
        if lines[index:index + len(sequence)] == sequence:
            return index
    return None


def apply_diff_to_text(original_text, diff_text):
    """
    Apply a simple fuzzy unified diff to text without relying on hunk line numbers.

    >>> apply_diff_to_text("hello\\nworld\\n", "@@\\n-hello\\n+hi")
    'hi\\nworld\\n'
    >>> apply_diff_to_text("alpha\\n", "@@\\n alpha\\n+beta")
    'alpha\\nbeta\\n'
    >>> apply_diff_to_text("alpha\\n", "@@\\n-beta\\n+gamma")
    Traceback (most recent call last):
    ...
    ValueError: Could not apply diff hunk
    """
    lines = original_text.splitlines(keepends=True)
    cursor = 0

    for hunk in _parse_diff_hunks(diff_text):
        old_lines = [text for raw, text in hunk if raw.startswith((" ", "-"))]
        new_lines = [text for raw, text in hunk if raw.startswith((" ", "+"))]
        start = _find_sequence(lines, old_lines, cursor)
        if start is None:
            raise ValueError("Could not apply diff hunk")
        end = start + len(old_lines)
        lines[start:end] = new_lines
        cursor = start + len(new_lines)

    return "".join(lines)


def _resolve_file_contents(file_info):
    """
    Build the final file contents from either literal text or a patch diff.

    >>> _resolve_file_contents({"contents": "hello"})
    'hello'
    >>> _resolve_file_contents({"path": "demo.txt", "diff": "@@\\n+hello"})
    'hello\\n'
    >>> _resolve_file_contents({})
    Traceback (most recent call last):
    ...
    ValueError: File entry must include contents or diff
    """
    if "contents" in file_info:
        return file_info["contents"]
    if "diff" in file_info:
        path = file_info["path"]
        original_text = ""
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as file_handle:
                original_text = file_handle.read()
        return apply_diff_to_text(original_text, file_info["diff"])
    raise ValueError("File entry must include contents or diff")


def run_write_files(files, commit_message):
    """
    Write or patch files, create a git commit, and run doctests on Python files.

    >>> import os, tempfile
    >>> from git import Repo
    >>> with tempfile.TemporaryDirectory() as tmpdir:
    ...     old_cwd = os.getcwd()
    ...     os.chdir(tmpdir)
    ...     _ = Repo.init(tmpdir)
    ...     result = run_write_files(
    ...         [{"path": "demo.txt", "contents": "hello"}],
    ...         "create demo",
    ...     )
    ...     file_text = open("demo.txt", "r", encoding="utf-8").read()
    ...     os.chdir(old_cwd)
    ...     "Committed" in result and file_text == "hello"
    True
    >>> run_write_files([{"path": "..", "contents": "nope"}], "bad")
    'Error: unsafe path'
    >>> import os, tempfile
    >>> from git import Repo
    >>> with tempfile.TemporaryDirectory() as tmpdir:
    ...     old_cwd = os.getcwd()
    ...     os.chdir(tmpdir)
    ...     _ = Repo.init(tmpdir)
    ...     _ = open("demo.txt", "w", encoding="utf-8").write("hello\\nworld\\n")
    ...     result = run_write_files(
    ...         [{"path": "demo.txt", "diff": "@@\\n-hello\\n+hi"}],
    ...         "patch demo",
    ...     )
    ...     file_text = open("demo.txt", "r", encoding="utf-8").read()
    ...     os.chdir(old_cwd)
    ...     "Committed" in result and file_text == "hi\\nworld\\n"
    True
    """
    paths = []
    python_outputs = []

    for file_info in files:
        path = file_info["path"]
        if not is_repo_path_safe(path):
            return "Error: unsafe path"
        try:
            contents = _resolve_file_contents(file_info)
        except ValueError as error:
            return f"Error: {error}"
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as file_handle:
            file_handle.write(contents)
        paths.append(path)

    commit = stage_and_commit(paths, commit_message)

    for path in paths:
        if path.endswith(".py"):
            python_outputs.append(f"$ doctests {path}\n{run_doctests(path)}")

    output_lines = [
        f"Committed {commit.hexsha[:7]} with message: [docchat] {commit_message}",
    ]
    if python_outputs:
        output_lines.extend(python_outputs)
    return "\n".join(output_lines)
