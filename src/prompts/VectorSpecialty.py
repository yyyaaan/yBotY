# Yan Pan, 2023
from datetime import datetime
from glob import glob
from langchain.document_loaders import TextLoader
from langchain.document_loaders.generic import GenericLoader
from langchain.document_loaders.parsers import LanguageParser
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pydantic import BaseModel

from prompts.VectorStorage import VectorStorage


# inherit NOT necessary (static method)
class VectorSpecialty(VectorStorage):
    """
    Implements storage interaction for special implementation:
    - load logs
    - load codebase
    """

    class InputCodeBaseSchema(BaseModel):
        collection_name: str
        path: str = "/app"
        language: str = "python"
        suffix: str = ".py"
        database: str = "elasticsearch"

    class InputLoadLogSchema(BaseModel):
        collection_name: str = "rolling"
        days: int = 1
        database: str = "elasticsearch"

    @staticmethod
    async def create_logs_db(
        name: str = "logs",
        database: str = "elasticsearch",
        days: int = 1,
        **kwargs,
    ):
        """automatic rolling: existing vector db will be removed"""

        try:
            await VectorStorage.delete_persistent_collection(
                collection_name=name, database=database
            )
        except Exception as e:
            print("create_logs_db: not deleted", e)

        int_today = int(f"{datetime.now():%Y%m%d}")
        # buffering logs (today) + matched previous days
        matched_logs = glob("/mnt/shared/fluentd/*/*.log")
        for i in range(days):
            matched_logs += glob(f"/mnt/shared/fluentd/*{int_today - i}.log")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
        )
        texts = []
        for x in matched_logs:
            texts.extend(splitter.split_documents(TextLoader(x).load()))

        params = {
            "source_file": "",
            "collection_name": name,
            "is_web_url": False,
            "predefined_texts": texts
        }

        if database.lower() == "chroma":
            VectorStorage.chroma_create_persistent_collection(**params)
        else:
            VectorStorage.elasticsearch_create_persistent_index(**params)

        return matched_logs

    @staticmethod
    def create_codebase_db(
        name: str = "codebase",
        database: str = "elasticsearch",
        path: str = "/app",
        language: str = "python",
        suffix: str = ".py",
        **kwargs,
    ):
        loader = GenericLoader.from_filesystem(
            path=path,
            glob="**/*",
            suffixes=suffix.split(","),
            parser=LanguageParser(language=language, parser_threshold=500)
        )
        documents = loader.load()
        docs_loaded = [x.metadata.get('source', '?') for x in documents]

        texts = RecursiveCharacterTextSplitter.from_language(
            language=language,
            chunk_size=2000,
            chunk_overlap=200
        ).split_documents(documents)

        params = {
            "source_file": "",
            "collection_name": name,
            "is_web_url": False,
            "predefined_texts": texts
        }

        if database.lower() == "chroma":
            VectorStorage.chroma_create_persistent_collection(**params)
        else:
            VectorStorage.elasticsearch_create_persistent_index(**params)

        return docs_loaded
