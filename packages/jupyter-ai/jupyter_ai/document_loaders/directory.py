import hashlib
import itertools
import os
import tarfile
from datetime import datetime
from glob import iglob
from pathlib import Path
from typing import List

import dask
from langchain.schema import Document
from langchain.text_splitter import TextSplitter
from langchain_community.document_loaders import PyPDFLoader


def arxiv_to_text(id: str, output_dir: str) -> str:
    """Downloads and extracts single tar file from arXiv.
    Combines the TeX components into a single file.

    Parameters
    ----------
    id : str
        id for the paper, numbers after "arXiv" in arXiv:xxxx.xxxxx

    output_dir : str
        directory to save the output file

    Returns
    -------
    output: str
        output path to the downloaded TeX file
    """

    import arxiv  # type:ignore[import-not-found,import-untyped]

    outfile = f"{id}-{datetime.now():%Y-%m-%d-%H-%M}.tex"
    download_filename = "downloaded-paper.tar.gz"
    output_path = os.path.join(output_dir, outfile)

    paper = next(arxiv.Client().results(arxiv.Search(id_list=[id])))
    paper.download_source(filename=download_filename)

    with tarfile.open(download_filename) as tar:
        tex_list = []
        for member in tar:
            if member.isfile() and member.name.lower().endswith(".tex"):
                tex_list.append(member.name)
                tar.extract(member, path="")

    with open(output_path, "w") as w:
        for f in tex_list:
            with open(f) as tex:
                w.write(tex.read())
            os.remove(f)

    os.remove(download_filename)

    return output_path


# Uses pypdf which is used by PyPDFLoader from langchain
def pdf_to_text(path):
    pages = PyPDFLoader(path)
    text = "\n \n".join([page.page_content for page in pages.load_and_split()])
    return text


def path_to_doc(path):
    with open(str(path)) as f:
        if os.path.splitext(path)[1].lower() == ".pdf":
            text = pdf_to_text(path)
        else:
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
    ".html",
    ".pdf",
    ".tex",  # added for raw latex files from arxiv
}


def split_document(document, splitter: TextSplitter) -> List[Document]:
    return splitter.split_documents([document])


def flatten(*chunk_lists):
    return list(itertools.chain(*chunk_lists))


def walk_directory(directory, all_files):
    filepaths = []
    for dir, subdirs, filenames in os.walk(directory):
        # Filter out hidden filenames, hidden directories, and excluded directories,
        # unless "all files" are requested
        if not all_files:
            subdirs[:] = [d for d in subdirs if not (d[0] == "." or d in EXCLUDE_DIRS)]
            filenames = [f for f in filenames if not f[0] == "."]
        filepaths += [Path(dir) / filename for filename in filenames]
    return filepaths


def collect_filepaths(path, all_files: bool):
    """Selects eligible files, i.e.,
    1. Files not in excluded directories, and
    2. Files that are in the valid file extensions list
    Called from the `split` function.
    Returns all the filepaths to eligible files.
    """
    # Check if the path points to a single file
    if os.path.isfile(path):
        filepaths = [Path(path)]
    elif os.path.isdir(path):
        filepaths = walk_directory(path, all_files)
    else:
        filepaths = []
        for glob_path in iglob(str(path), include_hidden=all_files, recursive=True):
            if os.path.isfile(glob_path):
                filepaths.append(Path(glob_path))
    valid_exts = {j.lower() for j in SUPPORTED_EXTS}
    filepaths = [fp for fp in filepaths if fp.suffix.lower() in valid_exts]
    return filepaths


def split(path, all_files: bool, splitter):
    """Splits files into chunks for vector db in RAG"""
    chunks = []
    filepaths = collect_filepaths(path, all_files)
    for filepath in filepaths:
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
