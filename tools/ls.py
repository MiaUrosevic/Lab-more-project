"""
The ls tool lists files in the current directory or in a specified relative directory.
"""

import glob
import os
from chat import is_path_safe


def run_ls(path="."):
    """
    List files in the current folder or a specified relative folder.

    # super cheesy and doesn't help me understand what
    # your program does; just actually list the 
    # contents of the output
    >>> isinstance(run_ls("."), str)
    True
    >>> run_ls("..")
    'Error: unsafe path'
    """
    if not is_path_safe(path):
        return "Error: unsafe path"

    pattern = os.path.join(path, "*") if path != "." else "*"
    matches = sorted(glob.glob(pattern))

    cleaned = [os.path.basename(m) for m in matches]
    return "\n".join(cleaned)
