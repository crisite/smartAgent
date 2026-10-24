"""Load PDF pages into the common document-chunk representation."""

from uuid import NAMESPACE_URL, uuid5

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from schemas.document import DocumentChunk, SourceType
from settings import load_document_dir


class PdfLoader:
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 120):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def load(self, filename: str) -> list[DocumentChunk]:
        file_path = load_document_dir() / filename
        source = file_path.name
        source_id = str(uuid5(NAMESPACE_URL, f"{SourceType.PDF.value}:{source}"))
        pages = PyPDFLoader(file_path).load()

        result: list[DocumentChunk] = []
        for page_document in pages:
            page = int(page_document.metadata.get("page", 0)) + 1
            title = page_document.metadata.get("title") or file_path.stem
            metadata = dict(page_document.metadata)
            metadata.update({"source": source, "source_type": SourceType.PDF.value})
            for section in self.splitter.split_documents([page_document]):
                ordinal = len(result)
                result.append(
                    DocumentChunk(
                        chunk_id=str(uuid5(NAMESPACE_URL, f"{source_id}:{ordinal}:{section.page_content}")),
                        source_id=source_id,
                        source_type=SourceType.PDF,
                        title=title,
                        ordinal=ordinal,
                        content=section.page_content,
                        page_start=page,
                        page_end=page,
                        metadata=metadata,
                    )
                )
        return result
