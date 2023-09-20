# Yan Pan 2023
from json import loads
from pydantic_settings import BaseSettings


with open("prompts.json") as f:
    PROMPTS = loads(f.read())

FUNCTIONS = PROMPTS.pop("functions")
PROMPTS = PROMPTS.pop("prompts")


class Configs(BaseSettings):
    max_request_tokens: int = 4000
    string_trace_end: str = "--- END OF TRACING ---"

    sqlite_name: str = "sqlEmission.db"
    sql_emission_schema: str = """
    CREATE TABLE EmissionName (
        code TEXT PRIMARY KEY,
        text TEXT,
        comment TEXT
    )
    CREATE TABLE IndustryName (
        code TEXT PRIMARY KEY,
        text TEXT,
        comment TEXT
    )
    CREATE TABLE EmissionData (
        year INTEGER,
        emission_code TEXT,
        industry_code TEXT,
        number REAL,
        FOREIGN KEY(emission_code) REFERENCES EmissionName(code),
        FOREIGN KEY(industry_code) REFERENCES IndustryName(code)
    )
    """

    class Config:
        env_prefix = "config_"


class Credentials(BaseSettings):
    CosmosDbConnectionString: str
    CosmosDbExpName: str = "experimental"

    AzureSearchUrl: str
    AzureSearchApiKey: str
    AzureSearchExpName: str = "experiments-documents"

    OpenAIUrl: str
    OpenAIApiKey: str
    OpenAIDeployment: str = "chat"      # gpt-35-turbo-16k
    OpenAIEmbedding: str = "embedding"  # text-embedding-ada-002

    OpenAIGPT4Url: str
    OpenAIGPT4ApiKey: str
    OpenAIGPT4Deployment: str = "gpt-4"

    # only necessary for index creation
    ConfigVectorSearchName: str = "experiments-vector-config"
    ConfigSemanticName: str = "experiments-semantic-config"
    AzureSearchAdminKey: str

    class Config:
        env_prefix = ""
