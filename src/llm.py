from typing import Optional, Type

from dotenv import load_dotenv
from openai import AsyncOpenAI
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from pydantic import BaseModel

load_dotenv()
client = AsyncOpenAI()


async def get_completion(message: str, model: Optional[str] = "gpt-4o-mini") -> ChatCompletionMessage:
    """
    LLM completion with raw string response

    :param message: The message to send to the LLM.
    :param model: The model to use for the completion.
    :return: The raw string response from the LLM.
    """
    messages = [{"role": "user", "content": message}]
    response = await client.chat.completions.create(model=model, messages=messages)
    return response.choices[0].message.content


async def get_completion_structured(
    message: str, response_model: Type[BaseModel], model: str = "gpt-4o-mini"
) -> BaseModel:
    """
    Get a structured completions backed by pydantic validation

    :param message: The message to send to the LLM.
    :param response_model: The Pydantic model to parse the response into.
    :param model: The model to use for the completion.
    :return: The parsed Pydantic model instance.
    """
    messages = [{"role": "user", "content": message}]
    response = await client.beta.chat.completions.parse(model=model, messages=messages, response_format=response_model)

    if response.choices[0].message.refusal:
        raise Exception(f"Model refused to respond: {response.choices[0].message.refusal}")
    return response.choices[0].message.parsed
