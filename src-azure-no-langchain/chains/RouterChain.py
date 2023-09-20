# Yan Pan, 2023
from chains.FunctionCall import FunctionCall
from dependencies.dependencies import Dependencies
from dependencies.logger import logger
from settings import Configs, FUNCTIONS, PROMPTS


# %%
class RouterChain:
    """
    RouterChain is usually the entrance of a user prompt.
    It will choose and execute the function

    The intermediate steps are yield as informative text.
    The final answer is streaming.
    """

    @staticmethod
    async def docs_completion(
        dependencies: Dependencies,
        available_skills: dict,
        question: str,
        docIds: str = "",
        **kwargs
    ):
        msg = PROMPTS['routing_entry']
        if docIds is not None and len(docIds):
            msg += f" User provided document docIds='{docIds}' (can be single or comma separated list, do not change the format)."  # noqa: E501
        msg += f" User questions: {question}"

        #  RouterChain #1: routing to correction function
        ans_function_call = dependencies.chat_completion(
            messages=[{"role": "user", "content": msg}],
            functions=FUNCTIONS,
        )
        __usage = ans_function_call.get("usage", {})
        ans_function_call = ans_function_call["choices"][0]["message"]
        logger.info(f"RouterChain #1: {ans_function_call} {__usage}")

        # RouterChain #2: routing to function call
        call = ans_function_call.get("function_call", {})
        yield (
            f"> [GPT #1] I should use {call.get('name', '!error name')} "
            f"{call.get('arguments', '!error arguments')} "
            f"[total-tokens={__usage.get('total_tokens', '?')}]"
        )
        async for item in FunctionCall.route_to_function(
            dependencies=dependencies,
            available_skills=available_skills,
            **call.to_dict(),
        ):
            if isinstance(item, str):
                yield item
            else:
                messages_from_function = item
                logger.warn(messages_from_function)

        # RouterChain #3: answer completion
        for event in dependencies.chat_completion(
            messages_from_function, stream=True
        ):
            if len(event['choices']):
                yield event['choices'][0].get('delta', {}).get('content', '')
            else:
                yield Configs().string_trace_end
