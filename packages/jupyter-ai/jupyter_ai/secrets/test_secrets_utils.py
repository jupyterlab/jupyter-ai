from jupyter_ai.secrets.secrets_utils import build_updated_dotenv, get_whitespace_around


class TestGetWhitespaceAround:
    """Test cases for get_whitespace_around function."""
    
    def test_empty_string(self):
        """Test with empty string."""
        prefix, suffix = get_whitespace_around("")
        assert prefix == ""
        assert suffix == ""
    
    def test_no_whitespace(self):
        """Test with string containing no whitespace."""
        prefix, suffix = get_whitespace_around("hello")
        assert prefix == ""
        assert suffix == ""
    
    def test_only_prefix_whitespace(self):
        """Test with string containing only leading whitespace."""
        prefix, suffix = get_whitespace_around("  hello")
        assert prefix == "  "
        assert suffix == ""
    
    def test_only_suffix_whitespace(self):
        """Test with string containing only trailing whitespace."""
        prefix, suffix = get_whitespace_around("hello  ")
        assert prefix == ""
        assert suffix == "  "
    
    def test_both_prefix_and_suffix_whitespace(self):
        """Test with string containing both leading and trailing whitespace."""
        prefix, suffix = get_whitespace_around("  hello  ")
        assert prefix == "  "
        assert suffix == "  "
    
    def test_mixed_whitespace_types(self):
        """Test with mixed whitespace types (spaces, tabs, newlines)."""
        prefix, suffix = get_whitespace_around(" \t\nhello\n\t ")
        assert prefix == " \t\n"
        assert suffix == "\n\t "
    
    def test_all_whitespace(self):
        """Test with string containing only whitespace."""
        prefix, suffix = get_whitespace_around("   ")
        assert prefix == "   "
        assert suffix == ""
    
    def test_single_character(self):
        """Test with single non-whitespace character."""
        prefix, suffix = get_whitespace_around("x")
        assert prefix == ""
        assert suffix == ""
    
    def test_single_whitespace_character(self):
        """Test with single whitespace character."""
        prefix, suffix = get_whitespace_around(" ")
        assert prefix == " "
        assert suffix == ""


class TestBuildUpdatedDotenv:
    """Test cases for build_updated_dotenv function."""
    
    def test_empty_updates(self):
        """Test with no updates to make."""
        result = build_updated_dotenv("KEY=value", {})
        assert result is None
    
    def test_add_to_empty_dotenv(self):
        """Test adding secrets to empty dotenv content."""
        result = build_updated_dotenv("", {"NEW_KEY": "new_value"})
        assert result == 'NEW_KEY="new_value"\n'
    
    def test_add_multiple_to_empty_dotenv(self):
        """Test adding multiple secrets to empty dotenv content."""
        result = build_updated_dotenv("", {
            "KEY1": "value1",
            "KEY2": "value2"
        })
        expected_lines = result.strip().split('\n')
        assert len(expected_lines) == 3  # Two keys plus one empty line
        assert 'KEY1="value1"' in expected_lines
        assert 'KEY2="value2"' in expected_lines
    
    def test_update_existing_key(self):
        """Test updating an existing key."""
        dotenv_content = 'EXISTING_KEY="old_value"\n'
        result = build_updated_dotenv(dotenv_content, {"EXISTING_KEY": "new_value"})
        assert 'EXISTING_KEY="new_value"' in result
    
    def test_add_new_key_to_existing_dotenv(self):
        """Test adding a new key to existing dotenv content."""
        dotenv_content = 'EXISTING_KEY="existing_value"\n'
        result = build_updated_dotenv(dotenv_content, {"NEW_KEY": "new_value"})
        assert 'EXISTING_KEY="existing_value"' in result
        assert 'NEW_KEY="new_value"' in result
    
    def test_remove_existing_key(self):
        """Test removing an existing key."""
        dotenv_content = 'KEY_TO_REMOVE="value"\nKEY_TO_KEEP="value"\n'
        result = build_updated_dotenv(dotenv_content, {"KEY_TO_REMOVE": None})
        assert "KEY_TO_REMOVE" not in result
        assert 'KEY_TO_KEEP="value"' in result
    
    def test_mixed_operations(self):
        """Test adding, updating, and removing keys in one operation."""
        dotenv_content = 'UPDATE_ME="old"\nREMOVE_ME="gone"\nKEEP_ME="same"\n'
        updates = {
            "UPDATE_ME": "new",
            "REMOVE_ME": None,
            "ADD_ME": "added"
        }
        result = build_updated_dotenv(dotenv_content, updates)
        
        assert 'UPDATE_ME="new"' in result
        assert "REMOVE_ME" not in result
        assert 'KEEP_ME="same"' in result
        assert 'ADD_ME="added"' in result
    
    def test_preserve_comments_and_empty_lines(self):
        """Test that comments and empty lines are preserved."""
        dotenv_content = '# This is a comment\nKEY="value"\n\n# Another comment\n'
        result = build_updated_dotenv(dotenv_content, {"NEW_KEY": "new_value"})
        
        assert "# This is a comment" in result
        assert "# Another comment" in result
        assert 'KEY="value"' in result
        assert 'NEW_KEY="new_value"' in result
    
    def test_delete_last_secret(self):
        dotenv_content="KEY='value'"
        result = build_updated_dotenv(dotenv_content, {"KEY": None})
        assert isinstance(result, str) and result.strip() == ""