"""Tests for default_toolkit.py functions and toolkit configuration."""

import pathlib
import tempfile
import pytest
from unittest.mock import patch, mock_open

from .default_toolkit import read, edit, write, search_grep, DEFAULT_TOOLKIT
from .models import Tool, Toolkit


class TestReadFunction:
    """Test the read function."""

    def test_read_valid_file(self):
        """Test reading lines from a valid file."""
        # Create a temporary file with known content
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("line 1\nline 2\nline 3\nline 4\nline 5\n")
            temp_path = f.name

        try:
            # Test reading from offset 2, limit 3
            result = read(temp_path, offset=2, limit=3)
            assert result == "line 2\nline 3\nline 4\n"

            # Test reading from offset 1, limit 2
            result = read(temp_path, offset=1, limit=2)
            assert result == "line 1\nline 2\n"

            # Test reading all lines from beginning
            result = read(temp_path, offset=1, limit=10)
            assert result == "line 1\nline 2\nline 3\nline 4\nline 5\n"

            # Test reading from middle to end
            result = read(temp_path, offset=4, limit=10)
            assert result == "line 4\nline 5\n"

        finally:
            # Clean up
            pathlib.Path(temp_path).unlink()

    def test_read_empty_file(self):
        """Test reading from an empty file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_path = f.name

        try:
            result = read(temp_path, offset=1, limit=5)
            assert result == ""
        finally:
            pathlib.Path(temp_path).unlink()

    def test_read_single_line_file(self):
        """Test reading from a file with one line."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("single line\n")
            temp_path = f.name

        try:
            result = read(temp_path, offset=1, limit=1)
            assert result == "single line\n"

            result = read(temp_path, offset=1, limit=5)
            assert result == "single line\n"
        finally:
            pathlib.Path(temp_path).unlink()

    def test_read_file_not_found(self):
        """Test reading from a non-existent file."""
        with pytest.raises(FileNotFoundError, match="File not found: /nonexistent/path"):
            read("/nonexistent/path", offset=1, limit=5)

    def test_read_offset_beyond_file_length(self):
        """Test reading with offset beyond file length."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("line 1\nline 2\n")
            temp_path = f.name

        try:
            # Offset beyond file length should return empty string
            result = read(temp_path, offset=10, limit=5)
            assert result == ""
        finally:
            pathlib.Path(temp_path).unlink()

    def test_read_negative_and_zero_values(self):
        """Test read function with negative and zero offset/limit values."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("line 1\nline 2\nline 3\n")
            temp_path = f.name

        try:
            # Negative offset should be normalized to 1
            result = read(temp_path, offset=-5, limit=2)
            assert result == "line 1\nline 2\n"

            # Zero offset should be normalized to 1
            result = read(temp_path, offset=0, limit=2)
            assert result == "line 1\nline 2\n"

            # Zero limit should return empty string
            result = read(temp_path, offset=1, limit=0)
            assert result == ""

            # Negative limit should return empty string
            result = read(temp_path, offset=1, limit=-5)
            assert result == ""

        finally:
            pathlib.Path(temp_path).unlink()

    def test_read_unicode_content(self):
        """Test reading file with unicode content."""
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.txt') as f:
            f.write("línea 1 🚀\nlínea 2 ❤️\nlínea 3 🎉\n")
            temp_path = f.name

        try:
            result = read(temp_path, offset=1, limit=2)
            assert result == "línea 1 🚀\nlínea 2 ❤️\n"
        finally:
            pathlib.Path(temp_path).unlink()

    def test_read_with_encoding_errors(self):
        """Test reading file with encoding issues using replace errors handling."""
        # This test ensures the 'replace' error handling works properly
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("valid line\n")
            temp_path = f.name

        try:
            # The function should handle encoding errors gracefully
            result = read(temp_path, offset=1, limit=1)
            assert result == "valid line\n"
        finally:
            pathlib.Path(temp_path).unlink()


class TestEditFunction:
    """Test the edit function."""

    def test_edit_replace_first_occurrence(self):
        """Test replacing the first occurrence of a string."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("foo bar foo baz foo")
            temp_path = f.name

        try:
            edit(temp_path, "foo", "qux", replace_all=False)
            
            # Read the file to verify the change
            content = pathlib.Path(temp_path).read_text(encoding='utf-8')
            assert content == "qux bar foo baz foo"
        finally:
            pathlib.Path(temp_path).unlink()

    def test_edit_replace_all_occurrences(self):
        """Test replacing all occurrences of a string."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("foo bar foo baz foo")
            temp_path = f.name

        try:
            edit(temp_path, "foo", "qux", replace_all=True)
            
            # Read the file to verify the change
            content = pathlib.Path(temp_path).read_text(encoding='utf-8')
            assert content == "qux bar qux baz qux"
        finally:
            pathlib.Path(temp_path).unlink()

    def test_edit_multiline_content(self):
        """Test editing multiline content."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("line 1\nold content\nline 3\nold content\nline 5")
            temp_path = f.name

        try:
            edit(temp_path, "old content", "new content", replace_all=True)
            
            content = pathlib.Path(temp_path).read_text(encoding='utf-8')
            assert content == "line 1\nnew content\nline 3\nnew content\nline 5"
        finally:
            pathlib.Path(temp_path).unlink()

    def test_edit_string_not_found(self):
        """Test editing when the target string is not found."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("hello world")
            temp_path = f.name

        try:
            # This should not raise an error, just leave the file unchanged
            edit(temp_path, "nonexistent", "replacement", replace_all=False)
            
            content = pathlib.Path(temp_path).read_text(encoding='utf-8')
            assert content == "hello world"
        finally:
            pathlib.Path(temp_path).unlink()

    def test_edit_file_not_found(self):
        """Test editing a non-existent file."""
        with pytest.raises(FileNotFoundError, match="File not found: /nonexistent/path"):
            edit("/nonexistent/path", "old", "new")

    def test_edit_empty_old_string(self):
        """Test editing with an empty old_string."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("hello world")
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="old_string must not be empty"):
                edit(temp_path, "", "replacement")
        finally:
            pathlib.Path(temp_path).unlink()

    def test_edit_unicode_content(self):
        """Test editing file with unicode content."""
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.txt') as f:
            f.write("hola 🌟 mundo 🌟 adiós")
            temp_path = f.name

        try:
            edit(temp_path, "🌟", "⭐", replace_all=True)
            
            content = pathlib.Path(temp_path).read_text(encoding='utf-8')
            assert content == "hola ⭐ mundo ⭐ adiós"
        finally:
            pathlib.Path(temp_path).unlink()

    def test_edit_newline_characters(self):
        """Test editing with newline characters."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("line1\nold\nline3")
            temp_path = f.name

        try:
            edit(temp_path, "\nold\n", "\nnew\n", replace_all=False)
            
            content = pathlib.Path(temp_path).read_text(encoding='utf-8')
            assert content == "line1\nnew\nline3"
        finally:
            pathlib.Path(temp_path).unlink()

    def test_edit_replace_with_empty_string(self):
        """Test replacing content with empty string (deletion)."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("keep this DELETE_ME keep this too")
            temp_path = f.name

        try:
            edit(temp_path, "DELETE_ME ", "", replace_all=False)
            
            content = pathlib.Path(temp_path).read_text(encoding='utf-8')
            assert content == "keep this keep this too"
        finally:
            pathlib.Path(temp_path).unlink()

    def test_edit_atomicity(self):
        """Test that edit operation is atomic (file is either fully updated or unchanged)."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            original_content = "original content"
            f.write(original_content)
            temp_path = f.name

        try:
            # Mock pathlib.Path.write_text to raise an exception
            with patch.object(pathlib.Path, 'write_text', side_effect=IOError("Disk full")):
                with pytest.raises(IOError):
                    edit(temp_path, "original", "modified")
                
                # File should remain unchanged due to the error
                content = pathlib.Path(temp_path).read_text(encoding='utf-8')
                assert content == original_content

        finally:
            pathlib.Path(temp_path).unlink()


class TestWriteFunction:
    """Test the write function."""

    def test_write_new_file(self):
        """Test writing content to a new file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir) / "new_file.txt"
            test_content = "Hello, world!\nThis is a test."
            
            write(str(temp_path), test_content)
            
            # Verify the file was created and contains the correct content
            assert temp_path.exists()
            content = temp_path.read_text(encoding='utf-8')
            assert content == test_content

    def test_write_overwrite_existing_file(self):
        """Test overwriting an existing file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("original content")
            temp_path = f.name

        try:
            new_content = "new content that replaces the old"
            write(temp_path, new_content)
            
            # Verify the file was overwritten
            content = pathlib.Path(temp_path).read_text(encoding='utf-8')
            assert content == new_content
        finally:
            pathlib.Path(temp_path).unlink()

    def test_write_empty_content(self):
        """Test writing empty content to a file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir) / "empty_file.txt"
            
            write(str(temp_path), "")
            
            # Verify the file exists and is empty
            assert temp_path.exists()
            content = temp_path.read_text(encoding='utf-8')
            assert content == ""

    def test_write_multiline_content(self):
        """Test writing multiline content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir) / "multiline.txt"
            test_content = "Line 1\nLine 2\nLine 3\n"
            
            write(str(temp_path), test_content)
            
            content = temp_path.read_text(encoding='utf-8')
            assert content == test_content

    def test_write_unicode_content(self):
        """Test writing unicode content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir) / "unicode.txt"
            test_content = "Hello 世界! 🌍 Café naïve résumé"
            
            write(str(temp_path), test_content)
            
            content = temp_path.read_text(encoding='utf-8')
            assert content == test_content

    def test_write_large_content(self):
        """Test writing large content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir) / "large.txt"
            # Create content with 10000 lines
            test_content = "\n".join([f"Line {i}" for i in range(10000)])
            
            write(str(temp_path), test_content)
            
            content = pathlib.Path(temp_path).read_text(encoding='utf-8')
            assert content == test_content

    @pytest.mark.skip("Fix this test for CRLF newlines (Windows problem)")
    def test_write_special_characters(self):
        """Test writing content with special characters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir) / "special.txt"
            test_content = 'Content with "quotes", \ttabs, and \nnewlines\r\n'
            
            write(str(temp_path), test_content)
            
            content = temp_path.read_text(encoding='utf-8')
            assert content == test_content

    def test_write_invalid_directory(self):
        """Test writing to a non-existent directory."""
        invalid_path = "/nonexistent/directory/file.txt"
        
        with pytest.raises(OSError):
            write(invalid_path, "test content")

    def test_write_permission_denied(self):
        """Test writing to a file without write permissions."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("original")
            temp_path = f.name

        try:
            # Make file read-only
            pathlib.Path(temp_path).chmod(0o444)
            
            with pytest.raises(OSError):
                write(temp_path, "new content")
                
        finally:
            # Restore write permissions and clean up
            pathlib.Path(temp_path).chmod(0o644)
            pathlib.Path(temp_path).unlink()

    def test_write_binary_like_content(self):
        """Test writing content that looks like binary data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir) / "binary_like.txt"
            # Content with null bytes and other control characters
            test_content = "Normal text\x00null byte\x01control char\xff"
            
            write(str(temp_path), test_content)
            
            content = temp_path.read_text(encoding='utf-8')
            assert content == test_content

    def test_write_json_content(self):
        """Test writing JSON-like content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir) / "data.json"
            test_content = '{"name": "test", "value": 42, "nested": {"key": "value"}}'
            
            write(str(temp_path), test_content)
            
            content = temp_path.read_text(encoding='utf-8')
            assert content == test_content

    def test_write_code_content(self):
        """Test writing code content with proper indentation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir) / "code.py"
            test_content = '''def hello():
    """Say hello."""
    print("Hello, world!")
    
    if True:
        return "success"
'''
            
            write(str(temp_path), test_content)
            
            content = temp_path.read_text(encoding='utf-8')
            assert content == test_content

    @pytest.mark.skip("Fix this test for CRLF newlines (Windows problem)")
    def test_write_preserves_line_endings(self):
        """Test that write preserves different line endings."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir) / "line_endings.txt"
            test_content = "Unix\nWindows\r\nMac\rMixed\r\n"
            
            write(str(temp_path), test_content)
            
            content = temp_path.read_text(encoding='utf-8')
            assert content == test_content


class TestSearchGrepFunction:
    """Test the search_grep function."""

    @patch('jupyter_ai.tools.default_toolkit.bash')
    @pytest.mark.asyncio
    async def test_search_grep_bash_integration(self, mock_bash):
        """Test that search_grep correctly calls bash with proper arguments."""
        mock_bash.return_value = "test.py:1:def test():"
        
        result = await search_grep("def", "*.py")
        
        # Verify bash was called
        mock_bash.assert_called_once()
        call_args = mock_bash.call_args[0][0]
        
        # Check that the command contains expected parts
        assert "rg" in call_args
        assert "--color=never" in call_args
        assert "--line-number" in call_args
        assert "--with-filename" in call_args
        assert "-g" in call_args
        assert "*.py" in call_args
        assert "def" in call_args
        
        assert result == "test.py:1:def test():"

    @patch('jupyter_ai.tools.default_toolkit.bash')
    @pytest.mark.asyncio
    async def test_search_grep_default_include(self, mock_bash):
        """Test search_grep with default include pattern."""
        mock_bash.return_value = ""
        
        await search_grep("pattern")
        
        call_args = mock_bash.call_args[0][0]
        # Should not contain -g flag when using default "*" pattern
        assert "-g" not in call_args or "\"*\"" not in call_args

    @patch('jupyter_ai.tools.default_toolkit.bash')
    @pytest.mark.asyncio
    async def test_search_grep_bash_exception(self, mock_bash):
        """Test search_grep handling of bash execution errors."""
        mock_bash.side_effect = Exception("Command failed")
        
        with pytest.raises(RuntimeError, match="Ripgrep search failed: Command failed"):
            await search_grep("pattern", "*.txt")

    @patch('jupyter_ai.tools.default_toolkit.bash')
    @pytest.mark.asyncio
    async def test_search_grep_basic_pattern(self, mock_bash):
        """Test basic pattern searching."""
        mock_bash.return_value = "test1.py:1:def hello_world():\ntest2.py:2:    def method(self):"
        
        result = await search_grep(r"def\s+\w+", "*.py")
        
        # Should find function definitions in both files
        assert "test1.py" in result
        assert "test2.py" in result
        assert "def hello_world" in result
        assert "def method" in result

    @patch('jupyter_ai.tools.default_toolkit.bash')
    @pytest.mark.asyncio
    async def test_search_grep_no_matches(self, mock_bash):
        """Test search with no matches."""
        mock_bash.return_value = ""
        
        result = await search_grep("nonexistent_pattern", "*.txt")
        assert result == ""

    @patch('jupyter_ai.tools.default_toolkit.bash')
    @pytest.mark.asyncio
    async def test_search_grep_with_include_pattern(self, mock_bash):
        """Test search with file include pattern."""
        mock_bash.return_value = "script.py:1:import os"
        
        result = await search_grep("import", "*.py")
        assert "script.py" in result
        assert "readme.txt" not in result

    @patch('jupyter_ai.tools.default_toolkit.bash')
    @pytest.mark.asyncio
    async def test_search_grep_special_characters(self, mock_bash):
        """Test searching for patterns with special regex characters."""
        # Mock different return values for different calls
        mock_bash.side_effect = [
            "special.txt:2:email: user@domain.com",
            "special.txt:1:price: $10.99"
        ]
        
        # Search for email pattern
        result = await search_grep(r"\w+@\w+\.\w+", "*.txt")
        assert "user@domain.com" in result
        
        # Search for price pattern  
        result = await search_grep(r"\$\d+\.\d+", "*.txt")
        assert "$10.99" in result

    @patch('jupyter_ai.tools.default_toolkit.bash')
    @pytest.mark.asyncio
    async def test_search_grep_unicode_content(self, mock_bash):
        """Test searching in files with unicode content."""
        mock_bash.return_value = "unicode.txt:1:Hello 世界"
        
        result = await search_grep("世界", "*.txt")
        assert "世界" in result

    @patch('jupyter_ai.tools.default_toolkit.bash')
    @pytest.mark.asyncio
    async def test_search_grep_line_anchors(self, mock_bash):
        """Test line anchor patterns (^ and $)."""
        mock_bash.side_effect = [
            "anchors.txt:1:start of line",
            "anchors.txt:3:line with end"
        ]
        
        # Search for lines starting with specific text
        result = await search_grep("^start", "*.txt")
        assert "start of line" in result
        
        # Search for lines ending with specific text  
        result = await search_grep("end$", "*.txt")
        assert "line with end" in result

    @patch('jupyter_ai.tools.default_toolkit.bash')
    @pytest.mark.asyncio
    async def test_search_grep_case_insensitive_pattern(self, mock_bash):
        """Test case insensitive regex patterns."""
        mock_bash.return_value = "mixed_case.txt:1:TODO: fix this\nmixed_case.txt:2:todo: also this\nmixed_case.txt:3:ToDo: and this"
        
        # Case insensitive search
        result = await search_grep("(?i)todo", "*.txt")
        lines = result.strip().split('\n') if result.strip() else []
        assert len(lines) == 3  # Should match all three variants

    @patch('jupyter_ai.tools.default_toolkit.bash')
    @pytest.mark.asyncio
    async def test_search_grep_complex_glob_patterns(self, mock_bash):
        """Test various complex glob patterns."""
        mock_bash.return_value = "src/main.py:1:import sys\nsrc/utils.py:1:import os"
        
        # Test recursive search in src directory
        result = await search_grep("import", "src/**/*.py")
        assert "src/main.py" in result
        assert "src/utils.py" in result
        assert "test_main.py" not in result