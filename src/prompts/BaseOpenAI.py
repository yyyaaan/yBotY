# Yan Pan, 2023
from asyncio import create_task, Event
from langchain.callbacks import AsyncIteratorCallbackHandler
from langchain.chat_models import AzureChatOpenAI, ChatOpenAI
from langchain.schema import LLMResult
from typing import AsyncIterable, Awaitable
from settings.settings import Settings


class BaseOpenAI:
    """
    base class that initialized chat or llm for langchain
    """

    def __init__(
        self,
        temperature: float = 0.7,
        model_name: str = "gpt-3.5-turbo",
        using_azure: bool = False,
        streaming: bool = False,
        **kwargs,
    ):
        settings = Settings()

        if streaming:
            self.async_callback = AsyncIteratorCallbackHandler()
            llm_streaming_kwargs = {
                "streaming": True,
                "callbacks": [self.async_callback]
            }
        else:
            llm_streaming_kwargs = {"streaming": False}

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

    async def wrap_done(self, fn: Awaitable, event: Event):
        """Wrap an awaitable, event on done or on exception"""
        try:
            await fn
        except Exception as e:
            print(f"Caught exception: {e}")
        finally:
            event.set()

    async def __stream(self, llm_result: LLMResult) -> AsyncIterable[str]:
        """
        Wrap the stream output.
        llm_result must be a async object, for example model.agenereate
        """

        task = create_task(self.wrap_done(
            llm_result, self.async_callback.done
        ))
        async for token in self.async_callback.aiter():
            yield f"{token} "
        await task
