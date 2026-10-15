from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter

from settings import load_document_dir

class MarkdownLoader():
    def __init__(self):
        pass


    def load(self, file_name: str) -> list[Document]:
        file_path = load_document_dir() / file_name
        loader = TextLoader(file_path,  encoding="utf-8")
        docs = loader.load()
        markdownHeaderSplitter = MarkdownHeaderTextSplitter(
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
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        sections = markdownHeaderSplitter.split_text(docs[0].page_content)
        for section in sections:
            section.metadata['source'] = file_path.name
        chunks = text_splitter.split_documents(sections)
        return chunks


if __name__ == '__main__':
    mdLoader = MarkdownLoader()
    chunks = mdLoader.load('04-大模型接入与智能素材开发篇.md')
    print(len(chunks))
    for chunk in chunks:
        print(chunk)
