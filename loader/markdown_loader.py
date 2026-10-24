"""Load Markdown files into the common document-chunk representation."""

from uuid import NAMESPACE_URL, uuid5

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from schemas.document import DocumentChunk, SourceType
from settings import load_document_dir


class MarkdownLoader:
    """Parse Markdown headings, then split each section into indexable chunks."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.markdown_header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "h1"),
                ("##", "h2"),
                ("###", "h3"),
                ("####", "h4"),
                ("#####", "h5"),
                ("######", "h6"),
            ],
            strip_headers=False,
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def load(self, filename: str) -> list[DocumentChunk]:
        file_path = load_document_dir() / filename
        source = file_path.name
        source_id = str(uuid5(NAMESPACE_URL, f"{SourceType.MARKDOWN.value}:{source}"))
        document = TextLoader(file_path, encoding="utf-8").load()[0]
        sections = self.markdown_header_splitter.split_text(document.page_content)

        for section in sections:
            section.metadata["source"] = source
            section.metadata["source_type"] = SourceType.MARKDOWN.value

        chunks = self.text_splitter.split_documents(sections)
        result: list[DocumentChunk] = []
        for ordinal, chunk in enumerate(chunks):
            metadata = dict(chunk.metadata)
            title = next(
                (metadata[key] for key in ("h6", "h5", "h4", "h3", "h2", "h1") if metadata.get(key)),
                None,
            )
            result.append(
                DocumentChunk(
                    chunk_id=str(uuid5(NAMESPACE_URL, f"{source_id}:{ordinal}:{chunk.page_content}")),
                    source_id=source_id,
                    source_type=SourceType.MARKDOWN,
                    content=chunk.page_content,
                    ordinal=ordinal,
                    title=title,
                    metadata=metadata,
                )
            )
        return result
