# Yan Pan, 2023
from langchain.callbacks import get_openai_callback
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from pydantic import BaseModel
from typing import Optional

from prompts.BaseOpenAI import BaseOpenAI


class CodeAnalyzer(BaseOpenAI):
    """
    Simple code analyzer.
    """

    class InputSchema(BaseModel):
        code: str

    class OutputSchema(BaseModel):
        language: Optional[str]
        description: Optional[str]
        review: Optional[str]
        security: Optional[str]
        exception: Optional[dict]
        metrics: Optional[dict]

    def __init__(self, temperature=0.0, using_azure=False, streaming=False):

        super().__init__(
            temperature=temperature,
            using_azure=using_azure,
            streaming=streaming
        )

        self.template = ChatPromptTemplate.from_template("""
            Please determine the language of the code delimited \
            by triple backticks. Also, prepare a brief summary, \
            review possible improvements and scan for security risks \
            using provided format after the code.
            Code ```{code}``` \
            {format}
        """.replace("  ", ""))

        self.parser = StructuredOutputParser.from_response_schemas([
            ResponseSchema(name="language", description="determine the language of the code provided"),         # noqa
            ResponseSchema(name="description", description="briefly summarize the functionality of the code"),  # noqa
            ResponseSchema(name="review", description="point out possible improvements, organize in a list"),   # noqa
            ResponseSchema(name="security", description="check for security risks or bugs, reply OK if none")   # noqa
        ])

    def analyze(self, code: str) -> dict[str, list]:
        messages = self.template.format_messages(
            code=code,
            format=self.parser.get_format_instructions()
        )

        with get_openai_callback() as cb:
            response = self.llm(messages)

        metrics = {
            "total_tokens": cb.total_tokens,
            "prompt_tokens": cb.prompt_tokens,
            "completion_tokens": cb.completion_tokens,
            "total_costs": cb.total_cost,
        }
        try:
            return {**self.parser.parse(response.content), "metrics": metrics}
        except Exception as e:
            return {"exception": {
                "content": response.content,
                "exception": str(e)}
            }

    async def analyze_stream(self, code: str):
        """
        stream the outputs, where json parser is no longer possible
        """
        self.validate_streaming()

        messages = self.template.format_messages(code=code, format="")
        task = self.create_asyncio_wrapped_task(
            self.llm.agenerate([messages])
        )
        async for token in self.async_callback.aiter():
            yield token

        await task
