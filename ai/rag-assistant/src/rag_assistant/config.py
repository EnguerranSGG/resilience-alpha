from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RAG_", extra="ignore")

    ollama_url: str = "http://ollama:11434"
    chat_model: str = Field(default="llama3.2:3b", description="Modèle local ≤ 8 milliards de paramètres")
    embedding_model: str = "nomic-embed-text"
    document_dirs: list[Path] = [Path("/opt/rag/documents"), Path("/opt/rag/docs")]
    index_path: Path = Path("/opt/rag/index/index.json")
    chunk_size: int = Field(default=1000, ge=200, le=4000)
    chunk_overlap: int = Field(default=150, ge=0, le=1000)
    top_k: int = Field(default=4, ge=1, le=10)
    temperature: float = Field(default=0.1, ge=0, le=1)
    max_question_chars: int = 500
