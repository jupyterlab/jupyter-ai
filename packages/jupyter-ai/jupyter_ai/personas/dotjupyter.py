from pathlib import Path


def find_dotjupyter_dir(cwd: str) -> str:
    """
    Find the nearest .jupyter directory by traversing up from the given path.

    Args:
        cwd (str): The starting directory path

    Returns:
        str: The absolute path to the .jupyter directory if found, None otherwise
    """
    current_path = Path(cwd).resolve()

    while current_path != current_path.parent:  # Stop at root directory
        dotjupyter = current_path / ".jupyter"
        if dotjupyter.is_dir():
            return str(dotjupyter)
        current_path = current_path.parent

    return None
