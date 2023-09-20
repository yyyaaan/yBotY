# Yan Pan 2023
from dependencies.dependencies import Dependencies
from dependencies.docprocessing import DocProcessing
from dependencies.logger import logger
from settings import PROMPTS


class VectorDbListing:

    def __init__(self, dependencies: Dependencies) -> None:
        self.dependencies = dependencies

    async def list_documents(
        self,
        category: str = "",
        note: str = "no note",
        **kwargs
    ):
        yield "> [function] I need to find the doc titles using traditional filter search"  # noqa: E501
        logger.info(f"> [function] performing filter search, category={category})")  # noqa: E501

        docs = self.dependencies.filter_vector_search(
            # filter="",
            distinct=True, remove_scores=True
        )
        yield f"> [database] I have found {len(docs)} unique docs"  # noqa: E501
        message_to_organize = f"""
            You have noted: {note}. {PROMPTS['doc_list_from_search']} {docs}
        """
        n_tokens = DocProcessing.count_tokens(message_to_organize)
        yield f"> [GPT #2] I am ready to provide the list. [est-prompt-tokens={n_tokens}]"  # noqa: E501
        yield [{"role": "user", "content": message_to_organize}]
