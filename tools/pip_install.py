"""
The pip_install tool installs a Python package with pip3.
"""

import subprocess


TOOL_SPEC = {
    "type": "function",
    "function": {
        "name": "pip_install",
        "description": "Install one Python library using pip3.",
        "parameters": {
            "type": "object",
            "properties": {
                "library_name": {
                    "type": "string",
                    "description": "The package name to install with pip3.",
                }
            },
            "required": ["library_name"],
        },
    },
}


def run_pip_install(library_name):
    """
    Install a Python package with pip3 and return the command output.

    >>> from unittest.mock import patch
    >>> completed = subprocess.CompletedProcess(["pip3"], 0, "ok", "")
    >>> with patch("subprocess.run", return_value=completed):
    ...     run_pip_install("requests")
    'ok'
    """
    result = subprocess.run(
        ["pip3", "install", library_name],
        capture_output=True,
        text=True,
        check=False,
    )
    return (result.stdout + result.stderr).strip()
