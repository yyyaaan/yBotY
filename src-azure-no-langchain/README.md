# Experiments with Azure OpenAI and Azure Vector Search

- customizable embeddings and searching with Vector Search
- `sql` skills to interact with database
- Router based chat flow design
- MapReduce or Stuff is chosen based on content length (token num)
- traceable thought chain
- simple and lightweight: only FastAPI, Azure and OpenAI SDK
- can select, even mix use of GPT3.5 and GPT4 within a chat chain

> GPT-3.5-turbo 0613 or GPT-4 0613 is required for function calling.

This module and `FastAPI` routers should be __mounted or proxy from auth controller__.

## [Design Chart (link)](http://v2.yan.fi/llm-design)


## How to use: Python FastAPI with UI

At project root, build and run the docker image:

```
# build image and run
docker build -t azure-openai-exp . 
docker run -p 8009:9009 azure-openai-exp

# alternative for dev; observe code changes
docker compose up
```

> The python codes are under `/src/python/`. 

> Ensure the following environment variables are properly set (not a part of source-control)


```
# .env (dot-env)
CosmosDbConnectionString=?
CosmosDbExpName="experimental"

AzureSearchUrl=?
AzureSearchApiKey=?
AzureSearchExpName="experiments-documents"

OpenAIUrl=?
OpenAIApiKey=?
OpenAIDeployment="chat"     # gpt-35-turbo-16k
OpenAIEmbedding="embedding" # text-embedding-ada-002

OpenAIGPT4Url=?
OpenAIGPT4ApiKey=?
OpenAIGPT4Deployment="gpt-4"

# Sematic and Vector Config only when necessary
ConfigVectorSearchName=?
ConfigSemanticName=?
AzureSearchAdminKey=?

```

## Emission Data from Statistics Finland 

[Link](https://pxdata.stat.fi/PxWeb/pxweb/en/StatFin/StatFin__tilma/statfin_tilma_pxt_11ig.px/table/tableViewLayout1/)

## References

[Vector Database Query](https://learn.microsoft.com/en-us/azure/search/vector-search-how-to-query?tabs=portal-vector-query)

[Azure Search Filters, odata-filter-expr](https://learn.microsoft.com/en-us/azure/search/search-filters)

[OpenAI function calling](https://openai.com/blog/function-calling-and-other-api-updates) [Microsoft function calling](https://techcommunity.microsoft.com/t5/azure-ai-services-blog/function-calling-is-now-available-in-azure-openai-service/ba-p/3879241)

See: https://github.com/openai/openai-python/issues/418#issuecomment-1525939500

