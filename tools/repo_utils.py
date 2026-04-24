"""
Shared repository helpers for file-writing and git-commit tools.
"""

import os

from chat import is_path_safe
from git import Repo


def is_repo_path_safe(path):
    """
    Return True when the path is relative, non-traversing, and outside `.git`.

    >>> is_repo_path_safe("chat.py")
    True
    >>> is_repo_path_safe(".git/config")
    False
    >>> is_repo_path_safe("../secret.txt")
    False
    """
    if not is_path_safe(path):
        return False
    normalized = path.replace("\\", "/")
    return normalized != ".git" and not normalized.startswith(".git/")


def open_repo():
    """
    Open the git repository rooted at the current working directory.

    >>> import os, tempfile
    >>> from git import Repo
    >>> with tempfile.TemporaryDirectory() as tmpdir:
    ...     old_cwd = os.getcwd()
    ...     os.chdir(tmpdir)
    ...     _ = Repo.init(tmpdir)
    ...     repo = open_repo()
    ...     os.chdir(old_cwd)
    ...     os.path.samefile(repo.working_tree_dir, tmpdir)
    True
    """
    return Repo(os.getcwd(), search_parent_directories=False)


def stage_and_commit(paths, commit_message):
    """
    Stage the given paths and create a `[docchat]` commit.

    >>> import os, tempfile
    >>> from git import Repo
    >>> with tempfile.TemporaryDirectory() as tmpdir:
    ...     old_cwd = os.getcwd()
    ...     os.chdir(tmpdir)
    ...     repo = Repo.init(tmpdir)
    ...     _ = open("demo.txt", "w", encoding="utf-8").write("hello")
    ...     commit = stage_and_commit(["demo.txt"], "add demo")
    ...     os.chdir(old_cwd)
    ...     commit.message.strip()
    '[docchat] add demo'
    """
    repo = open_repo()
    repo.index.add(paths)
    return repo.index.commit(f"[docchat] {commit_message}")
