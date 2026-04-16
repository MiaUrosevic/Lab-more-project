"""
The cat tool reads a text file in the current project and returns its contents.
"""

from chat import is_path_safe


def run_cat(path):
    """
    Read and return the contents of a text file.

    >>> run_cat("..")
    'Error: unsafe path'
    >>> "Error:" in run_cat("definitely_not_a_real_file_123.txt")
    True
    >>> "Main entry point" in run_cat("chat.py")
    True
    """
    if not is_path_safe(path):
        return "Error: unsafe path"

    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error: {e}"
