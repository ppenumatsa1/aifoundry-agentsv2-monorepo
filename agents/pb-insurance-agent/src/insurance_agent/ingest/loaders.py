from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

from insurance_agent.core.logging import get_logger


@dataclass(frozen=True)
class DocumentChunk:
    source: str
    chunk_id: int
    content: str


def load_text_from_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    parts: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text:
            parts.append(text)
    return "\n".join(parts).strip()


def load_text_from_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    if chunk_size <= 0:
        return [text]
    if chunk_overlap >= chunk_size:
        chunk_overlap = max(0, chunk_size // 4)

    chunks: list[str] = []
    start = 0
    text_length = len(text)
    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunks.append(text[start:end])
        if end == text_length:
            break
        start = end - chunk_overlap
    return chunks


def load_documents(doc_dir: Path, chunk_size: int, chunk_overlap: int) -> list[DocumentChunk]:
    logger = get_logger(__name__)
    chunks: list[DocumentChunk] = []
    files = sorted(list(doc_dir.glob("*.pdf")) + list(doc_dir.glob("*.txt")))

    if not files:
        raise ValueError(f"No documents found in {doc_dir}")

    for file_path in files:
        if file_path.suffix.lower() == ".pdf":
            text = load_text_from_pdf(file_path)
        else:
            text = load_text_from_txt(file_path)

        if not text:
            logger.warning("empty_document path=%s", file_path)
            continue

        parts = split_text(text, chunk_size, chunk_overlap)
        logger.info("loaded_document path=%s chunks=%s", file_path.name, len(parts))
        for idx, part in enumerate(parts, start=1):
            chunks.append(
                DocumentChunk(
                    source=file_path.name,
                    chunk_id=idx,
                    content=part,
                )
            )

    return chunks
