# Yan Pan, 2023

from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType


from prompts.DocumentQA import DocumentQA


class DocumentQAMultiple():

    def __init__(self):
        QA1 = DocumentQA(db_name="log-rolling", db_type="chroma")
        QA2 = DocumentQA(db_name="codebase-default", db_type="chroma")

        tools = [
            Tool(
                name="Logging",
                func=QA2.qa.run,
                description="""
You may find the logs (debug info, warning, info, errors) here.
Each line contains a json object,
and the last field ('time') contains a unix format time tag.
If your answer would need time,
please translate the unix time to human readable short date time.
                """.replace("\n", " "),
            ),
            Tool(
                name="Codebase",
                func=QA2.qa.run,
                description="""
The code base can be find here.
If question about why a certain warning/error occurred,
it is useful to find relevant code piece and perform analysis.
                """.replace("\n", " "),
            ),
        ]

        self.agent = initialize_agent(
            tools=tools,
            llm=QA1.llm,
            agent=AgentType.SELF_ASK_WITH_SEARCH,
            verbose=True,
            # return_intermediate_steps=True
        )

    def ask(self, question):
        return self.agent.run(question)
