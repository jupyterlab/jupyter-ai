"""
Test the local persona manager.
"""

import tempfile
from pathlib import Path

import pytest
from jupyter_ai.personas.base_persona import BasePersona, PersonaDefaults
from jupyter_ai.personas.persona_manager import load_persona_classes_from_directory


@pytest.fixture
def tmp_persona_dir():
    """Create a temporary directory for testing LocalPersonaLoader with guaranteed cleanup."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


class TestLoadPersonaClassesFromDirectory:
    """Test cases for load_persona_classes_from_directory function."""

    def test_empty_directory_returns_empty_list(self, tmp_persona_dir):
        """Test that an empty directory returns an empty list of persona classes."""
        result = load_persona_classes_from_directory(str(tmp_persona_dir))
        assert result == []

    def test_non_persona_file_returns_empty_list(self, tmp_persona_dir):
        """Test that a Python file without persona classes returns an empty list."""
        # Create a file that doesn't contain "persona" in the name
        non_persona_file = tmp_persona_dir / "no_personas.py"
        non_persona_file.write_text("pass")

        result = load_persona_classes_from_directory(str(tmp_persona_dir))
        assert result == []

    def test_simple_persona_file_returns_persona_class(self, tmp_persona_dir):
        """Test that a file with a BasePersona subclass returns that class."""
        # Create a simple persona file
        persona_file = tmp_persona_dir / "simple_personas.py"
        persona_content = """
from jupyter_ai.personas.base_persona import BasePersona

class TestPersona(BasePersona):
    id = "test_persona"
    name = "Test Persona"
    description = "A simple test persona"

    def process_message(self, message):
        pass
"""
        persona_file.write_text(persona_content)

        result = load_persona_classes_from_directory(str(tmp_persona_dir))

        assert len(result) == 1
        assert result[0].__name__ == "TestPersona"
        assert issubclass(result[0], BasePersona)

    def test_bad_persona_file_returns_empty_list(self, tmp_persona_dir):
        """Test that a file with syntax errors returns empty list."""
        # Create a file with invalid Python code
        bad_persona_file = tmp_persona_dir / "bad_persona.py"
        bad_persona_file.write_text("1/0")

        result = load_persona_classes_from_directory(str(tmp_persona_dir))

        assert result == []
