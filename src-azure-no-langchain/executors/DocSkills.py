# Yan Pan 2023
import re
from asyncio import gather
from json import loads

from dependencies.dependencies import Dependencies
from dependencies.docprocessing import DocProcessing
from dependencies.logger import logger
from settings import Configs, PROMPTS


# %%
class DocSkills:
    """
    Wrapping the core skills from other Chains or Executors,
    Function Call handles only intermediate steps.

    It returns message list that is ready for final GPT completion,
    and thus supports token generation asynchronously
    """

    def __init__(self, dependencies: Dependencies) -> None:
        self.dependencies = dependencies

    def __docIds_to_filer_str(self, docIds):
        clean = [re.sub(r"[\'\"\s]", "", x) for x in docIds.split(",")]
        result = ""
        if len(clean) > 1:
            result = f"search.in(SourceId, '{','.join(clean)}', ',')"
        if len(clean) == 1:
            result = f"SourceId eq '{clean[0]}'"
        logger.debug(f"odata-filter: {result}")
        return result

    async def answer_question(
        self,
        docIds: str,
        query: str,
        note: str = "no note",
        **kwargs
    ):
        yield f"> [function] I don't need stuff previous messages as I have a note of length {len(note)}"  # noqa: E501
        yield f"> [function] I need to query the vector database for '{query}'"
        logger.info(f"> [function] performing vector search for '{query}'")
        search_results = self.dependencies.query_vector_search(
            query=query,
            filter=self.__docIds_to_filer_str(docIds),
        )
        context_text, counter = "", 0
        for one in search_results:
            source = one["SourceFileName"] + f" at {100*(one['PageNumber']+1)/one['TotalPages']:.0f}%"  # noqa: E501
            context_text += f"Context: {one['Content']}"
            context_text += f"Source: {source}. |||"
            counter += 1

        yield f"> [database] I have now access to {counter} context with source information"  # noqa: E501
        message_stuffed = f"""
            You have noted the user questions was: {note}.
            {PROMPTS['doc_content_is_provided']}
            {context_text}
            {PROMPTS['instruction_doc_source_format']}
        """
        n_tokens = DocProcessing.count_tokens(message_stuffed)
        yield f"> [GPT #2] I am ready to answer the question. [est-prompt-tokens={n_tokens}]"  # noqa: E501
        yield [{"role": "user", "content": message_stuffed}]

    async def summarize_document(
        self,
        docIds: str,
        note: str = "no note",
        **kwargs
    ):
        yield f"> [function] I don't need stuff previous messages as I have a note of length {len(note)}"  # noqa: E501
        yield "> [function] I need to find all chunks for the doc using traditional filter search"  # noqa: E501
        logger.info("> [function] performing filter search)")

        all_docs = self.dependencies.search_client.search(
            search_text="*",
            filter=self.__docIds_to_filer_str(docIds),
            select=["PageNumber", "Content"],
        )
        all_docs = [x for x in all_docs]
        len_docs = len(all_docs)
        yield f"> [database] I have found {len_docs} chunks, start MAPPING asynchronously"  # noqa: E501

        contents, usages = await self.__map_completions(
            message_contents=[
                f"You have made the notes: {note}. {PROMPTS['doc_summarize_map_chunk']} ```{x['Content']}```"  # noqa: E501
                for x in all_docs
            ]
        )
        yield f"> [GPT #2-#{len_docs+1}] Map summarization for all chunks completed [tokens={[x.get('total_tokens') for x in usages]}]"  # noqa: E501

        message_to_reduce = f"""
            You have noted the user questions was: {note}.
            {PROMPTS['doc_summarize_reduce']}
            {' '.join(contents)}
        """
        n_tokens = DocProcessing.count_tokens(message_to_reduce)
        yield f"> [GPT #{len_docs+2}] I am ready to provide the final summary. [est-prompt-tokens={n_tokens}]"  # noqa: E501
        yield [{"role": "user", "content": message_to_reduce}]

    def compare_documents(
        self,
        docIds: str,
        category: str = "reference",
        note: str = "no note",
        **kwargs
    ):
        """to be implemented"""
        return f"compared! {docIds} {category} {note}"
