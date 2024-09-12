import os
import glob
import re
from typing import List

import nbformat
from jupyter_ai.models import ListOptionsEntry, HumanChatMessage
from jupyter_ai.document_loaders.directory import SUPPORTED_EXTS

from .base import BaseContextProvider, ContextProviderException

FILE_CONTEXT_TEMPLATE = """
File: {filepath}
```
{content}
```
""".strip()


class FileContextProvider(BaseContextProvider):
    id = "file"
    description = "Include file contents"
    requires_arg = True
    header = "Following are contents of files referenced:"

    def replace_prompt(self, prompt: str) -> str:
        # replaces instances of @file:<filepath> with '<filepath>'
        def substitute(match):
            filepath = match.group(0).partition(":")[2]
            return f"'{filepath}'"

        return re.sub(self.pattern, substitute, prompt)

    def get_arg_options(self, arg_prefix: str) -> List[ListOptionsEntry]:
        is_abs = not os.path.isabs(arg_prefix)
        path_prefix = arg_prefix if is_abs else os.path.join(self.base_dir, arg_prefix)
        return [
            self._make_option(path, is_abs, is_dir)
            for path in glob.glob(path_prefix + "*")
            if (
                (is_dir := os.path.isdir(path))
                or os.path.splitext(path)[1] in SUPPORTED_EXTS
            )
        ]

    def _make_option(self, path: str, is_abs: bool, is_dir: bool) -> ListOptionsEntry:
        if not is_abs:
            path = os.path.relpath(path, self.base_dir)
        if is_dir:
            path += "/"
        return ListOptionsEntry.from_arg(
            type="@",
            id=self.id,
            description="Directory" if is_dir else "File",
            arg=path,
            is_complete=not is_dir,
        )

    async def make_context_prompt(self, message: HumanChatMessage) -> str:
        instances = set(self._find_instances(message.prompt))
        if not instances:
            return ""
        context = "\n\n".join(
            [context for i in instances if (context := self._make_instance_context(i))]
        )
        if not context:
            return ""
        return self.header + "\n" + context

    def _make_instance_context(self, instance: str) -> str:
        filepath = instance.partition(":")[2]
        if not os.path.isabs(filepath):
            filepath = os.path.join(self.base_dir, filepath)

        if not os.path.exists(filepath):
            raise ContextProviderException(
                f"File not found while trying to read '{filepath}' "
                f"triggered by `{instance}`."
            )
        if os.path.isdir(filepath):
            raise ContextProviderException(
                f"Cannot read directory '{filepath}' triggered by `{instance}`. "
                f"Only files are supported."
            )
        if os.path.splitext(filepath)[1] not in SUPPORTED_EXTS:
            raise ContextProviderException(
                f"Cannot read unsupported file type '{filepath}' triggered by `{instance}`. "
                f"Supported file extensions are: {', '.join(SUPPORTED_EXTS)}."
            )
        try:
            with open(filepath) as f:
                content = f.read()
        except PermissionError:
            raise ContextProviderException(
                f"Permission denied while trying to read '{filepath}' "
                f"triggered by `{instance}`."
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

    def get_filepaths(self, message: HumanChatMessage) -> List[str]:
        filepaths = []
        for instance in self._find_instances(message.prompt):
            filepath = instance.partition(":")[2]
            if not os.path.isabs(filepath):
                filepath = os.path.join(self.base_dir, filepath)
            filepaths.append(filepath)
        return filepaths
