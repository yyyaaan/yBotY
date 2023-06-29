# Yan Pan, 2023
from langchain.chat_models import AzureChatOpenAI, ChatOpenAI

from settings.settings import Settings

class BaseOpenAI:
    """
    base class that initialized chat or llm for langchain
    """

    def __init__(self, 
                 temperature=0.7, 
                 model_name="gpt-3.5-turbo", 
                 using_azure=False,
                 **kwargs
    ):
        
        settings = Settings()

        if using_azure:
            self.llm = AzureChatOpenAI(
                temperature=temperature,
                deployment_name=settings.AZ_OPENAI_DEPLOYMENT,
                openai_api_type="azure",
                openai_api_key=settings.AZ_OPENAI_KEY,
                openai_api_base=settings.AZ_OPENAI_BASE,
                openai_api_version=settings.AZ_OPENAI_VERSION,
            )
        else:
            self.llm = ChatOpenAI(
                temperature=temperature,
                model_name=model_name,
                openai_api_key=settings.OPENAI_KEY
            )
        return None