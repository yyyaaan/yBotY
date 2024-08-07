# Yan Pan, 2023
from asyncio import create_task, Event, Task
from langchain.callbacks import AsyncIteratorCallbackHandler # noqa
from typing import AsyncIterable, Awaitable
from botSettings.settings import Settings
from langchain_community.callbacks import OpenAICallbackHandler
from langchain_core.outputs import LLMResult
from langchain_openai import AzureChatOpenAI, ChatOpenAI


class BaseOpenAI:
    """
    base class that initialized chat or llm for langchain
    tracing: callable function that takes dict as input - record OpenAI usage
    """

    def __init__(
        self,
        temperature: float = 0.7,
        model_name: str = "gpt-4o",
        using_azure: bool = False,
        streaming: bool = False,
        trace_func: callable = print,
        **kwargs,
    ):
        settings = Settings()
        self.openai_callback = OpenAICallbackHandler()
        self.trace = trace_func  # callable
        self.database = "unspecified"
        self.result = None # only available for async

        if streaming:
            self.async_callback = AsyncIteratorCallbackHandler()
            llm_streaming_kwargs = {
                "streaming": True,
                "callbacks": [self.async_callback, self.openai_callback]
            }
        else:
            llm_streaming_kwargs = {
                "streaming": False,
                "callbacks": [self.openai_callback]
            }

        if using_azure:
            self.llm = AzureChatOpenAI(
                **llm_streaming_kwargs,
                temperature=temperature,
                deployment_name=settings.AZ_OPENAI_DEPLOYMENT,
                openai_api_type="azure",
                openai_api_key=settings.AZ_OPENAI_KEY,
                openai_api_base=settings.AZ_OPENAI_BASE,
                openai_api_version=settings.AZ_OPENAI_VERSION,
            )
        else:
            self.llm = ChatOpenAI(
                **llm_streaming_kwargs,
                temperature=temperature,
                model_name=model_name,
                openai_api_key=settings.OPENAI_KEY
            )

        return None

    def collect_usage(self) -> dict:
        try:
            usage = {
                "cls": self.__class__.__name__,
                "database": self.database,
                "model_name": self.llm.model_name,
                "streaming": self.llm.streaming,
                "total_tokens": self.openai_callback.total_tokens,
                "prompt_tokens": self.openai_callback.prompt_tokens,
                "completion_tokens": self.openai_callback.completion_tokens,
                "total_costs": self.openai_callback.total_cost,
            }
            self.trace(usage)
            return usage
        except Exception as e:
            print(e)
            return {}

    def validate_streaming(self):
        if self.llm.streaming:
            pass
        else:
            raise Exception("Require initialization with streaming=True")

    # below supports token/word streaming
    async def wrap_done(self, fn: Awaitable, event: Event):
        """Wrap an awaitable, event on done or on exception"""
        try:
            self.result = await fn
        except Exception as e:
            print(f"Caught exception: {e}")
        finally:
            event.set()

    def create_asyncio_wrapped_task(self, llm_result: LLMResult) -> Task:
        return create_task(
            self.wrap_done(llm_result, self.async_callback.done)
        )

    async def __stream(self, llm_result: LLMResult) -> AsyncIterable[str]:
        """
        Wrap the stream output.
        llm_result must be a async object, for example model.agenereate
        """
        # task = create_task(self.wrap_done(
        #     llm_result, self.async_callback.done
        # ))
        task = self.create_asyncio_wrapped_task(llm_result)
        async for token in self.async_callback.aiter():
            yield f"{token} "
        await task
