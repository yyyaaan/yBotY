# Yan Pan, 2023
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
        temperature: float = 0.1
        model: str = "gpt-3.5-turbo"

    class OutputSchema(BaseModel):
        language: Optional[str] = ""
        description: Optional[str] = ""
        review: Optional[str] = ""
        security: Optional[str] = ""
        exception: Optional[dict] = {}
        metrics: Optional[dict] = {}

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

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

        response = self.llm(messages)

        try:
            return {
                **self.parser.parse(response.content),
                "metrics": self.collect_usage()
            }
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
        _ = self.collect_usage()
