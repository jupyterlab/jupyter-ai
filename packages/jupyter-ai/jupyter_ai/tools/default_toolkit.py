import asyncio
import pathlib
import shlex
from typing import Optional

from .models import Tool, Toolkit


def read(file_path: str, offset: int, limit: int) -> str:
    """
    Read a subset of lines from a text file.

    Parameters
    ----------
    file_path : str
        Absolute path to the file that should be read.
    offset : int
        The line number at which to start reading (1-based indexing).
    limit : int
        Number of lines to read starting from *offset*.  
        If *offset + limit* exceeds the number of lines in the file,
        all available lines after *offset* are returned.

    Returns
    -------
    List[str]
        List of lines (including line-ending characters) that were read.

    Examples
    --------
    >>> # Suppose ``/tmp/example.txt`` contains 10 lines
    >>> read('/tmp/example.txt', offset=3, limit=4)
    ['third line\n', 'fourth line\n', 'fifth line\n', 'sixth line\n']
    """
    path = pathlib.Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Normalize arguments
    offset = max(1, int(offset))
    limit = max(0, int(limit))
    lines: list[str] = []

    with path.open(encoding='utf-8', errors='replace') as f:
        # Skip to offset
        line_no = 0
        # Loop invariant: line_no := last read line
        # After the loop exits, line_no == offset - 1, meaning the
        # next line starts at `offset`
        while line_no < offset - 1:
            line = f.readline()
            # Return early if offset exceeds number of lines in file
            if line == "":
                return ""
            line_no += 1
        
        # Append lines until limit is reached
        while len(lines) < limit:
            line = f.readline()
            if line == "":
                break
            lines.append(line)

    return "".join(lines)


def edit(
    file_path: str,
    old_string: str,
    new_string: str,
    replace_all: bool = False,
) -> None:
    """
    Replace occurrences of a substring in a file.

    Parameters
    ----------
    file_path : str
        Absolute path to the file that should be edited.
    old_string : str
        Text that should be replaced.
    new_string : str
        Text that will replace *old_string*.
    replace_all : bool, optional
        If ``True`` all occurrences of *old_string* are replaced.
        If ``False`` (default), only the first occurrence in the file is replaced.

    Returns
    -------
    None

    Raises
    ------
    FileNotFoundError
        If *file_path* does not exist.
    ValueError
        If *old_string* is empty (replacing an empty string is ambiguous).

    Notes
    -----
    The file is overwritten atomically: it is first read into memory,
    the substitution is performed, and the file is written back.
    This keeps the operation safe for short to medium-sized files.

    Examples
    --------
    >>> # Replace only the first occurrence
    >>> edit('/tmp/test.txt', 'foo', 'bar', replace_all=False)
    >>> # Replace all occurrences
    >>> edit('/tmp/test.txt', 'foo', 'bar', replace_all=True)
    """
    path = pathlib.Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    if old_string == "":
        raise ValueError("old_string must not be empty")

    # Read the entire file
    content = path.read_text(encoding="utf-8", errors="replace")

    # Perform replacement
    if replace_all:
        new_content = content.replace(old_string, new_string)
    else:
        new_content = content.replace(old_string, new_string, 1)

    # Write back
    path.write_text(new_content, encoding="utf-8")


def write(file_path: str, content: str) -> None:
    """
    Write content to a file, creating it if it doesn't exist.

    Parameters
    ----------
    file_path : str
        Absolute path to the file that should be written.
    content : str
        Content to write to the file.

    Returns
    -------
    None

    Raises
    ------
    OSError
        If the file cannot be written (e.g., permission denied, invalid path).

    Notes
    -----
    This function will overwrite the file if it already exists.
    The parent directory must exist; this function does not create directories.

    Examples
    --------
    >>> write('/tmp/example.txt', 'Hello, world!')
    >>> write('/tmp/data.json', '{"key": "value"}')
    """
    path = pathlib.Path(file_path)
    
    # Write the content to the file
    path.write_text(content, encoding="utf-8")


async def search_grep(pattern: str, include: str = "*", cwd: Optional[str] = None) -> str:
    """
    Search for text patterns in files using ripgrep.

    This function uses ripgrep (rg) to perform fast regex-based text searching
    across files, with optional file filtering based on glob patterns.

    Parameters
    ----------
    pattern : str
        A regular expression pattern to search for. Ripgrep uses Rust regex
        syntax which supports:
        - Basic regex features: ., *, +, ?, ^, $, [], (), |
        - Character classes: \w, \d, \s, \W, \D, \S
        - Unicode categories: \p{L}, \p{N}, \p{P}, etc.
        - Word boundaries: \b, \B
        - Anchors: ^, $, \A, \z
        - Quantifiers: {n}, {n,}, {n,m}
        - Groups: (pattern), (?:pattern), (?P<name>pattern)
        - Lookahead/lookbehind: (?=pattern), (?!pattern), (?<=pattern), (?<!pattern)
        - Flags: (?i), (?m), (?s), (?x), (?U)
        
        Note: Ripgrep uses Rust's regex engine, which does NOT support:
        - Backreferences (use --pcre2 flag for this)
        - Some advanced PCRE features
    include : str, optional
        A glob pattern to filter which files to search. Defaults to "*" (all files).
        Glob patterns follow gitignore syntax:
        - * matches any sequence of characters except /
        - ? matches any single character except /
        - ** matches any sequence of characters including /
        - [abc] matches any character in the set
        - {a,b} matches either "a" or "b"
        - ! at start negates the pattern
        Examples: "*.py", "**/*.js", "src/**/*.{ts,tsx}", "!*.test.*"
    cwd : str, optional
        The directory to search in. Defaults to current working directory.

    Returns
    -------
    str
        The raw output from ripgrep, including file paths, line numbers,
        and matching lines. Empty string if no matches found.

    Raises
    ------
    RuntimeError
        If ripgrep command fails or encounters an error (non-zero exit code).
        This includes cases where:
        - Pattern syntax is invalid
        - Include glob pattern is malformed
        - Ripgrep binary is not available
        - File system errors occur

    Examples
    --------
    >>> search_grep(r"def\s+\w+", "*.py")
    'file.py:10:def my_function():'
    
    >>> search_grep(r"TODO|FIXME", "**/*.{py,js}")
    'app.py:25:# TODO: implement this
    script.js:15:// FIXME: handle edge case'
    
    >>> search_grep(r"class\s+(\w+)", "src/**/*.py")
    'src/models.py:1:class User:'
    """
    # Use bash tool to execute ripgrep
    cmd_parts = ["rg", "--color=never", "--line-number", "--with-filename"]
    
    # Add glob pattern if specified
    if include != "*":
        cmd_parts.extend(["-g", include])
    
    # Add the pattern (always quote it to handle special characters)
    cmd_parts.append(pattern)
    
    # Join command with proper shell escaping
    command = " ".join(f'"{part}"' if " " in part or any(c in part for c in "!*?[]{}()") else part for part in cmd_parts)

    try:
        result = await bash(command, cwd=cwd)
        return result
    except Exception as e:
        raise RuntimeError(f"Ripgrep search failed: {str(e)}") from e


async def bash(command: str, timeout: Optional[int] = None, cwd: Optional[str] = None) -> str:
    """Executes a bash command and returns the result

    Args:
        command: The bash command to execute
        timeout: Optional timeout in seconds
        cwd: Optional working directory to execute the command in

    Returns:
        The command output (stdout and stderr combined)
    """
    # coerce `timeout` to the correct type. sometimes LLMs pass this as a string
    if isinstance(timeout, str):
        timeout = int(timeout)

    proc = await asyncio.create_subprocess_exec(
        *shlex.split(command),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
    )

    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout)
        stdout = stdout.decode("utf-8")
        stderr = stderr.decode("utf-8")

        if proc.returncode != 0:
            info = f"Command returned non-zero exit code {proc.returncode}. This usually indicates an error."
            info += "\n\n" + fr"Original command: {command}"
            if not (stdout or stderr):
                info += "\n\nNo further information was given in stdout or stderr."
                return info
            if stdout:
                info += f"stdout:\n\n```\n{stdout}\n```\n\n"
            if stderr:
                info += f"stderr:\n\n```\n{stderr}\n```\n\n"
            return info

        if stdout:
            return stdout
        return "Command executed successfully with exit code 0. No stdout/stderr was returned."

    except asyncio.TimeoutError:
        proc.kill()
        return f"Command timed out after {timeout} seconds"


DEFAULT_TOOLKIT = Toolkit(name="jupyter-ai-default-toolkit")
DEFAULT_TOOLKIT.add_tool(Tool(callable=bash))
DEFAULT_TOOLKIT.add_tool(Tool(callable=read))
DEFAULT_TOOLKIT.add_tool(Tool(callable=edit))
DEFAULT_TOOLKIT.add_tool(Tool(callable=write))
DEFAULT_TOOLKIT.add_tool(Tool(callable=search_grep))