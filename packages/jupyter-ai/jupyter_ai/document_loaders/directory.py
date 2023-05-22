from typing import List, Tuple, Type
from pathlib import Path
import hashlib
import itertools
import os

import dask

from langchain.schema import Document
from langchain.text_splitter import (
    TextSplitter,
)

from jupyter_ai_magics.utils import decompose_model_id, load_embedding_providers, load_providers
from jupyter_ai_magics.embedding_providers import BaseEmbeddingsProvider

def path_to_doc(path):
    with open(str(path), 'r') as f:
        text = f.read()
        m = hashlib.sha256()
        m.update(text.encode('utf-8'))
        metadata = {'path': str(path), 'sha256': m.digest(), 'extension': path.suffix}
        return Document(page_content=text, metadata=metadata)

EXCLUDE_DIRS = {'.ipynb_checkpoints', 'node_modules', 'lib', 'build', '.git', '.DS_Store'}
SUPPORTED_EXTS = {'.py', '.md', '.R', '.Rmd', '.jl', '.sh', '.ipynb', '.js', '.ts', '.jsx', '.tsx', '.txt'}

def split_document(document, splitter: TextSplitter) -> List[Document]:
    return splitter.split_documents([document])

def flatten(*chunk_lists):
    return list(itertools.chain(*chunk_lists))

def split(path, splitter):
    chunks = []

    for dir, _, filenames in os.walk(path):
        if dir in EXCLUDE_DIRS:
            continue
        
        for filename in filenames:
            filepath = Path(os.path.join(dir, filename))
            if filepath.suffix not in SUPPORTED_EXTS:
                continue

            document = dask.delayed(path_to_doc)(filepath)
            chunk = dask.delayed(split_document)(document, splitter)
            chunks.append(chunk)
    
    flattened_chunks = dask.delayed(flatten)(*chunks)
    return flattened_chunks

def join(embeddings):
    embedding_records = []
    metadatas = []

    for embedding_record, metadata in embeddings:
        embedding_records.append(embedding_record)
        metadatas.append(metadata)
    
    return (embedding_records, metadatas)

def embed_chunk(chunk, em):
    metadata = chunk.metadata
    content = chunk.page_content
    embedding = em.embed_query(content)
    return ((content, embedding), metadata)

# TODO: figure out how to declare the typing of this fn
# dask.delayed.Delayed doesn't work, nor does dask.Delayed
def get_embeddings(chunks, em):
    # split documents in parallel w.r.t. each file
    embeddings = []

    # compute embeddings in parallel
    for chunk in chunks:
        embedding = dask.delayed(embed_chunk)(chunk, em)
        embeddings.append(embedding)
    
    return dask.delayed(join)(embeddings)

# def get_ep(self, model_id: str) -> Tuple[str, Type[BaseEmbeddingsProvider]]:
#     """Returns the embedding provider class that matches the provider id"""
#     provider_id, local_model_id = decompose_model_id(model_id, self.embeddings_providers)
#     provider = self.embeddings_providers.get(provider_id, None)
#     return local_model_id, provider
