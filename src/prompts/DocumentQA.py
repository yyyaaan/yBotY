# Yan Pan, 2023
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma, DocArrayInMemorySearch

from prompts.BaseOpenAI import BaseOpenAI
from settings.settings import Settings


class DocumentQA(BaseOpenAI):
    """
    Document QA backend with ChromaDB, use static method to create a persistent db.
    """

    @staticmethod
    def create_persistent_chroma_db(
        source_file: str = "",
        directory: str = "default",
    ):
        """create chroma embeddings DB from text file"""

        chroma_dir = f"{Settings().CHROMA_PATH}/{directory}"

        if source_file.lower().endswith(".html"):
            from langchain.document_loaders import UnstructuredHTMLLoader
            loader = UnstructuredHTMLLoader(source_file)

        if source_file.lower().endswith(".txt"):
            from langchain.document_loaders import TextLoader
            loader = TextLoader(source_file)

        documents = loader.load()

        texts = RecursiveCharacterTextSplitter(
            chunk_size = 1000,
            chunk_overlap = 100,
        ).split_documents(documents)

        vector_db = Chroma.from_documents(
            documents = texts, 
            embedding = OpenAIEmbeddings(), 
            persist_directory = chroma_dir,
        )
        vector_db.persist()
        del vector_db
        return None

    def __init__(self, temperature=0.0, using_azure=False):
        super().__init__(temperature=temperature, using_azure=using_azure)

        self.db = DocArrayInMemorySearch(
            vector_store=UnstructuredHTMLLoader(file_path="me.html").load(),
            embedding=OpenAIEmbeddings()
        )
        
        # db = Chroma.from_documents(docs, embeddings)

        self.qa = RetrievalQA.from_chain_type(
            llm=ChatOpenAI(temperature = 0.0), 
            chain_type="stuff", # "stuff", 
            retriever=db.as_retriever(), 
            verbose=True
)