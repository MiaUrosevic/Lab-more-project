"""
The ls tool lists files in the current directory or in a specified relative directory.
"""

import glob
import os
from chat import is_path_safe


def run_ls(path="."):
    """
    List files in the current folder or a specified relative folder.

    >>> import tempfile
    >>> with tempfile.TemporaryDirectory() as tmp:
    ...     open(os.path.join(tmp, "b.txt"), "w").close()
    ...     open(os.path.join(tmp, "a.txt"), "w").close()
    ...     run_ls(tmp)
    'a.txt\\nb.txt'

    >>> run_ls("..")
    'Error: unsafe path'
    """
    if not is_path_safe(path):
        return "Error: unsafe path"

    pattern = os.path.join(path, "*") if path != "." else "*"
    matches = sorted(glob.glob(pattern))

    cleaned = [os.path.basename(m) for m in matches]
    return "\n".join(cleaned)
