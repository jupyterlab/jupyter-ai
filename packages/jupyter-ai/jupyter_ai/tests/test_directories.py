import os
import tempfile
from pathlib import Path

import pytest
from jupyter_ai.personas.directories import find_dot_dir, find_workspace_dir


def test_find_dot_dir_jupyter_found():
    # Create a temporary directory structure
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create nested directories
        nested_dir = Path(temp_dir) / "level1" / "level2" / "level3"
        nested_dir.mkdir(parents=True)

        # Create .jupyter directory at level2
        dotjupyter_dir = nested_dir.parent / ".jupyter"
        dotjupyter_dir.mkdir()

        # Test finding .jupyter from level3
        result = find_dot_dir(str(nested_dir), ".jupyter")
        assert Path(result).resolve() == dotjupyter_dir.resolve()
        assert Path(result).is_dir()


def test_find_dot_dir_jupyter_not_found():
    # Create a temporary directory without .jupyter
    with tempfile.TemporaryDirectory() as temp_dir:
        nested_dir = Path(temp_dir) / "level1" / "level2" / "level3"
        nested_dir.mkdir(parents=True)

        # Test from level3 - should return None as no .jupyter exists
        result = find_dot_dir(str(nested_dir), ".jupyter")
        assert result is None


def test_find_dot_dir_jupyter_current_level():
    # Create a temporary directory with .jupyter at the same level
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir) / "test_dir"
        test_dir.mkdir()

        dotjupyter_dir = test_dir / ".jupyter"
        dotjupyter_dir.mkdir()

        # Test finding .jupyter from the same directory
        result = find_dot_dir(str(test_dir), ".jupyter")
        assert Path(result).resolve() == dotjupyter_dir.resolve()
        assert os.path.isdir(result)


def test_find_dot_dir_jupyter_with_root_dir():
    # Create a temporary directory structure with .jupyter at multiple levels
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create nested directories
        level1 = Path(temp_dir) / "level1"
        level2 = level1 / "level2"
        level3 = level2 / "level3"
        level3.mkdir(parents=True)

        # Create .jupyter directories at both level1 and level2
        dotjupyter_level1 = level1 / ".jupyter"
        dotjupyter_level1.mkdir()

        dotjupyter_level2 = level2 / ".jupyter"
        dotjupyter_level2.mkdir()

        # Test finding .jupyter from level3 with root_dir set to level2
        # Should find the .jupyter at level2, not level1
        result = find_dot_dir(str(level3), ".jupyter", root_dir=str(level2))
        assert Path(result).resolve() == dotjupyter_level2.resolve()
        assert Path(result).is_dir()

        # Test finding .jupyter from level3 with root_dir set to level1
        # Should find the .jupyter at level2
        result = find_dot_dir(str(level3), ".jupyter", root_dir=str(level1))
        assert Path(result).resolve() == dotjupyter_level2.resolve()
        assert Path(result).is_dir()

        # Test finding .jupyter from level3 with root_dir set to level3
        # Should return None as no .jupyter exists at or above level3 within the root_dir
        result = find_dot_dir(str(level3), ".jupyter", root_dir=str(level3))
        assert result is None


def test_find_dot_dir_git():
    # Test finding .git directory
    with tempfile.TemporaryDirectory() as temp_dir:
        nested_dir = Path(temp_dir) / "level1" / "level2" / "level3"
        nested_dir.mkdir(parents=True)

        # Create .git directory at level2
        dotgit_dir = nested_dir.parent / ".git"
        dotgit_dir.mkdir()

        # Test finding .git from level3
        result = find_dot_dir(str(nested_dir), ".git")
        assert Path(result).resolve() == dotgit_dir.resolve()
        assert Path(result).is_dir()


def test_find_dot_dir_not_found():
    # Test when target directory doesn't exist
    with tempfile.TemporaryDirectory() as temp_dir:
        nested_dir = Path(temp_dir) / "level1" / "level2" / "level3"
        nested_dir.mkdir(parents=True)

        # Test finding .git when it doesn't exist
        result = find_dot_dir(str(nested_dir), ".git")
        assert result is None


def test_find_dot_dir_with_root_dir():
    # Test with root_dir boundary
    with tempfile.TemporaryDirectory() as temp_dir:
        level1 = Path(temp_dir) / "level1"
        level2 = level1 / "level2"
        level3 = level2 / "level3"
        level3.mkdir(parents=True)

        # Create .git at level1
        dotgit_level1 = level1 / ".git"
        dotgit_level1.mkdir()

        # Test finding .git from level3 with root_dir set to level2
        # Should return None since .git is above the root_dir
        result = find_dot_dir(str(level3), ".git", root_dir=str(level2))
        assert result is None

        # Test finding .git from level3 with root_dir set to level1
        # Should find .git at level1
        result = find_dot_dir(str(level3), ".git", root_dir=str(level1))
        assert Path(result).resolve() == dotgit_level1.resolve()


def test_find_dot_dir_custom_name():
    # Test with custom dot directory name
    with tempfile.TemporaryDirectory() as temp_dir:
        nested_dir = Path(temp_dir) / "level1" / "level2"
        nested_dir.mkdir(parents=True)

        # Create .custom directory
        custom_dir = nested_dir / ".custom"
        custom_dir.mkdir()

        # Test finding .custom
        result = find_dot_dir(str(nested_dir), ".custom")
        assert Path(result).resolve() == custom_dir.resolve()
        assert Path(result).is_dir()


def test_find_workspace_dir_jupyter_only():
    # Test when only .jupyter exists
    with tempfile.TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir) / "project"
        chat_dir = project_dir / "notebooks"
        chat_dir.mkdir(parents=True)

        # Create .jupyter directory at project level
        jupyter_dir = project_dir / ".jupyter"
        jupyter_dir.mkdir()

        # Should return project directory (parent of .jupyter)
        result = find_workspace_dir(str(chat_dir))
        assert Path(result).resolve() == project_dir.resolve()


def test_find_workspace_dir_git_only():
    # Test when only .git exists
    with tempfile.TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir) / "project"
        chat_dir = project_dir / "notebooks"
        chat_dir.mkdir(parents=True)

        # Create .git directory at project level
        git_dir = project_dir / ".git"
        git_dir.mkdir()

        # Should return project directory (parent of .git)
        result = find_workspace_dir(str(chat_dir))
        assert Path(result).resolve() == project_dir.resolve()


def test_find_workspace_dir_neither_exists():
    # Test when neither .jupyter nor .git exists
    with tempfile.TemporaryDirectory() as temp_dir:
        chat_dir = Path(temp_dir) / "notebooks"
        chat_dir.mkdir(parents=True)

        # Should return the chat directory itself
        result = find_workspace_dir(str(chat_dir))
        assert Path(result).resolve() == chat_dir.resolve()


def test_find_workspace_dir_jupyter_at_root():
    # Test when .jupyter directory's parent is the root_dir
    with tempfile.TemporaryDirectory() as temp_dir:
        root_dir = Path(temp_dir)
        jupyter_dir = root_dir / ".jupyter"
        jupyter_dir.mkdir()

        project_dir = root_dir / "project"
        chat_dir = project_dir / "notebooks"
        chat_dir.mkdir(parents=True)

        # Create .git directory at project level
        git_dir = project_dir / ".git"
        git_dir.mkdir()

        # Should find .git and return project directory
        result = find_workspace_dir(str(chat_dir), root_dir=str(root_dir))
        assert Path(result).resolve() == project_dir.resolve()


def test_find_workspace_dir_jupyter_at_root_no_git():
    # Test when .jupyter directory's parent is the root_dir and no .git exists
    with tempfile.TemporaryDirectory() as temp_dir:
        root_dir = Path(temp_dir)
        jupyter_dir = root_dir / ".jupyter"
        jupyter_dir.mkdir()

        project_dir = root_dir / "project"
        chat_dir = project_dir / "notebooks"
        chat_dir.mkdir(parents=True)

        # Should return chat directory since no .git found
        result = find_workspace_dir(str(chat_dir), root_dir=str(root_dir))
        assert Path(result).resolve() == chat_dir.resolve()


def test_find_workspace_dir_both_exist():
    # Test when both .jupyter and .git exist at same level
    with tempfile.TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir) / "project"
        chat_dir = project_dir / "notebooks"
        chat_dir.mkdir(parents=True)

        # Create both .jupyter and .git at project level
        jupyter_dir = project_dir / ".jupyter"
        jupyter_dir.mkdir()
        git_dir = project_dir / ".git"
        git_dir.mkdir()

        # Should return project directory (parent of .jupyter, which is found first)
        result = find_workspace_dir(str(chat_dir))
        assert Path(result).resolve() == project_dir.resolve()


def test_find_dot_dir_invalid_dir():
    # Test with non-existent directory
    with pytest.raises(ValueError, match="is not a directory"):
        find_dot_dir("/non/existent/path", ".git")

    # Test with file instead of directory
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("test")

        with pytest.raises(ValueError, match="is not a directory"):
            find_dot_dir(str(test_file), ".git")


def test_find_workspace_dir_invalid_dir():
    # Test with non-existent directory
    with pytest.raises(ValueError, match="is not a directory"):
        find_workspace_dir("/non/existent/path")

    # Test with file instead of directory
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("test")

        with pytest.raises(ValueError, match="is not a directory"):
            find_workspace_dir(str(test_file))
