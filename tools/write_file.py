"""
The write_file tool writes or patches one file and delegates the work to write_files.
"""

from tools.write_files import run_write_files


TOOL_SPEC = {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": (
            "Write or patch one file, commit it, and run doctests if it is a "
            "Python file."
        ),
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
                "diff": {
                    "type": "string",
                    "description": "A unified-diff style patch to apply to the file.",
                },
                "commit_message": {
                    "type": "string",
                    "description": "The git commit message suffix to use after [docchat].",
                },
            },
            "required": ["path", "commit_message"],
            "anyOf": [
                {"required": ["contents"]},
                {"required": ["diff"]},
            ],
        },
    },
}


def run_write_file(path, commit_message, contents=None, diff=None):
    """
    Write or patch one file by delegating to the multi-file implementation.

    >>> result = run_write_file("..", "bad", contents="hello")
    >>> result
    'Error: unsafe path'
    """
    file_info = {"path": path}
    if contents is not None:
        file_info["contents"] = contents
    if diff is not None:
        file_info["diff"] = diff
    return run_write_files(
        [file_info],
        commit_message,
    )
