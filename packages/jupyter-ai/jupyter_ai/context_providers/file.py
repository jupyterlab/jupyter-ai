import glob
import os
from typing import List

import nbformat
from jupyter_ai.document_loaders.directory import SUPPORTED_EXTS
from jupyter_ai.models import HumanChatMessage, ListOptionsEntry

from .base import (
    BaseCommandContextProvider,
    ContextCommand,
    ContextProviderException,
    find_commands,
)

FILE_CONTEXT_TEMPLATE = """
File: {filepath}
```
{content}
```
""".strip()


class FileContextProvider(BaseCommandContextProvider):
    id = "file"
    help = "Include selected file's contents"
    requires_arg = True
    header = "Following are contents of files referenced:"

    def get_arg_options(self, arg_prefix: str) -> List[ListOptionsEntry]:
        is_abs = not os.path.isabs(arg_prefix)
        path_prefix = arg_prefix if is_abs else os.path.join(self.base_dir, arg_prefix)
        path_prefix = path_prefix
        return [
            self._make_arg_option(
                arg=self._make_path(path, is_abs, is_dir),
                description="Directory" if is_dir else "File",
                is_complete=not is_dir,
            )
            for path in glob.glob(path_prefix + "*")
            if (
                (is_dir := os.path.isdir(path))
                or os.path.splitext(path)[1] in SUPPORTED_EXTS
            )
        ]

    def _make_path(self, path: str, is_abs: bool, is_dir: bool) -> str:
        if not is_abs:
            path = os.path.relpath(path, self.base_dir)
        if is_dir:
            path += "/"
        return path

    async def _make_context_prompt(
        self, message: HumanChatMessage, commands: List[ContextCommand]
    ) -> str:
        context = "\n\n".join(
            [
                context
                for i in set(commands)
                if (context := self._make_command_context(i))
            ]
        )
        if not context:
            return ""
        return self.header + "\n" + context

    def _make_command_context(self, command: ContextCommand) -> str:
        filepath = command.arg or ""
        if not os.path.isabs(filepath):
            filepath = os.path.join(self.base_dir, filepath)

        if not os.path.exists(filepath):
            raise ContextProviderException(
                f"File not found while trying to read '{filepath}' "
                f"triggered by `{command}`."
            )
        if os.path.isdir(filepath):
            raise ContextProviderException(
                f"Cannot read directory '{filepath}' triggered by `{command}`. "
                f"Only files are supported."
            )
        if os.path.splitext(filepath)[1] not in SUPPORTED_EXTS:
            raise ContextProviderException(
                f"Cannot read unsupported file type '{filepath}' triggered by `{command}`. "
                f"Supported file extensions are: {', '.join(SUPPORTED_EXTS)}."
            )
        try:
            with open(filepath) as f:
                content = f.read()
        except PermissionError:
            raise ContextProviderException(
                f"Permission denied while trying to read '{filepath}' "
                f"triggered by `{command}`."
            )
        return FILE_CONTEXT_TEMPLATE.format(
            filepath=filepath,
            content=self._process_file(content, filepath),
        )

    def _process_file(self, content: str, filepath: str):
        if filepath.endswith(".ipynb"):
            nb = nbformat.reads(content, as_version=4)
            return "\n\n".join([cell.source for cell in nb.cells])
        return content

    def _replace_command(self, command: ContextCommand) -> str:
        # replaces commands of @file:<filepath> with '<filepath>'
        filepath = command.arg or ""
        return f"'{filepath}'"

    def get_filepaths(self, message: HumanChatMessage) -> List[str]:
        filepaths = []
        for command in find_commands(self, message.prompt):
            filepath = command.arg or ""
            if not os.path.isabs(filepath):
                filepath = os.path.join(self.base_dir, filepath)
            filepaths.append(filepath)
        return filepaths
