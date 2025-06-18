import os
import tempfile
from pathlib import Path

import pytest
from jupyter_ai.personas.dotjupyter import find_dotjupyter_dir


def test_find_dotjupyter_dir_found():
    # Create a temporary directory structure
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create nested directories
        nested_dir = Path(temp_dir) / "level1" / "level2" / "level3"
        nested_dir.mkdir(parents=True)

        # Create .jupyter directory at level2
        dotjupyter_dir = nested_dir.parent / ".jupyter"
        dotjupyter_dir.mkdir()

        # Test finding .jupyter from level3
        result = find_dotjupyter_dir(str(nested_dir))
        assert Path(result).resolve() == dotjupyter_dir.resolve()
        assert Path(result).is_dir()


def test_find_dotjupyter_dir_not_found():
    # Create a temporary directory without .jupyter
    with tempfile.TemporaryDirectory() as temp_dir:
        nested_dir = Path(temp_dir) / "level1" / "level2" / "level3"
        nested_dir.mkdir(parents=True)

        # Test from level3 - should return None as no .jupyter exists
        result = find_dotjupyter_dir(str(nested_dir))
        assert result is None


def test_find_dotjupyter_dir_current_level():
    # Create a temporary directory with .jupyter at the same level
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir) / "test_dir"
        test_dir.mkdir()

        dotjupyter_dir = test_dir / ".jupyter"
        dotjupyter_dir.mkdir()

        # Test finding .jupyter from the same directory
        result = find_dotjupyter_dir(str(test_dir))
        assert Path(result).resolve() == dotjupyter_dir.resolve()
        assert os.path.isdir(result)
