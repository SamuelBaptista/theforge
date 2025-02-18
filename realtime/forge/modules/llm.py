import openai
import os
from pydantic import BaseModel


def structured_output_prompt(
        prompt: str, response_format: BaseModel, llm_model: str = "gpt-4o-2024-08-06"
) -> BaseModel:
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    completion = client.beta.chat.completions.parse(
        model=llm_model,
        messages=[
            {"role": "user", "content": prompt},
        ],
        response_format=response_format,
    )

    message = completion.choices[0].message

    if not message.parsed:
        raise ValueError(message.refusal)

    return message.parsed


def chat_prompt(prompt: str, model: str) -> str:
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "user", "content": prompt},
        ],
    )

    message = completion.choices[0].message

    return message.content
