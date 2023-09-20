# Yan Pan 2023
from inspect import getmembers, isfunction, ismethod
from json import loads
from json.decoder import JSONDecodeError

from dependencies.dependencies import Dependencies
from dependencies.logger import logger
from executors.DocSkills import DocSkills
from executors.SqlExecutor import SqlExecutor
from executors.VectorDbListing import VectorDbListing


class FunctionCall:
    """
    Wrapping the core skills from other Chains or Executors,
    Function Call handles only intermediate steps.

    It returns message list that is ready for final GPT completion,
    and thus supports token generation asynchronously
    """

    @staticmethod
    async def route_to_function(
        dependencies: Dependencies,
        available_skills: dict,
        name: str,
        arguments: str,  # json-loadable
        **kwargs
    ):
        """
        routing to correct function based on name
        available_skills --> see collect_available_skills below
        """
        # handle possible format issue
        try:
            parsed_arguments = loads(arguments)
        except JSONDecodeError:
            yield [{
                "role": "system",
                "content": "you need to tell user that the system failed to generating answer due to mal-formatted arguments"  # noqa: E501
            }]
            return

        # call the functions, and continuous yield token/message
        try:
            class_instance_to_use = available_skills[name](dependencies)
            logger.error(class_instance_to_use)
            class_methods = dict(getmembers(class_instance_to_use, ismethod))
            logger.error(class_methods)
            func_to_call = class_methods[name]
            async for item in func_to_call(**parsed_arguments):
                yield item
        except Exception as e:
            yield [{
                "role": "system",
                "content": f"please tell the user that the system failed to perform function calling failed due to {e}"  # noqa: E501
            }]

    @staticmethod
    def collect_available_skills():
        """
        should be used in app startup
        returns {str_name: class reference}
        helps prevention of injection risk with 'eval'
        """
        skills = {}
        for the_class in [DocSkills, SqlExecutor, VectorDbListing]:
            for name, _ in getmembers(the_class, predicate=isfunction):
                if not name.startswith("_"):
                    skills[name] = the_class
        logger.info(
            f"Loaded {len(skills)} skills available for LLM" + "\n -" +
            "\n -".join(sorted([str(k) for k in skills.keys()]))
        )
        return skills
