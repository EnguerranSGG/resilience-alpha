"""Index vectoriel persistant (fichier JSON, adapté au prototype).

Construction ::

    python -m rag_assistant.index
"""

from __future__ import annotations

import sys
from pathlib import Path

from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import InMemoryVectorStore

from rag_assistant.config import Settings
from rag_assistant.loader import load_documents


def build_index(settings: Settings, embeddings: Embeddings) -> tuple[InMemoryVectorStore, int]:
    chunks = load_documents(settings.document_dirs, settings.chunk_size, settings.chunk_overlap)
    if not chunks:
        raise RuntimeError(f"aucun document trouvé dans {settings.document_dirs}")
    store = InMemoryVectorStore(embeddings)
    store.add_documents(chunks)
    settings.index_path.parent.mkdir(parents=True, exist_ok=True)
    store.dump(str(settings.index_path))
    return store, len(chunks)


def load_index(path: Path, embeddings: Embeddings) -> InMemoryVectorStore | None:
    if not path.is_file():
        return None
    return InMemoryVectorStore.load(str(path), embeddings)


def main() -> int:
    from langchain_ollama import OllamaEmbeddings

    settings = Settings()
    embeddings = OllamaEmbeddings(model=settings.embedding_model, base_url=settings.ollama_url)
    _, count = build_index(settings, embeddings)
    print(f"{count} extraits indexés dans {settings.index_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
