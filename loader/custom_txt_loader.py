"""Load chapter-oriented text files into the common document representation."""

import re
from uuid import NAMESPACE_URL, uuid5

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from schemas.document import DocumentChunk, SourceType
from settings import load_document_dir


class TxtLoader:
    """Read a TXT file with an explicit encoding and preserve chapter metadata."""

    chapter_pattern = re.compile(
        r"^\s*(第\s*[0-9０-９一二三四五六七八九十百千万零〇两]+\s*[章节回][^\r\n]*)\s*$",
        re.MULTILINE,
    )

    def __init__(self, encoding: str = "gb18030", chunk_size: int = 500, chunk_overlap: int = 50):
        self.encoding = encoding
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def load(self, filename: str) -> list[DocumentChunk]:
        file_path = load_document_dir() / filename
        source = file_path.name
        source_id = str(uuid5(NAMESPACE_URL, f"{SourceType.TXT.value}:{source}"))
        text = file_path.read_text(encoding=self.encoding)
        sections = self._split_chapters(text)

        documents = [
            Document(
                page_content=content,
                metadata={
                    "source": source,
                    "source_type": SourceType.TXT.value,
                    "chapter": chapter,
                },
            )
            for chapter, content in sections
            if content.strip()
        ]
        chunks = self.splitter.split_documents(documents)
        return [
            DocumentChunk(
                chunk_id=str(uuid5(NAMESPACE_URL, f"{source_id}:{ordinal}:{chunk.page_content}")),
                source_id=source_id,
                source_type=SourceType.TXT,
                content=chunk.page_content,
                ordinal=ordinal,
                chapter=chunk.metadata.get("chapter"),
                metadata=dict(chunk.metadata),
            )
            for ordinal, chunk in enumerate(chunks)
        ]

    def _split_chapters(self, text: str) -> list[tuple[str | None, str]]:
        matches = list(self.chapter_pattern.finditer(text))
        if not matches:
            return [(None, text)]

        sections: list[tuple[str | None, str]] = []
        preamble = text[: matches[0].start()].strip()
        if preamble:
            sections.append((None, preamble))
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            chapter = match.group(1).strip()
            content = text[match.start():end].strip()
            if content:
                sections.append((chapter, content))
        return sections


# Keep the old class name as a compatibility alias for existing scripts.
CustomTextLoader = TxtLoader
