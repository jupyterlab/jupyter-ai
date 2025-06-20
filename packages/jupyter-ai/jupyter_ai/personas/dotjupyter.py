from pathlib import Path
from typing import Optional


def find_dotjupyter_dir(cwd: str, root_dir: Optional[str] = None) -> Optional[str]:
    """
    Find the nearest .jupyter directory by traversing up from the given path.

    Args:
        cwd (str): The starting directory path
        root_dir (Optional[str]): The root directory to stop searching at. If None, searches to filesystem root.

    Returns:
        str: The absolute path to the .jupyter directory if found, None otherwise
    """
    current_path = Path(cwd).resolve()
    
    # Determine the stopping point
    if root_dir is not None:
        stop_path = Path(root_dir).resolve()
    else:
        stop_path = current_path.parent  # Will be set to filesystem root in the loop

    while current_path != current_path.parent:  # Stop at root directory
        dotjupyter = current_path / ".jupyter"
        try:
            if dotjupyter.is_dir():
                return str(dotjupyter)
        except PermissionError:
            # Stop searching if we don't have permission to access this directory
            break
        
        # Stop if we've reached the specified root directory
        if root_dir is not None and current_path == stop_path:
            break
            
        current_path = current_path.parent

    return None
