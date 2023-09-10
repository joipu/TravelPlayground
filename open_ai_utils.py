
import openai
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Get the API key from the environment variable
OPEN_AI_KEY = os.getenv('TRAVEL_PLAYGROUND_OPENAI_API_KEY')


def get_response_from_chatgpt(prompt, system_message, model):
    if not OPEN_AI_KEY:
        print("OPEN_AI_KEY is not set. Please create a .env file and set TRAVEL_PLAYGROUND_OPENAI_API_KEY to your OpenAI API key.")
    openai.api_key = OPEN_AI_KEY
    try:
        completion = openai.ChatCompletion.create(
            model=model,
            temperature=0.5,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"GPT response error: {e}"
