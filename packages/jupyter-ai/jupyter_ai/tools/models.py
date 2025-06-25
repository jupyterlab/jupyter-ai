import re
from typing import Callable, Optional

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
        >>> async def greet(name: str):
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
    name: Optional[str] = None
    description: Optional[str] = None
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
        return (
            self.name == other.name
            and self.description == other.description
            and self.read == other.read
            and self.write == other.write
            and self.delete == other.delete
            and self.execute == other.execute
        )

    def __hash__(self):
        return hash(id(self.callable))


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
    description: Optional[str] = None
    tools: set = Field(default_factory=set)
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def add_tool(self, tool: Tool):
        """Add a tool to this toolkit.

        Args:
            tool: The tool to add to the toolkit.
        """
        self.tools.add(tool)

    def get_tools(
        self,
        read: Optional[bool] = None,
        write: Optional[bool] = None,
        execute: Optional[bool] = None,
        delete: Optional[bool] = None,
    ) -> set[Tool]:
        """Find tools in this toolkit based on capability filters.

        Returns tools that match all of the specified capability criteria.
        If a capability filter is None, it won't be considered in filtering.
        If all capability filters are None, returns all tools in the toolkit.

        Args:
            read: Whether the tool can read data. None means don't filter on this capability.
            write: Whether the tool can write data. None means don't filter on this capability.
            execute: Whether the tool can execute operations. None means don't filter on this capability.
            delete: Whether the tool can delete data. None means don't filter on this capability.

        Returns:
            A set containing tools that match the specified capability criteria.

        Example:
            >>> toolkit = Toolkit(name="TestToolkit")
            >>> read_tool = Tool(callable=lambda: None, name="reader", read=True)
            >>> write_tool = Tool(callable=lambda: None, name="writer", write=True)
            >>> write_execute_tool = Tool(callable=lambda: None, name="writer_executor", write=True, execute=True)
            >>> toolkit.add_tool(read_tool)
            >>> toolkit.add_tool(write_tool)
            >>> toolkit.add_tool(write_execute_tool)
            >>> read_tools = toolkit.get_tools(read=True)
            >>> len(read_tools)
            1
            >>> all_tools = toolkit.get_tools()
            >>> len(all_tools)
            3
            >>> write_tools = toolkit.get_tools(write=True)
            >>> len(write_tools)
            2
            >>> write_and_execute_tools = toolkit.get_tools(write=True, execute=True)
            >>> len(write_and_execute_tools)
            1
        """
        toolset = set()

        for tool in self.tools:
            # Tool should match all non-None filter criteria
            if (
                (read is None or read == tool.read)
                and (write is None or write == tool.write)
                and (execute is None or execute == tool.execute)
                and (delete is None or delete == tool.delete)
            ):
                toolset.add(tool)

        return toolset
