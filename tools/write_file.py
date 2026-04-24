"""
The write_file tool writes one file and delegates the work to write_files.
"""

from tools.write_files import run_write_files


TOOL_SPEC = {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": "Write one file, commit it, and run doctests if it is a Python file.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The relative path of the file to write.",
                },
                "contents": {
                    "type": "string",
                    "description": "The UTF-8 file contents to write.",
                },
                "commit_message": {
                    "type": "string",
                    "description": "The git commit message suffix to use after [docchat].",
                },
            },
            "required": ["path", "contents", "commit_message"],
        },
    },
}


def run_write_file(path, contents, commit_message):
    """
    Write one file by delegating to the multi-file implementation.

    >>> result = run_write_file("..", "hello", "bad")
    >>> result
    'Error: unsafe path'
    """
    return run_write_files(
        [{"path": path, "contents": contents}],
        commit_message,
    )
