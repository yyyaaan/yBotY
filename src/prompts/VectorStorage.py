# Yan Pan, 2023
from glob import glob
from httpx import AsyncClient
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma, ElasticsearchStore
from os import system
from pydantic import BaseModel

# Loaders are imported only when necessary
from botSettings.settings import Settings


class VectorStorage:
    """
    In support of NLP, stores the vector representations of documents
    """

    class InputSchema(BaseModel):
        source_file: str
        collection_name: str
        is_web_url: bool = False
        database: str = "elasticsearch"

    class InputDelSchema(BaseModel):
        collection_name: str

    class InputDelFileSchema(BaseModel):
        filename: str

    @staticmethod
    def delete_filesystem_file(filename):
        upload_dir = Settings().UPLOAD_PATH
        if upload_dir not in filename:
            filename = f"{upload_dir}/{filename}"
        system(f'rm -f "{filename}"')
        return None

    @staticmethod
    async def list_vector_db_set():
        try:
            async with AsyncClient() as client:
                res = await client.get(url=f"{Settings().ELASTICSEARCH_URL}/_aliases")  # noqa: E501
            if res.status_code > 299:
                raise Exception(f"Elastic Search not available {res.text}")
            indices = [k for k, _ in res.json().items() if not k.startswith(".")]
        except Exception as e:
            raise Exception(f"Elastic Search not available {e}")
        return {
            "chroma": [x.split("/")[-1] for x in glob(f"{Settings().CHROMA_PATH}/*")],  # noqa: E501
            "elasticsearch": indices,
        }

    @staticmethod
    def prepare_documents(
        source_file: str,
        is_web_url: bool = False
    ):
        """used by chroma/elasticsearch_create_..."""
        file_dir = Settings().UPLOAD_PATH
        if (not is_web_url) and (file_dir not in source_file):
            source_file = f"{file_dir}/{source_file}"
        source_file_ext = source_file.split(".")[-1].lower()

        # from langchain.document_loaders import DataFrameLoader

        if is_web_url:
            from langchain.document_loaders import WebBaseLoader
            loader = WebBaseLoader(source_file)

        elif source_file_ext in ["html", "htm"]:
            # from langchain.document_loaders import UnstructuredHTMLLoader
            # bs_kwargs={"features": "html.parser"}
            from langchain.document_loaders import BSHTMLLoader
            loader = BSHTMLLoader(file_path=source_file),

        elif source_file_ext in ["csv"]:
            from langchain.document_loaders import UnstructuredCSVLoader
            loader = UnstructuredCSVLoader(source_file)

        elif source_file_ext in ["doc", "docx"]:
            from langchain.document_loaders import UnstructuredWordDocumentLoader  # noqa
            loader = UnstructuredWordDocumentLoader(source_file)

        elif source_file_ext in ["pdf"]:
            from langchain.document_loaders import UnstructuredPDFLoader
            loader = UnstructuredPDFLoader(source_file)

        elif source_file_ext in ["md"]:
            from langchain.document_loaders import UnstructuredMarkdownLoader  # noqa
            loader = UnstructuredMarkdownLoader(source_file)

        elif source_file_ext in ["txt"]:
            from langchain.document_loaders import TextLoader
            loader = TextLoader(source_file)

        else:
            raise ValueError("Unsupported file type")

        documents = loader.load()
        texts = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
        ).split_documents(documents)

        return texts

    @staticmethod
    def chroma_create_persistent_collection(
        source_file: str,
        collection_name: str,
        is_web_url: bool = False
    ) -> None:
        """
        embed a document (html, txt, doc) to vector and save to database
        when is_web_url is true, shortcut to download and parse file
        collection_name is also the folder name
        """
        settings = Settings()
        vector_db = Chroma.from_documents(
            documents=VectorStorage.prepare_documents(source_file, is_web_url),
            embedding=OpenAIEmbeddings(openai_api_key=settings.OPENAI_KEY),
            persist_directory=f"{settings.CHROMA_PATH}/{collection_name}",
        )
        vector_db.persist()
        del vector_db

        return None

    @staticmethod
    def chroma_delete_persistent_collection(
        collection_name: str, use_chroma=False
    ):
        """
        delete a Chroma collection, and flush the folder
        """
        settings = Settings()
        collection_dir = f"{settings.CHROMA_PATH}/{collection_name}"

        if use_chroma:
            vector_db = Chroma(
                embedding_function=OpenAIEmbeddings(openai_api_key=settings.OPENAI_KEY), # noqa
                persist_directory=collection_dir,
            )
            print(f"DEL Chroma DB Collection {vector_db._collection.name}")
            vector_db.delete_collection()

        system(f"rm -rf {collection_dir}")

    @staticmethod
    def elasticsearch_create_persistent_index(
        source_file: str,
        collection_name: str,
        is_web_url: bool = False
    ):
        settings = Settings()
        es = ElasticsearchStore.from_documents(
            documents=VectorStorage.prepare_documents(source_file, is_web_url),
            index_name=collection_name,
            embedding=OpenAIEmbeddings(openai_api_key=settings.OPENAI_KEY),
            es_url=settings.ELASTICSEARCH_URL,
        )
        es.client.indices.refresh(index=collection_name)
        return None