import re
from typing import Callable

from pydantic import BaseModel, ConfigDict, Field, model_validator


def get_doc_description(func) -> str:
    """Extract the first paragraph from a function's docstring.

    Args:
        func: The function to extract documentation from.

    Returns:
        The first paragraph of the function's docstring, cleaned up and
        with whitespace normalized. Returns empty string if no docstring exists.

    Example:
        >>> def sample_func():
        ...     '''This is the first paragraph.
        ...
        ...     This is the second paragraph.'''
        ...     pass
        >>> get_doc_description(sample_func)
        'This is the first paragraph.'
    """
    if not func.__doc__:
        return ""

    # Split docstring into paragraphs
    paragraphs = re.split(r"\n\s*\n", func.__doc__.strip())

    # Return the first paragraph, cleaned up
    if paragraphs:
        return re.sub(r"\s+", " ", paragraphs[0].strip())

    return ""


class Tool(BaseModel):
    """Represents a tool with callable function and capability metadata.

    A Tool wraps a callable function with metadata including name, description,
    and flags that indicate what operations the tool can perform.

    Attributes:
        callable: The function that implements the tool's functionality.
        name: The tool's name. Auto-generated from callable if not provided.
        description: Tool description. Auto-extracted from callable docstring if not provided.
        read: Whether the tool can read data.
        write: Whether the tool can write data.
        execute: Whether the tool can execute operations.
        delete: Whether the tool can delete data.

    Example:
        >>> def greet(name: str):
        ...     '''Say hello to someone.'''
        ...     return f"Hello, {name}!"
        >>> tool = Tool(callable=greet, read=True)
        >>> tool.name
        'greet'
        >>> tool.description
        'Say hello to someone.'
        >>> tool.read
        True
    """

    callable: Callable = Field(exclude=True)
    name: str | None = None
    description: str | None = None
    read: bool = False
    write: bool = False
    execute: bool = False
    delete: bool = False

    @model_validator(mode="after")
    def set_name_description(self):
        if not self.name:
            if hasattr(self.callable, "__name__") and self.callable.__name__:
                self.name = self.callable.__name__
            else:
                raise ValueError("Unable to extract name from callable")

        if not self.description:
            self.description = get_doc_description(self.callable)

        return self

    def __eq__(self, other):
        if not isinstance(other, Tool):
            return False
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)


class ToolSet(set):
    """A collection of tools that enforces unique tool names.

    Ensures that tools with duplicate names cannot be added to the same collection.

    Example:
        >>> toolset = ToolSet()
        >>> tool1 = Tool(callable=lambda: None, name="test")
        >>> tool2 = Tool(callable=lambda: None, name="test")  # Same name
        >>> toolset.add(tool1)
        >>> toolset.add(tool2)  # Raises ValueError
        Traceback (most recent call last):
        ...
        ValueError: Tool with name 'test' already exists in the set
    """

    def add(self, item):
        if item in self:
            raise ValueError(f"Tool with name '{item.name}' already exists in the set")
        super().add(item)


class Toolkit(BaseModel):
    """A collection of tools with capability-based filtering.

    A Toolkit groups related tools together and provides methods to add tools
    and find tools based on their capability flags.

    Attributes:
        name: The toolkit's name.
        description: Optional description of the toolkit.
        tools: The set of tools in this toolkit.

    Example:
        >>> def read_file(path: str):
        ...     '''Read a file from disk.'''
        ...     with open(path) as f:
        ...         return f.read()
        >>> def write_file(path: str, content: str):
        ...     '''Write content to a file.'''
        ...     with open(path, 'w') as f:
        ...         f.write(content)
        >>> toolkit = Toolkit(name="FileTools", description="File operations")
        >>> read_tool = Tool(callable=read_file, read=True)
        >>> write_tool = Tool(callable=write_file, write=True)
        >>> toolkit.add_tool(read_tool)
        >>> toolkit.add_tool(write_tool)
        >>> len(toolkit.tools)
        2
        >>> read_tools = toolkit.find_tools(read=True)
        >>> len(read_tools)
        1
    """

    name: str
    description: str | None = None
    tools: ToolSet = Field(default_factory=ToolSet)
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def add_tool(self, tool: Tool):
        """Add a tool to this toolkit.

        Args:
            tool: The tool to add to the toolkit.

        Raises:
            ValueError: If a tool with the same name already exists in the toolkit.
        """
        self.tools.add(tool)

    def find_tools(
        self,
        read: bool = False,
        write: bool = False,
        execute: bool = False,
        delete: bool = False,
    ) -> ToolSet:
        """Find tools in this toolkit based on capability filters.

        Returns tools that match all of the specified capability criteria.
        If no capability filters are specified, returns all tools in the toolkit.

        Args:
            read: Whether the tool can read data.
            write: Whether the tool can write data.
            execute: Whether the tool can execute operations.
            delete: Whether the tool can delete data.

        Returns:
            A ToolSet containing tools that match the specified capability criteria.

        Example:
            >>> toolkit = Toolkit(name="TestToolkit")
            >>> read_tool = Tool(callable=lambda: None, name="reader", read=True)
            >>> write_tool = Tool(callable=lambda: None, name="writer", write=True)
            >>> write_execute_tool = Tool(callable=lambda: None, name="writer_executor", write=True, execute=True)
            >>> toolkit.add_tool(read_tool)
            >>> toolkit.add_tool(write_tool)
            >>> toolkit.add_tool(writer_executor)
            >>> read_tools = toolkit.find_tools(read=True)
            >>> len(read_tools)
            1
            >>> all_tools = toolkit.find_tools()
            >>> len(all_tools)
            3
            >>> write_tools = toolkit.find_tools(write=True)
            >>> len(write_tools)
            2
            >>> write_and_execute_tools = toolkit.find_tools(write=True, execute=True)
            >>> len(write_and_execute_tools)
            1
        """
        toolset = ToolSet()

        any_param_true = read or write or execute or delete

        for tool in self.tools:
            if not any_param_true:
                toolset.add(tool)
                continue

            matches_all = True

            if read and not tool.read:
                matches_all = False
            if write and not tool.write:
                matches_all = False
            if execute and not tool.execute:
                matches_all = False
            if delete and not tool.delete:
                matches_all = False

            if matches_all:
                toolset.add(tool)

        return toolset
