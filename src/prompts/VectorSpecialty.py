# Yan Pan, 2023
from langchain.document_loaders.generic import GenericLoader
from langchain.document_loaders.parsers import LanguageParser
from langchain.text_splitter import RecursiveCharacterTextSplitter

from prompts.VectorStorage import VectorStorage


# inherit NOT necessary (static method)
class VectorSpecialty(VectorStorage):
    """
    Implements storage interaction for special implementation:
    - load logs
    - load codebase
    """

    @staticmethod
    def create_codebase_db(
        name: str = "codebase",
        database: str = "elasticsearch",
        path: str = "/app",
        language: str = "python",
        suffix: str = ".py",
        **kwargs,
    ):
        
        print("moved!")
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
