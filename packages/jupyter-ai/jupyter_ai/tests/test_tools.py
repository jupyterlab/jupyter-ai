"""Tests for toolkit"""

from jupyter_ai.tools import Tool, Toolkit


def sample_function():
    """This is a sample function for testing."""
    return "Hello, World!"


def another_function(name: str):
    """Greet someone by name.

    This function takes a name and returns a greeting.
    """
    return f"Hello, {name}!"


def no_doc_function():
    return "No documentation"


class TestTool:
    """Test the Tool class."""

    def test_creation_with_name_and_description(self):
        """Test creating a tool with explicit name and description."""
        tool = Tool(
            callable=sample_function,
            name="custom_name",
            description="Custom description",
            read=True,
        )

        assert tool.name == "custom_name"
        assert tool.description == "Custom description"
        assert tool.read is True
        assert tool.write is False
        assert tool.execute is False
        assert tool.delete is False

    def test_creation_auto_name_description(self):
        """Test creating a tool with auto-generated name and description."""
        tool = Tool(callable=another_function, write=True)

        assert tool.name == "another_function"
        assert tool.description == "Greet someone by name."
        assert tool.read is False
        assert tool.write is True

    def test_creation_no_docstring(self):
        """Test creating a tool with function that has no docstring."""
        tool = Tool(callable=no_doc_function)

        assert tool.name == "no_doc_function"
        assert tool.description == ""

    def test_equality(self):
        """Test tool equality based on name."""
        tool1 = Tool(callable=sample_function, name="test")
        tool2 = Tool(callable=sample_function, name="test")
        tool3 = Tool(callable=sample_function, name="different")

        assert tool1 == tool2  # Same name
        assert tool1 != tool3  # Different name
        assert tool1 != "not_a_tool"  # Different type

    def test_hash(self):
        """Test tool hashing based on name."""
        tool1 = Tool(callable=sample_function, name="test")
        tool2 = Tool(callable=sample_function, name="test")

        assert hash(tool1) == hash(tool2)  # Same name, same hash


class TestToolkit:
    """Test the Toolkit class."""

    def test_creation(self):
        """Test creating a toolkit."""
        toolkit = Toolkit(name="TestToolkit", description="A test toolkit")

        assert toolkit.name == "TestToolkit"
        assert toolkit.description == "A test toolkit"
        assert len(toolkit.tools) == 0

    def test_add_tool(self):
        """Test adding a tool to toolkit."""
        toolkit = Toolkit(name="TestToolkit")
        tool = Tool(callable=sample_function, read=True)

        toolkit.add_tool(tool)
        assert len(toolkit.tools) == 1
        assert tool in toolkit.tools

    def test_find_tools(self):
        """Test finding tools with various capability filters."""
        # Create a toolkit
        toolkit = Toolkit(name="test_toolkit")

        # Create tools with different permission combinations
        read_only_tool = Tool(callable=lambda: None, name="read_only", read=True)
        write_tool = Tool(callable=lambda: None, name="write_tool", write=True)
        execute_tool = Tool(callable=lambda: None, name="execute_tool", execute=True)
        delete_tool = Tool(callable=lambda: None, name="delete_tool", delete=True)
        read_execute_tool = Tool(
            callable=lambda: None, name="read_execute", read=True, execute=True
        )
        write_execute_tool = Tool(
            callable=lambda: None, name="write_execute", write=True, execute=True
        )
        all_perms_tool = Tool(
            callable=lambda: None,
            name="all_perms",
            read=True,
            write=True,
            execute=True,
            delete=True,
        )

        # Add tools to the toolkit
        toolkit.add_tool(read_only_tool)
        toolkit.add_tool(write_tool)
        toolkit.add_tool(execute_tool)
        toolkit.add_tool(delete_tool)
        toolkit.add_tool(read_execute_tool)
        toolkit.add_tool(write_execute_tool)
        toolkit.add_tool(all_perms_tool)

        # Test 1: Default parameters (all None) - should return all tools
        default_tools = toolkit.get_tools()
        assert (
            len(default_tools) == 7
        ), "All tools should be returned with default parameters"
        assert read_only_tool in default_tools
        assert write_tool in default_tools
        assert execute_tool in default_tools
        assert delete_tool in default_tools
        assert read_execute_tool in default_tools
        assert write_execute_tool in default_tools
        assert all_perms_tool in default_tools

        # Test 2: Find tools with read permission
        read_tools = toolkit.get_tools(read=True)
        assert len(read_tools) == 3
        assert read_only_tool in read_tools
        assert read_execute_tool in read_tools
        assert all_perms_tool in read_tools
        assert write_tool not in read_tools
        assert execute_tool not in read_tools
        assert delete_tool not in read_tools
        assert write_execute_tool not in read_tools

        # Test 3: Find tools with write permission
        write_tools = toolkit.get_tools(write=True)
        assert len(write_tools) == 3
        assert write_tool in write_tools
        assert write_execute_tool in write_tools
        assert all_perms_tool in write_tools
        assert read_only_tool not in write_tools
        assert read_execute_tool not in write_tools
        assert execute_tool not in write_tools
        assert delete_tool not in write_tools

        # Test 4: Find tools with execute permission
        execute_tools = toolkit.get_tools(execute=True)
        assert len(execute_tools) == 4
        assert execute_tool in execute_tools
        assert read_execute_tool in execute_tools
        assert write_execute_tool in execute_tools
        assert all_perms_tool in execute_tools
        assert read_only_tool not in execute_tools
        assert write_tool not in execute_tools
        assert delete_tool not in execute_tools

        # Test 5: Find tools with delete permission
        delete_tools = toolkit.get_tools(delete=True)
        assert len(delete_tools) == 2
        assert delete_tool in delete_tools
        assert all_perms_tool in delete_tools
        assert read_only_tool not in delete_tools
        assert write_tool not in delete_tools
        assert execute_tool not in delete_tools
        assert read_execute_tool not in delete_tools
        assert write_execute_tool not in delete_tools

        # Test 6: Combined permissions (read and execute)
        read_execute_tools = toolkit.get_tools(read=True, execute=True)
        assert len(read_execute_tools) == 2
        assert read_execute_tool in read_execute_tools
        assert all_perms_tool in read_execute_tools
        assert read_only_tool not in read_execute_tools
        assert write_tool not in read_execute_tools
        assert execute_tool not in read_execute_tools
        assert write_execute_tool not in read_execute_tools
        assert delete_tool not in read_execute_tools

        # Test 7: Combined permissions (read and write)
        read_write_tools = toolkit.get_tools(read=True, write=True)
        assert len(read_write_tools) == 1
        assert all_perms_tool in read_write_tools
        assert read_only_tool not in read_write_tools
        assert write_tool not in read_write_tools
        assert execute_tool not in read_write_tools
        assert read_execute_tool not in read_write_tools
        assert write_execute_tool not in read_write_tools
        assert delete_tool not in read_write_tools

        # Test 8: Combined permissions (write and execute)
        write_execute_tools = toolkit.get_tools(write=True, execute=True)
        assert len(write_execute_tools) == 2
        assert write_execute_tool in write_execute_tools
        assert all_perms_tool in write_execute_tools
        assert read_only_tool not in write_execute_tools
        assert write_tool not in write_execute_tools
        assert execute_tool not in write_execute_tools
        assert read_execute_tool not in write_execute_tools
        assert delete_tool not in write_execute_tools

        # Test 9: Combined permissions (read, write, and execute)
        read_write_execute_tools = toolkit.get_tools(
            read=True, write=True, execute=True
        )
        assert len(read_write_execute_tools) == 1
        assert all_perms_tool in read_write_execute_tools
        assert read_only_tool not in read_write_execute_tools
        assert write_tool not in read_write_execute_tools
        assert execute_tool not in read_write_execute_tools
        assert read_execute_tool not in read_write_execute_tools
        assert write_execute_tool not in read_write_execute_tools
        assert delete_tool not in read_write_execute_tools

        # Test 10: All permissions
        all_perm_tools = toolkit.get_tools(
            read=True, write=True, execute=True, delete=True
        )
        assert len(all_perm_tools) == 1
        assert all_perms_tool in all_perm_tools
        assert read_only_tool not in all_perm_tools
        assert write_tool not in all_perm_tools
        assert execute_tool not in all_perm_tools
        assert read_execute_tool not in all_perm_tools
        assert write_execute_tool not in all_perm_tools
        assert delete_tool not in all_perm_tools

        write_not_execute_tools = toolkit.get_tools(write=True, execute=False)
        assert len(write_not_execute_tools) == 1
        assert write_tool in write_not_execute_tools
        assert execute_tool not in write_not_execute_tools
        assert read_execute_tool not in write_not_execute_tools
        assert all_perms_tool not in write_not_execute_tools
