"""
The rm tool deletes safe relative files matched by a glob and commits the removal.
"""

import glob
import os

from tools.repo_utils import is_repo_path_safe, open_repo


TOOL_SPEC = {
    "type": "function",
    "function": {
        "name": "rm",
        "description": (
            "Delete one or more relative files matched by a glob and commit the "
            "removal."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "A safe relative path or glob describing files to remove.",
                }
            },
            "required": ["path"],
        },
    },
}


def run_rm(path):
    """
    Remove files matched by a safe relative glob and commit the deletion.

    >>> run_rm("..")
    'Error: unsafe path'
    >>> run_rm("definitely_not_here.txt").startswith("Error: no files matched")
    True
    """
    if not is_repo_path_safe(path):
        return "Error: unsafe path"

    matches = sorted(glob.glob(path))
    if not matches:
        return f"Error: no files matched {path}"

    safe_matches = []
    for match in matches:
        if not is_repo_path_safe(match):
            return "Error: unsafe path"
        if os.path.isfile(match):
            os.remove(match)
            safe_matches.append(match)

    if not safe_matches:
        return f"Error: no files matched {path}"

    repo = open_repo()
    repo.git.add("--", *safe_matches)
    commit_message = f"[docchat] rm {path}"
    commit = repo.index.commit(commit_message)
    return f"Committed {commit.hexsha[:7]} with message: {commit_message}"
