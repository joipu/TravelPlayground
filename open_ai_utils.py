
import openai

openai.api_key = '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'


def get_response_from_chatgpt(prompt, system_message, model):
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
