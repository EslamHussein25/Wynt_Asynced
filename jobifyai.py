import os
import json
import logging
import asyncio
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api_key = os.getenv('OPENAI_API_KEY')
if api_key is None:
    print("OPENAI_API_KEY is not set.")

client = OpenAI(api_key=api_key)

MODEL = "gpt-4o-mini"

async def process_gpt_4o_turbo(text, agent):
    try:
        completion = await asyncio.to_thread(
            client.chat.completions.create,
            model=MODEL,
            messages=[
                {"role": "system", "content": agent},
                {"role": "user", "content": text},
            ],
            temperature=0.5,
            max_tokens=4096,
            n=1,
            stop=None,
        )

        # Process the completion response
        logger.info(f"completion.choices[0].message.content : {completion.choices[0].message.content}")
        completion_text = completion.choices[0].message.content

        # Check and extract JSON content
        if "```json" in completion_text and "```" in completion_text:
            json_content = completion_text.split("```json")[1].split("```")[0].strip()
        else:
            json_content = completion_text.strip()

        completion_json = json_content

        return completion_json
    except json.JSONDecodeError:
        logger.error("Invalid JSON response from GPT-4o")
        return {"error": "Invalid JSON response from GPT-4o"}
    except KeyError:
        logger.error("Error processing completion.")
        return {"error": "Error processing completion."}
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return {"error": f"An error occurred: {e}"}
