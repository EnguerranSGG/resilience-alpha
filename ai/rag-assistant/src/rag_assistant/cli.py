"""Poser une question depuis le terminal : ``python -m rag_assistant.cli "Quel est le rôle du WAF ?"``."""

from __future__ import annotations

import sys

from rag_assistant.config import Settings
from rag_assistant.index import load_index
from rag_assistant.qa import answer


def main(argv: list[str]) -> int:
    from langchain_ollama import ChatOllama, OllamaEmbeddings

    if len(argv) < 2:
        print('usage : python -m rag_assistant.cli "question"', file=sys.stderr)
        return 2
    settings = Settings()
    embeddings = OllamaEmbeddings(model=settings.embedding_model, base_url=settings.ollama_url)
    store = load_index(settings.index_path, embeddings)
    if store is None:
        print("Index absent : lancer `python -m rag_assistant.index`", file=sys.stderr)
        return 1
    llm = ChatOllama(model=settings.chat_model, base_url=settings.ollama_url, temperature=settings.temperature)
    result = answer(" ".join(argv[1:]), store, llm, settings.top_k)
    print(result.answer, "\n\nSources :")
    for source in result.sources:
        print(f"  [{source.ref}] {source.source} — {source.section}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
