# Yan Pan, 2023
from langchain.chains import RetrievalQA
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from pydantic import BaseModel

from prompts.BaseOpenAI import BaseOpenAI
from botSettings.settings import Settings


class DocumentQA(BaseOpenAI):
    """
    Document QA backend with ChromaDB
    See ChromaDB must be existing - create it using VectorDB.create_from_file
    """

    CHAIN_TYPES = ["stuff", "map_reduce", "refine"]

    class InputSchema(BaseModel):
        question: str

    class OutputSchema(BaseModel):
        response: str
        metrics: dict = {}

    def __init__(self, db_name: str, chain_type: str = "stuff", **kwargs):

        if chain_type not in self.CHAIN_TYPES:
            raise ValueError(f"chain_type must be one of {self.CHAIN_TYPES}")

        super().__init__(**kwargs)

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

        response = self.qa.run(question)
        return {
            "response": response,
            "metrics": self.collect_usage()
        }

    async def ask_stream(self, question: str):
        self.validate_streaming()

        task = self.create_asyncio_wrapped_task(
            self.qa.arun(question)
        )
        async for token in self.async_callback.aiter():
            yield token

        await task
        _ = self.collect_usage()
