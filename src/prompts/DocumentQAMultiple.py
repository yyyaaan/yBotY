# Yan Pan, 2023

from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType


from prompts.DocumentQA import DocumentQA


class DocumentQAMultiple():

    def __init__(self) -> None:    
        QA1 = DocumentQA(db_name="log-rolling", db_type="chroma")
        QA2 = DocumentQA(db_name="codebase-default", db_type="chroma")

        tools = [
            Tool(
                name="Logging",
                func=QA2.qa.run,
                description="useful for when you need to answer questions find some logs, warnings, errors",
            ),
            Tool(
                name="Codebase",
                func=QA2.qa.run,
                description="useful for when you need to answer questions the python codebase and debug",
            ),
        ]

        self.agent = initialize_agent(
            tools=tools,
            llm=QA1.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            # return_intermediate_steps=True
        )

    def ask(self, question):
        return self.agent.run(question)
