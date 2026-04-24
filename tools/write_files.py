"""
The write_files tool writes multiple files, commits them, and runs doctests on Python files.
"""

import os

from tools.doctests import run_doctests
from tools.repo_utils import is_repo_path_safe, stage_and_commit


TOOL_SPEC = {
    "type": "function",
    "function": {
        "name": "write_files",
        "description": "Write multiple files, commit them, and run doctests for Python files.",
        "parameters": {
            "type": "object",
            "properties": {
                "files": {
                    "type": "array",
                    "description": "A list of file objects containing path and contents keys.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "contents": {"type": "string"},
                        },
                        "required": ["path", "contents"],
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


def run_write_files(files, commit_message):
    """
    Write files, create a git commit, and run doctests on Python files.

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
    """
    paths = []
    python_outputs = []

    for file_info in files:
        path = file_info["path"]
        contents = file_info["contents"]
        if not is_repo_path_safe(path):
            return "Error: unsafe path"
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
