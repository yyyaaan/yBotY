# Yan Pan 2023 | Experimental Code, NOT FOR PROD
# %%
import numpy as np
import openai
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient, models
from azure.search.documents.models import Vector
from uuid import uuid4

from dependencies.docprocessing import DocProcessing
from dependencies.logger import logger
from settings import Credentials


# %% Configuration and Clients
class Dependencies:

    search_client = None
    credentials = Credentials()

    def __init__(
        self,
        use_gpt4=False,
        use_experimental_search=True,
    ):

        self.use_gpt4 = use_gpt4
        self.search_fields = [  # default fields, no Content
            "id",
            "SourceFileName",
            "SourceUrl",
            "PageNumber",
            "TotalPages",
            "SourceId",
        ]

        if use_experimental_search:
            self.search_client = SearchClient(
                endpoint=self.credentials.AzureSearchUrl,
                credential=AzureKeyCredential(self.credentials.AzureSearchApiKey),  # noqa: E501
                index_name=self.credentials.AzureSearchExpName,
            )
            self.search_fields.extend(["Category", "Tier", "TokenCount"])
        else:
            self.search_client = SearchClient(
                endpoint=self.credentials.AzureSearchUrl,
                credential=AzureKeyCredential(self.credentials.AzureSearchApiKey),  # noqa: E501
                index_name="tietoevry-chat-documents",
            )

    def chat_completion(self, messages, **kwargs):
        """wrapper to use either gpt3.5-turbo or gpt-4"""
        if self.use_gpt4:
            return self.chat_completion_gpt4(messages, **kwargs)
        return self.chat_completion_gpt3_5(messages, **kwargs)

    def chat_completion_gpt3_5(
        self, messages: list, functions: list = [],
        stream=False, return_coroutine=False
    ):
        openai_args = {
            "deployment_id": "chat",
            "model": "gpt-4o",
            "api_key": self.credentials.OpenAIApiKey,
            "api_base": self.credentials.OpenAIUrl,
            "api_type": "azure",
            "api_version": "2023-08-01-preview",
            "messages": messages
        }
        if len(functions):
            openai_args["functions"] = functions
        if return_coroutine:
            return openai.ChatCompletion.acreate(**openai_args)
        return openai.ChatCompletion.create(**openai_args, stream=stream)

    def chat_completion_gpt4(
        self, messages: list, functions: list = [],
        stream=False, return_coroutine=False
    ):
        openai_args = {
            "deployment_id": "gpt-4",
            "model": "gpt-4",
            "api_key": self.credentials.OpenAIGPT4ApiKey,
            "api_base": self.credentials.OpenAIGPT4Url,
            "api_type": "azure",
            "api_version": "2023-08-01-preview",
            "messages": messages
        }
        if len(functions):
            openai_args["functions"] = functions
        if return_coroutine:
            return openai.ChatCompletion.acreate(**openai_args)
        return openai.ChatCompletion.create(**openai_args, stream=stream)

    def query_vector_search(self, query, filter="", k=3, **kwargs):
        vector = Vector(
            value=self.embed_text_chunk(query),
            fields="EmbeddingVector",
            k=k
        )
        res = [x for x in self.search_client.search(
            search_text="*",
            filter=filter,
            vectors=[vector],
            select=["PageNumber", "Content", *self.search_fields],
            **kwargs
        )]
        logger.info(f"Vector Search k={k} scores=" + " ".join([str(x.get('@search.score')) for x in res]))  # noqa: E501
        return res

    def filter_vector_search(
        self,
        filter="",
        distinct=True,
        remove_scores=True,
        **kwargs
    ):
        params = {
            "search_text": "*",
            "select": ["SourceUrl", *self.search_fields],
            **kwargs
        }
        if filter is not None and len(filter):
            params["filter"] = filter

        all_docs = [x for x in self.search_client.search(**params)]

        condition = lambda x: (not x.startswith("@")) if remove_scores else True  # noqa: E501, E731
        logger.info(f"Filter Search has {len(all_docs)} results")

        if not distinct:
            return [
                {k: v for k, v in one.items() if condition}
                for one in all_docs
            ]

        unique_ids = set()
        unique_docs = []
        for one in all_docs:
            if one["SourceId"] not in unique_ids:
                unique_ids.add(one["SourceId"])
                unique_docs.append({k: v for k, v in one.items() if condition(k)})  # noqa: E501

        return sorted(unique_docs, key=lambda k: k.get("SourceFileName", "."))

    def embed_text_chunk(self, text: str):
        openai_config = {
            "deployment_id": self.credentials.OpenAIEmbedding,
            "api_key": self.credentials.OpenAIApiKey,
            "api_base": self.credentials.OpenAIUrl,
            "api_type": "azure",
            "api_version": "2023-08-01-preview",
        }
        response = openai.Embedding.create(
            **openai_config,
            input=text,
        )
        embeddings = response['data'][0]['embedding']
        return embeddings

    def embed_text(
        self,
        text: str,
        max_tokens: int = 1500,
        overlapping_sentences: int = 2,
        adjust_weight: bool = False
    ):
        """
        auto chunking based on max words allowed in each chunk
        IMPORTANT: use number of words for normalization, approximate tokens
        """
        texts = DocProcessing.chunk_text_by_sentences(
            text, max_tokens, overlapping_sentences
        )

        # count tokens
        n_tokens = [DocProcessing.count_tokens(text) for text in texts]
        weights = [x / sum(n_tokens) for x in n_tokens]

        embeddings = [self.embed_text_chunk(text) for text in texts]
        if adjust_weight and len(texts) > 1:
            # weighting and normalization NOT necessary
            # if chunked less than max token
            results = []
            for em, weight in zip(embeddings, weights):
                weight_adjusted = em * weight
                normalized = weight_adjusted / np.linalg.norm(weight_adjusted)
                results.append(normalized.tolist())
            embeddings = results

        return [{
            "text": a,
            "embedding": b,
            "token_count": DocProcessing.count_tokens(a),
        } for a, b in zip(texts, embeddings)]

    def embed_and_upload_docs(
        self,
        Content: str,
        SourceFileName: str,
        SourceId: str,
        SourceUrl: str,
        ChunkTitle: str,
        Category: str,
        TextOffset: int,
        Tier: int = 0,
        max_tokens: int = 1500,
    ):
        """to match index fields"""

        embedded = self.embed_text(Content, max_tokens=max_tokens)

        items = [{
            "id": uuid4().hex,  # hex for chunk id, str value for doc id
            "Content": x["text"],
            "SourceFileName": SourceFileName,
            "SourceId": SourceId,
            "SourceUrl": SourceUrl,
            "ChunkTitle": ChunkTitle,
            "Category": Category,
            "Tier": Tier,
            "TokenCount": x["token_count"],
            "PageNumber": i,
            "TotalPages": len(embedded),
            "TextOffset": TextOffset,
            "EmbeddingVector": x["embedding"],
        } for i, x in enumerate(embedded)]

        res = self.search_client.upload_documents(items)
        return res

    @staticmethod
    def create_or_update_search_index():
        """
        ONLY need for initial setup, no need for rerun. Admin required
        VectorSearch and Semantic are default
        fields are matching C# DocumentSearchService.SearchableDocumentChunk
        """

        credentials = Credentials()

        index_client = SearchIndexClient(
            endpoint=credentials.AzureSearchUrl,
            credential=AzureKeyCredential(credentials.AzureSearchAdminKey),
        )

        vector_search_config = models.VectorSearch(
            algorithm_configurations=[
                models.HnswVectorSearchAlgorithmConfiguration(
                    name=credentials.ConfigVectorSearchName,
                    kind="hnsw",
                    parameters={
                        "m": 4,
                        "efConstruction": 400,
                        "efSearch": 500,
                        "metric": "cosine"
                    }
                )
            ]
        )

        semantic_config = models.SemanticConfiguration(
            name=credentials.ConfigSemanticName,
            prioritized_fields=models.PrioritizedFields(
                title_field=models.SemanticField(field_name="ChunkTitle"),
                prioritized_content_fields=[
                    models.SemanticField(field_name="Content")
                ],
                prioritized_keywords_fields=[],
            )
        )

        __t_str = {"type": models.SearchFieldDataType.String}
        __t_int = {"type": models.SearchFieldDataType.Int32}

        fields = [
            models.SimpleField(
                name="id", key=True, filterable=True, **__t_str
            ),
            models.SearchableField(
                name="Content", **__t_str, analyzer_name="en.lucene"
            ),
            models.SimpleField(name="SourceFileName", **__t_str),
            models.SimpleField(name="SourceId", filterable=True, **__t_str),
            models.SimpleField(name="SourceUrl", filterable=True, **__t_str),
            models.SimpleField(name="ChunkTitle", filterable=True, **__t_str),
            models.SimpleField(name="Category", filterable=True, **__t_str),
            models.SimpleField(name="Tier", filterable=True, **__t_int),
            models.SimpleField(name="TokenCount", **__t_int),
            models.SimpleField(name="PageNumber", **__t_int),
            models.SimpleField(name="TotalPages", **__t_int),
            models.SimpleField(name="TextOffset", **__t_int),
            models.SearchField(
                name="EmbeddingVector",
                searchable=True,
                vector_search_dimensions=1536,
                type=models.SearchFieldDataType.Collection(models.SearchFieldDataType.Single),  # noqa: E501
                vector_search_configuration="experiments-vector-config"
            )
        ]

        index_to_create = models.SearchIndex(
            name=credentials.AzureSearchExpName,
            fields=fields,
            vector_search=vector_search_config,
            semantic_settings=models.SemanticSettings(
                configurations=[semantic_config]
            ),
        )
        result = index_client.create_or_update_index(index_to_create)

        logger.info(result)
# %%
