from typing import List, Optional
from pathlib import Path
import hashlib
import itertools

import ray

from langchain.document_loaders.base import BaseLoader
from langchain.schema import Document
from langchain.document_loaders.directory import _is_visible
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter, TextSplitter,
)

@ray.remote
def path_to_doc(path):
    with open(str(path), 'r') as f:
        text = f.read()
        m = hashlib.sha256()
        m.update(text.encode('utf-8'))
        metadata = {'path': str(path), 'sha256': m.digest(), 'extension': path.suffix}
        return Document(page_content=text, metadata=metadata)

class ExcludePattern(Exception):
    pass
    
def iter_paths(path, extensions, exclude):
    for p in Path(path).rglob('*'):
        if p.is_dir():
            continue
        if not _is_visible(p.relative_to(path)):
            continue
        try:
            for pattern in exclude:
                if pattern in str(p):
                    raise ExcludePattern()
        except ExcludePattern:
            continue
        if p.suffix in extensions:
            yield p

class RayRecursiveDirectoryLoader(BaseLoader):
    
    def __init__(
        self,
        path,
        extensions={'.py', '.md', '.R', '.Rmd', '.jl', '.sh', '.ipynb', '.js', '.ts', '.jsx', '.tsx', '.txt'},
        exclude={'.ipynb_checkpoints', 'node_modules', 'lib', 'build', '.git', '.DS_Store'}
    ):
        self.path = path
        self.extensions = extensions
        self.exclude=exclude
    
    def load(self) -> List[Document]:
        paths = iter_paths(self.path, self.extensions, self.exclude)
        doc_refs = list(map(path_to_doc.remote, paths))
        return ray.get(doc_refs)
    
    def load_and_split(
        self, text_splitter: Optional[TextSplitter] = None
    ) -> List[Document]:
        if text_splitter is None:
            _text_splitter = RecursiveCharacterTextSplitter()
        else:
            _text_splitter = text_splitter

        @ray.remote
        def split(doc):
            return _text_splitter.split_documents([doc])
        
        paths = iter_paths(self.path, self.extensions, self.exclude)
        doc_refs = map(split.remote, map(path_to_doc.remote, paths))
        return list(itertools.chain(*ray.get(list(doc_refs))))