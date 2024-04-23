import hashlib
import itertools
import os
import shutil
import tarfile
from pathlib import Path
from typing import List

import dask
from langchain.document_loaders import ArxivLoader, PyPDFLoader
from langchain.schema import Document
from langchain.text_splitter import TextSplitter

# Download a single tar file from arXiv and store in a temp folder for RAG, then run learn on it.
try:
    import arxiv
except Exception as e:
    print("Missing package: arxiv")


def arxiv_to_text(id):  # id is numbers after "arXiv" in arXiv:xxxx.xxxxx
    # Get the paper from arxiv
    outfile = id + ".tex"
    temp_dir = "downloads_temp"
    if not os.path.isdir(temp_dir):
        os.mkdir(temp_dir)
    client = arxiv.Client()
    paper = next(arxiv.Client().results(arxiv.Search(id_list=[id])))
    paper.download_source(dirpath=temp_dir, filename="downloaded-paper.tar.gz")
    # Extract downloaded tar file
    tar = tarfile.open(temp_dir + "/downloaded-paper.tar.gz")
    tar.extractall(temp_dir)
    tar.close()
    tex_list = os.listdir(temp_dir)
    tex_list = [j for j in tex_list if j.lower().endswith(".tex")]
    with open(outfile, "wb") as wfd:
        for f in tex_list:
            with open(temp_dir + "/" + f, "rb") as fd:
                shutil.copyfileobj(fd, wfd)

    outfile_path = os.path.realpath(outfile)
    shutil.rmtree(temp_dir)  # Delete the temp folder but not the downloaded latex files
    return outfile_path


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
    ".tex", # added for raw latex files from arxiv
}


def split_document(document, splitter: TextSplitter) -> List[Document]:
    return splitter.split_documents([document])


def flatten(*chunk_lists):
    return list(itertools.chain(*chunk_lists))


def split(path, all_files: bool, splitter):
    chunks = []

    # Check if the path points to a single file
    if os.path.isfile(path):
        dir = os.path.dirname(path)
        filenames = [os.path.basename(path)]
    else:
        for dir, subdirs, filenames in os.walk(path):
            # Filter out hidden filenames, hidden directories, and excluded directories,
            # unless "all files" are requested
            if not all_files:
                subdirs[:] = [
                    d for d in subdirs if not (d[0] == "." or d in EXCLUDE_DIRS)
                ]
                filenames = [f for f in filenames if not f[0] == "."]

    for filename in filenames:
        filepath = Path(os.path.join(dir, filename))
        # Lower case everything to make sure file extension comparisons are not case sensitive
        if filepath.suffix.lower() not in {j.lower() for j in SUPPORTED_EXTS}:
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
