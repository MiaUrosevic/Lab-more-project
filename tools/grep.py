"""
The grep tool searches matching project files for lines that match a regex.
"""

import glob
import re
from chat import is_path_safe


def run_grep(pattern, path_glob):
    """
    Search matching files for lines that match a regex.

    >>> import os, shutil
    >>> test_dir = "__doctest_grep_tmp__"
    >>> shutil.rmtree(test_dir, ignore_errors=True)
    >>> os.makedirs(test_dir)
    >>> _ = open(os.path.join(test_dir, "a.txt"), "w", encoding="utf-8").write("hello world\\nfoo")
    >>> _ = open(os.path.join(test_dir, "b.txt"), "w", encoding="utf-8").write("bar\\nhello again")
    >>> run_grep("hello", os.path.join(test_dir, "*.txt"))
    'hello world\\nhello again'
    >>> shutil.rmtree(test_dir)

    >>> run_grep("hello", "..")
    'Error: unsafe path'

    >>> import os, shutil
    >>> test_dir = "__doctest_grep_tmp__"
    >>> shutil.rmtree(test_dir, ignore_errors=True)
    >>> os.makedirs(test_dir)
    >>> _ = open(os.path.join(test_dir, "a.txt"), "w", encoding="utf-8").write("nothing here")
    >>> run_grep("xyz", os.path.join(test_dir, "*.txt"))
    ''
    >>> shutil.rmtree(test_dir)
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
