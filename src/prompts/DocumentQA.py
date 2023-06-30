# Yan Pan, 2023
from langchain.callbacks import get_openai_callback
from langchain.chains import RetrievalQA
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma

from prompts.BaseOpenAI import BaseOpenAI
from settings.settings import Settings


class DocumentQA(BaseOpenAI):
    """
    Document QA backend with ChromaDB
    See ChromaDB must be existing - create it using VectorDB.create_from_file
    """

    CHAIN_TYPES = ["stuff", "map_reduce"]

    def __init__(
        self,
        db_name: str,
        chain_type: str = "stuff",
        temperature: float = 0.0,
        using_azure: bool = False
    ) -> None:

        if chain_type not in self.CHAIN_TYPES:
            raise ValueError(f"chain_type must be one of {self.CHAIN_TYPES}")

        super().__init__(temperature=temperature, using_azure=using_azure)

        settings = Settings()
        db = Chroma(
            persist_directory=f"{settings.CHROMA_PATH}/{db_name}",
            embedding_function=OpenAIEmbeddings(openai_api_key=settings.OPENAI_KEY), # noqa
        )

        self.qa = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type=chain_type,
            retriever=db.as_retriever(),
        )

        return None

    def ask(self, question: str) -> str:

        with get_openai_callback() as cb:
            response = self.qa.run(question)

        metrics = {
            "total_tokens": cb.total_tokens,
            "prompt_tokens": cb.prompt_tokens,
            "completion_tokens": cb.completion_tokens,
            "total_costs": cb.total_cost,
        }
        return {
            "response": response,
            "metrics": metrics
        }
