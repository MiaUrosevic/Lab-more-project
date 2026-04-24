"""
The doctests tool runs verbose doctests for a relative project file.
"""

import subprocess
import sys

from tools.repo_utils import is_repo_path_safe


TOOL_SPEC = {
    "type": "function",
    "function": {
        "name": "doctests",
        "description": "Run verbose doctests for a relative file and return the output.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The relative path of the file whose doctests should run.",
                }
            },
            "required": ["path"],
        },
    },
}


def run_doctests(path):
    """
    Run doctests with verbose output for a safe relative path.

    >>> run_doctests("..")
    'Error: unsafe path'
    >>> output = run_doctests("tools/calculate.py")
    >>> "Test passed." in output
    True
    """
    if not is_repo_path_safe(path):
        return "Error: unsafe path"

    result = subprocess.run(
        [sys.executable, "-m", "doctest", "-v", path],
        capture_output=True,
        text=True,
        check=False,
    )
    return (result.stdout + result.stderr).strip()
