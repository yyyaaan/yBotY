# Yan Pan, 2023
from langchain.chat_models import AzureChatOpenAI, ChatOpenAI

from settings.settings import Settings

class BaseOpenAI:
    """
    base class that initialized chat or llm for langchain
    """

    def __init__(self, 
                 init_chat=False, init_llm=False,
                 temperature=0.7, 
                 model_name="gpt-3.5-turbo", 
                 using_azure=False,
                 **kwargs
    ):

        if init_chat and using_azure:
            self.__init_azure_chat(temperature)
        if init_chat and not using_azure:
            self.__init_openai_chat(temperature, model_name)
        if init_llm and using_azure:
            self.__init_azure_llm(temperature)
        if init_llm and not using_azure:
            self.__init_openai_llm(temperature, model_name)
        
    def __init_azure_llm(self, temperature,  **kwargs):
        pass

    def __init_openai_llm(self, temperature, model_name, **kwargs):
        pass

    def __init_azure_chat(self, temperature,  **kwargs):
        settings = Settings()
        self.chat = AzureChatOpenAI(
            temperature=temperature,
            deployment_name=settings.AZ_OPENAI_DEPLOYMENT,
            openai_api_type="azure",
            openai_api_key=settings.AZ_OPENAI_KEY,
            openai_api_base=settings.AZ_OPENAI_BASE,
            openai_api_version=settings.AZ_OPENAI_VERSION,
        )

    def __init_openai_chat(self, temperature, model_name, **kwargs):
        settings = Settings()
        self.chat = ChatOpenAI(
            temperature=temperature,
            model_name=model_name,
            openai_api_key=settings.OPENAI_KEY
        )
