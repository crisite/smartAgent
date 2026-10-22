import uuid

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from schemas.document import DocumentChunk, SourceType
from settings import load_document_dir


class PdfLoader:
    def __init__(self, chunk_size: int=800, chunk_overlap: int=120):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

    def load(self, filename: str) -> list[DocumentChunk]:
        filePath = load_document_dir() / filename
        loader = PyPDFLoader(filePath)
        docs = loader.load()
        documentChunks: list[DocumentChunk] = []
        source_id = str(uuid.uuid5(uuid.NAMESPACE_OID, filename))
        source_type = SourceType.PDF
        display_name = filename
        title = docs[0].metadata['title']
        ordinal:int = 0
        """
            chunk_id: str = Field(min_length=1)
            source_id: str = Field(min_length=1)
            source_type: SourceType
            content: str = Field(min_length=1)
            ordinal: int = Field(ge=0)
            title: str | None = None
            page_start: int | None = Field(default=None, ge=1)
            page_end: int | None = Field(default=None, ge=1)
            chapter: str | None = None
            metadata: dict[str, Any] = Field(default_factory=dict)
        """

        sectionChunks: list[DocumentChunk] = []
        for doc in docs:
            sections = self.splitter.split_documents([doc])
            for section in sections:
                sectionChunks.append(DocumentChunk(
                    chunk_id=str(uuid.uuid5(uuid.NAMESPACE_OID, section.page_content)),
                    source_id=source_id,
                    source_type=source_type,
                    title=title,
                    ordinal=ordinal + 1,
                    content=section.page_content,
                    page_start=doc.metadata['page'] + 1,
                    page_end=doc.metadata['page'] + 1,
                ))
        return sectionChunks

if __name__ == '__main__':
    loader = PdfLoader()
    docs = loader.load('Python廖雪峰.pdf')

    for doc in docs:
        print(doc)
