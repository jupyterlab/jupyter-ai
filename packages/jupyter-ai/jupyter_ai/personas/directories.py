from pathlib import Path
from typing import Optional


def find_dot_dir(
    dir: str, dot_dir: str, root_dir: Optional[str] = None
) -> Optional[str]:
    """
    Find the nearest dot directory by traversing up from the given directory.

    Args:
        dir (str): The starting directory path
        dot_dir (str): The dot directory name to search for (e.g., '.jupyter', '.git')
        root_dir (Optional[str]): The root directory to stop searching at.
            If None, searches to filesystem root.

    Returns:
        str: The absolute path to the dot directory if found, None otherwise

    Raises:
        ValueError: If dir is not a directory
    """
    current_path = Path(dir).resolve()

    # Validate that the starting path is a directory
    if not current_path.is_dir():
        raise ValueError(f"'{dir}' is not a directory")

    # Convert root_dir to resolved path if provided
    root_path = Path(root_dir).resolve() if root_dir is not None else None

    while current_path != current_path.parent:  # Stop at filesystem root
        target_dir = current_path / dot_dir
        try:
            if target_dir.is_dir():
                return str(target_dir)
        except PermissionError:
            # Stop searching if we don't have permission to access this directory
            break

        # Stop if we've reached the specified root directory
        if root_path is not None and current_path == root_path:
            break

        current_path = current_path.parent

    return None


def find_workspace_dir(dir: str, root_dir: Optional[str] = None) -> str:
    """
    Find the workspace directory using the following algorithm:

    1. First finds the nearest .jupyter directory
    2. If the .jupyter directory has a parent that is the root_dir,
       go to step 3, otherwise return the .jupyter directory
    3. Try to find a .git directory, if found return that
    4. Simply return the directory the chat file is in.

    Args:
        dir (str): The starting directory path
        root_dir (Optional[str]): The root directory to stop searching at. If None, searches to filesystem root.

    Returns:
        str: The absolute path to the workspace directory

    Raises:
        ValueError: If dir is not a directory
    """
    # Validate that the starting path is a directory
    dir_path = Path(dir).resolve()
    if not dir_path.is_dir():
        raise ValueError(f"'{dir}' is not a directory")

    # Step 1: Find nearest .jupyter directory
    jupyter_dir = find_dot_dir(dir, ".jupyter", root_dir)

    if jupyter_dir is not None:
        jupyter_path = Path(jupyter_dir)
        done = True
        # Step 2: Check if .jupyter directory's parent is the root_dir, if so, go to step 3
        if root_dir is not None:
            root_path = Path(root_dir).resolve()
            if jupyter_path.parent == root_path:
                done = False
        if done:
            return str(jupyter_path.parent)

    # Step 3: Try to find .git directory (if no .jupyter found)
    git_dir = find_dot_dir(dir, ".git", root_dir)
    if git_dir is not None:
        return str(Path(git_dir).parent)

    # Step 4: Return chat file directory
    return str(dir_path)
