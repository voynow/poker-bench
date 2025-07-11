import csv
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Type

from dotenv import load_dotenv
from openai import AsyncOpenAI
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from pydantic import BaseModel

load_dotenv()
client = AsyncOpenAI()

# Pricing per million tokens (as of current rates)
MODEL_PRICING = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
    "gpt-4.1-nano": {"input": 0.10, "output": 0.40},
}


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> tuple[float, float, float]:
    """
    Calculate input, output, and total costs for a model call.

    :param model: The model to use for the completion.
    :param input_tokens: The number of input tokens used.
    :param output_tokens: The number of output tokens used.
    :return: A tuple containing the input cost, output cost, and total cost.
    """
    if model not in MODEL_PRICING:
        raise ValueError(f"Cannot calculate cost for model: {model}")

    pricing = MODEL_PRICING[model]
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    total_cost = input_cost + output_cost
    return input_cost, output_cost, total_cost


def clear_llm_log() -> None:
    """Clear the LLM usage log file to start fresh."""
    log_file = Path("llm_usage_log.csv")
    if log_file.exists():
        log_file.unlink()


def log_llm_call(
    model: str,
    function_name: str,
    input_content: str,
    output_content: str,
    input_tokens: int,
    output_tokens: int,
    latency_ms: int,
) -> None:
    """Log LLM call data to CSV file for analysis."""
    log_file = Path("llm_usage_log.csv")

    # Create header if file doesn't exist
    if not log_file.exists():
        with open(log_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "timestamp",
                    "model",
                    "function_name",
                    "input_content_preview",
                    "output_content_preview",
                    "input_tokens",
                    "output_tokens",
                    "total_tokens",
                    "latency_ms",
                    "input_cost",
                    "output_cost",
                    "total_cost",
                ]
            )

    # Calculate costs
    input_cost, output_cost, total_cost = calculate_cost(model, input_tokens, output_tokens)

    # Truncate content for readability (first 100 chars)
    input_preview = input_content[:100] + "..." if len(input_content) > 100 else input_content
    output_preview = output_content[:100] + "..." if len(output_content) > 100 else output_content

    # Append log entry
    with open(log_file, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                datetime.now().isoformat(),
                model,
                function_name,
                input_preview,
                output_preview,
                input_tokens,
                output_tokens,
                input_tokens + output_tokens,
                latency_ms,
                f"{input_cost:.6f}",
                f"{output_cost:.6f}",
                f"{total_cost:.6f}",
            ]
        )


async def get_completion(message: str, model: Optional[str] = "gpt-4o-mini") -> ChatCompletionMessage:
    """
    LLM completion with raw string response

    :param message: The message to send to the LLM.
    :param model: The model to use for the completion.
    :return: The raw string response from the LLM.
    """
    start_time = time.time()
    messages = [{"role": "user", "content": message}]
    response = await client.chat.completions.create(model=model, messages=messages)
    latency_ms = int((time.time() - start_time) * 1000)

    content = response.choices[0].message.content
    usage = response.usage

    log_llm_call(
        model=model,
        function_name="get_completion",
        input_content=message,
        output_content=content,
        input_tokens=usage.prompt_tokens,
        output_tokens=usage.completion_tokens,
        latency_ms=latency_ms,
    )

    return content


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
    start_time = time.time()
    messages = [{"role": "user", "content": message}]
    response = await client.beta.chat.completions.parse(model=model, messages=messages, response_format=response_model)
    latency_ms = int((time.time() - start_time) * 1000)

    if response.choices[0].message.refusal:
        raise Exception(f"Model refused to respond: {response.choices[0].message.refusal}")

    parsed_response = response.choices[0].message.parsed
    usage = response.usage

    log_llm_call(
        model=model,
        function_name="get_completion_structured",
        input_content=message,
        output_content=str(parsed_response),
        input_tokens=usage.prompt_tokens,
        output_tokens=usage.completion_tokens,
        latency_ms=latency_ms,
    )

    return parsed_response
