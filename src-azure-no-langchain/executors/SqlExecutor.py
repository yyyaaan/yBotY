# Yan Pan 2023
from json import loads
from sqlite3 import connect as connect_sql

from dependencies.dependencies import Dependencies
from dependencies.logger import logger
from settings import Configs


# %%
class SqlExecutor:
    function_calls_sql = [{
        "name": "query",
        "description": "retrieve the sql results given a query",
        "parameters": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "the sql query needs to be executed",
                },
                "note": {
                    "type": "string",
                    "description": "put user question and your findings here"
                }
            },
            "required":  ["note"]
        }
    }]

    def __init__(self, dependencies: Dependencies) -> None:
        self.dependencies = dependencies

    async def query_sql_database(
        self,
        db: str = "error",
        note: str = "",
        **kwargs
    ):
        yield f"> [function] I need to query from database `{db}` and I should see schemas"  # noqa: E501

        self.db = db
        if db == "sqlEmission.db":
            schema = Configs().sql_emission_schema
        else:
            schema = ""
            yield [{
                "role": "system",
                "content": f"please tell the user that there is no such database {db} to use"  # noqa: E501
            }]
            return 

        message_with_sql_schema = f"""
        You have noted that the user question was: ```{note}```.
        The relevant sql schema is: ```{schema}```
        Please write the SQL query and call the function `query`.
        """
        yield "> [function] I have now access to the schema, and I should write SQL statements"

        message_call_sql = {"role": "user", "content": message_with_sql_schema}
        sql_call = self.dependencies.chat_completion(
            messages=[message_call_sql],
            functions=SqlExecutor.function_calls_sql
        )
        try:
            sql_call = sql_call["choices"][0]["message"]
            args = sql_call.get("function_call", {}).get("arguments")
            args = loads(args)
            yield f"> [SQL] {args.get('sql', 'error')}"  # noqa: E501')}"
            sql_result = self.sql_query(**args)
            yield [{
                "role": "user",
                "content": f"""
                User asked questions: ```{note}```.
                You have now the data from sql below, and you should be able to answer it accordingly
                ```{sql_result}```
                """
            }]
        except Exception as e:
            yield [{
                "role": "system",
                "content": f"please tell the user that the failed to call sql {e}"  # noqa: E501
            }]

    def sql_query(self, sql, **kwargs):
        conn = connect_sql(self.db)
        res = conn.cursor().execute(sql).fetchall()
        conn.close()
        logger.info(f"db {self.db} query results has length {len(res)}")
        return res
