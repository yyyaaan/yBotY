# Yan Pan, 2023
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
# Loaders are imported only when necessary

from settings.settings import Settings


class VectorStorage:
    """
    In support of NLP, stores the vector representations of documents
    """

    @staticmethod
    def chroma_create_persistent_db(
        source_file: str,
        db_name: str
    ) -> None:
        """
        embed a document (html, txt, doc) to vector and save to database
        db_name is also the folder name
        """
        source_file_ext = source_file.split(".")[-1].lower()

        if source_file_ext in ["html", "htm"]:
            from langchain.document_loaders import UnstructuredHTMLLoader
            loader = UnstructuredHTMLLoader(source_file)

        if source_file_ext in ["doc", "docx"]:
            from langchain.document_loaders import UnstructuredWordDocumentLoader  # noqa
            loader = UnstructuredWordDocumentLoader(source_file)

        if source_file_ext in ["md"]:
            from langchain.document_loaders import UnstructuredMarkdownLoader  # noqa
            loader = UnstructuredMarkdownLoader(source_file)

        if source_file_ext in ["txt"]:
            from langchain.document_loaders import TextLoader
            loader = TextLoader(source_file)

        documents = loader.load()
        texts = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
        ).split_documents(documents)

        settings = Settings()
        vector_db = Chroma.from_documents(
            documents=texts,
            embedding=OpenAIEmbeddings(openai_api_key=settings.OPENAI_KEY),
            persist_directory=f"{settings.CHROMA_PATH}/{db_name}",
        )
        vector_db.persist()
        del vector_db

        return None

    @staticmethod
    def chroma_delete_persistent_db(db_name: str):
        """
        delete a Chroma collection (i.e. the db)
        it is generally UNnecessary, flush the folder suffices
        """
        settings = Settings()
        vector_db = Chroma(
            embedding_function=OpenAIEmbeddings(openai_api_key=settings.OPENAI_KEY), # noqa
            persist_directory=f"{settings.CHROMA_PATH}/{db_name}",
        )
        print(f"Deleting persistent Chroma db {vector_db._collection.name}")
        vector_db.delete_collection()
