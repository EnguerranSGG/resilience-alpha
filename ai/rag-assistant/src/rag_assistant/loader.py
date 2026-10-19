"""Chargement et découpage des documents Markdown et PDF."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

SUPPORTED = {".md", ".pdf"}
_HEADERS = [("#", "h1"), ("##", "h2"), ("###", "h3")]


def iter_files(directories: Iterable[Path]) -> list[Path]:
    files: list[Path] = []
    for directory in directories:
        if directory.is_dir():
            files.extend(p for p in sorted(directory.rglob("*")) if p.suffix.lower() in SUPPORTED)
    return files


def _load_markdown(path: Path, root: Path) -> list[Document]:
    sections = MarkdownHeaderTextSplitter(_HEADERS, strip_headers=False).split_text(path.read_text(encoding="utf-8"))
    for section in sections:
        heading = " > ".join(section.metadata[h] for _, h in _HEADERS if h in section.metadata)
        section.metadata = {"source": str(path.relative_to(root)), "section": heading}
    return sections


def _load_pdf(path: Path, root: Path) -> list[Document]:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    return [
        Document(
            page_content=page.extract_text() or "",
            metadata={"source": str(path.relative_to(root)), "section": f"page {i}"},
        )
        for i, page in enumerate(reader.pages, start=1)
    ]


def load_documents(directories: Iterable[Path], chunk_size: int, chunk_overlap: int) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    documents: list[Document] = []
    for directory in directories:
        for path in iter_files([directory]):
            loader = _load_pdf if path.suffix.lower() == ".pdf" else _load_markdown
            documents.extend(loader(path, directory.parent))
    chunks = splitter.split_documents([d for d in documents if d.page_content.strip()])
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk"] = i
    return chunks
