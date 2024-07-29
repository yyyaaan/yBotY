# Yan Pan, 2023
from langchain.chains import RetrievalQA, RetrievalQAWithSourcesChain
from langchain_community.vectorstores import Chroma, ElasticsearchStore
from langchain_openai import OpenAIEmbeddings
from pydantic import BaseModel

from prompts.BaseOpenAI import BaseOpenAI
from botSettings.settings import Settings


class DocumentQA(BaseOpenAI):
    """
    Document QA backend
    vector collection must exist- create it using VectorDB.create_from_file
    """

    CHAIN_TYPES = ["stuff", "map_reduce", "refine"]

    class InputSchema(BaseModel):
        question: str
        database: str = "elasticsearch"
        collection: str = "default"
        temperature: float = 0.1
        model: str = "gpt-4o"
        include_source: bool = False

    class OutputSchema(BaseModel):
        response: str
        metrics: dict = {}

    def __init__(
        self,
        db_name: str,
        db_type: str = "elasticsearch",
        chain_type: str = "stuff",
        include_source: bool = False,
        **kwargs
    ):

        if chain_type not in self.CHAIN_TYPES:
            raise ValueError(f"chain_type must be one of {self.CHAIN_TYPES}")

        super().__init__(**kwargs)

        # different chain type if source is required!
        self.include_source = include_source
        ChainClass = RetrievalQAWithSourcesChain if include_source else RetrievalQA  # noqa: E501
        self.qa = ChainClass.from_chain_type(
            llm=self.llm,
            chain_type=chain_type,
            retriever=self.__configure_db(db_name, db_type),
            callbacks=[self.openai_callback],
        )

        return None

    def __configure_db(self, db_name: str, db_type: str):
        settings = Settings()
        embedding = OpenAIEmbeddings(openai_api_key=settings.OPENAI_KEY)
        if db_type.lower() == 'elasticsearch':
            db = ElasticsearchStore(
                index_name=db_name,
                embedding=embedding,
                es_url=settings.ELASTICSEARCH_URL
            )
            self.database = "elasticsearch"
        else:
            db = Chroma(
                persist_directory=f"{settings.CHROMA_PATH}/{db_name}",
                embedding_function=embedding,
            )
            self.database = "chroma"
        return db.as_retriever()

    def ask(self, question: str) -> str:

        response = self.qa.run(question)
        return {
            "response": response,
            "metrics": self.collect_usage()
        }

    async def ask_stream(self, question: str):
        self.validate_streaming()

        if self.include_source:
            task = self.create_asyncio_wrapped_task(
                self.qa.acall({"question": question}, return_only_outputs=False)  # noqa: E501
            )
        else:
            task = self.create_asyncio_wrapped_task(
                self.qa.arun(question)
            )

        async for token in self.async_callback.aiter():
            yield token

        await task
        print(self.result)
        print(type(self.result))
        _ = self.collect_usage()

# %%
