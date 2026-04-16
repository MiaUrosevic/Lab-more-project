"""
The grep tool searches matching project files for lines that match a regex.
"""

import glob
import re
from chat import is_path_safe


def run_grep(pattern, path_glob):
    """
    Search matching files for lines that match a regex.

    >>> run_grep("hello", "..")
    'Error: unsafe path'
    >>> isinstance(run_grep("def", "tools/*.py"), str)
    True
    >>> "def run_ls" in run_grep("def run_ls", "tools/*.py")
    True
    >>> run_grep("^this_should_not_match_anything_12345$", "tools/*.py")
    ''
    """
    if not is_path_safe(path_glob):
        return "Error: unsafe path"

    out = []
    for filename in sorted(glob.glob(path_glob)):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                for line in f:
                    if re.search(pattern, line):
                        out.append(line.rstrip("\n"))
        except Exception:
            continue

    return "\n".join(out)
