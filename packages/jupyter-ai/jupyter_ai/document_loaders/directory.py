import logging
from typing import Dict, List, Optional, Union

from langchain.document_loaders.base import BaseLoader
from langchain.document_loaders.directory import FILE_LOADER_TYPE, _is_visible
from langchain.document_loaders.unstructured import UnstructuredFileLoader
from langchain.schema import Document
from wcmatch.pathlib import Path


logger = logging.getLogger(__name__)


class DirectoryLoader(BaseLoader):
    """Loading logic for loading documents from a directory."""

    def __init__(
        self,
        path: str,
        glob: Union[str, List[str]] = "**/[!.]*",
        silent_errors: bool = False,
        load_hidden: bool = False,
        loader_cls: FILE_LOADER_TYPE = UnstructuredFileLoader,
        loader_kwargs: Optional[Dict] = None,
        recursive: bool = False,
    ):
        """Initialize with path to directory and how to glob over it."""
        if loader_kwargs is None:
            loader_kwargs = {}
        self.path = path
        self.glob = glob
        self.load_hidden = load_hidden
        self.loader_cls = loader_cls
        self.loader_kwargs = loader_kwargs
        self.silent_errors = silent_errors
        self.recursive = recursive

    def load(self) -> List[Document]:
        """Load documents."""
        p = Path(self.path)
        docs = []
        items = p.rglob(self.glob) if self.recursive else p.glob(self.glob)
        for i in items:
            if i.is_file():
                if _is_visible(i.relative_to(p)) or self.load_hidden:
                    try:
                        sub_docs = self.loader_cls(str(i), **self.loader_kwargs).load()
                        docs.extend(sub_docs)
                    except Exception as e:
                        if self.silent_errors:
                            logger.warning(e)
                        else:
                            raise e
        return docs