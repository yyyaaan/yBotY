# Yan Pan, 2023
from typing import Any
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import ResponseSchema
from langchain.output_parsers import StructuredOutputParser

from prompts.BaseOpenAI import BaseOpenAI

class CodeAnalyzer(BaseOpenAI):
    """
    Simple code analyzer.
    """

    def __init__(self, temperature=0.0, using_azure=False) -> None:

        super().__init__(init_chat=True, temperature=temperature, using_azure=using_azure)

        self.template = ChatPromptTemplate.from_template("""
            Please determine the language of the code delimited by triple backticks. \
            Also, prepare a brief summary, review possible improvements and scan for security risks \
            using provided format after the code.
            Code ```{code}``` \
            Reply using json. {format}
        """.replace("  ", ""))

        self.parser = StructuredOutputParser.from_response_schemas([
            ResponseSchema(name="language", description="determine the language of the code provided"),
            ResponseSchema(name="description", description="briefly summarize the functionality of the code"),
            ResponseSchema(name="review", description="point out possible improvements, organize in a list"),
            ResponseSchema(name="security", description="check for security risks or bugs, reply OK if none")
        ])

    def analyze(self, code: str) -> dict[str, Any]:
        messages = self.template.format_messages(
            code=code,
            format=self.parser.get_format_instructions()
        )
        response = self.chat(messages)
        try:
            return self.parser.parse(response.content)
        except Exception as e:
            return {"response": response.content, "exception": str(e)}
