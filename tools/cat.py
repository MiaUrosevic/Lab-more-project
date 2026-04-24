"""
The cat tool reads a text file in the current project and returns its contents.
"""

from chat import is_path_safe


def run_cat(path):
    """
    Read and return the contents of a text file.

    >>> import os, shutil
    >>> test_dir = "__doctest_cat_tmp__"
    >>> shutil.rmtree(test_dir, ignore_errors=True)
    >>> os.makedirs(test_dir)
    >>> path = os.path.join(test_dir, "hello.txt")
    >>> _ = open(path, "w", encoding="utf-8").write("hello\\nworld")
    >>> run_cat(path)
    'hello\\nworld'
    >>> shutil.rmtree(test_dir)

    >>> run_cat("..")
    'Error: unsafe path'

    >>> run_cat("definitely_not_a_real_file_123.txt").startswith("Error:")
    True
    """
    if not is_path_safe(path):
        return "Error: unsafe path"

    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error: {e}"
