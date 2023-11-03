import hashlib
import itertools
import os
from pathlib import Path
from typing import List

import dask
from langchain.schema import Document
from langchain.text_splitter import TextSplitter


def path_to_doc(path):
    with open(str(path)) as f:
        text = f.read()
        m = hashlib.sha256()
        m.update(text.encode("utf-8"))
        metadata = {"path": str(path), "sha256": m.digest(), "extension": path.suffix}
        return Document(page_content=text, metadata=metadata)


# Unless /learn has the "all files" option passed in, files and directories beginning with '.' are excluded
EXCLUDE_DIRS = {
    "node_modules",
    "lib",
    "build",
}
SUPPORTED_EXTS = {
    ".py",
    ".md",
    ".R",
    ".Rmd",
    ".jl",
    ".sh",
    ".ipynb",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".txt",
}


def split_document(document, splitter: TextSplitter) -> List[Document]:
    return splitter.split_documents([document])


def flatten(*chunk_lists):
    return list(itertools.chain(*chunk_lists))


def split(path, all_files: bool, splitter):
    chunks = []

    for dir, subdirs, filenames in os.walk(path):
        # Filter out hidden filenames, hidden directories, and excluded directories,
        # unless "all files" are requested
        if not all_files:
            subdirs[:] = [d for d in subdirs if not (d[0] == '.' or d in EXCLUDE_DIRS)]
            filenames = [f for f in filenames if not f[0] == '.']

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


def embed_chunk(chunk, em_provider_cls, em_provider_args):
    em = em_provider_cls(**em_provider_args)
    metadata = chunk.metadata
    content = chunk.page_content
    embedding = em.embed_query(content)
    return ((content, embedding), metadata)


# TODO: figure out how to declare the typing of this fn
# dask.delayed.Delayed doesn't work, nor does dask.Delayed
def get_embeddings(chunks, em_provider_cls, em_provider_args):
    # split documents in parallel w.r.t. each file
    embeddings = []

    # compute embeddings in parallel
    for chunk in chunks:
        embedding = dask.delayed(embed_chunk)(chunk, em_provider_cls, em_provider_args)
        embeddings.append(embedding)

    return dask.delayed(join)(embeddings)
