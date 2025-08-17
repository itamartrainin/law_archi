import re
import json

from litellm import completion

def extract_json(text):
    # Extract the first JSON-like block using regex
    match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', text)
    if match:
        json_str = match.group()
        data = json.loads(json_str)
    else:
        raise ValueError("No JSON object found in the response.")
    return data

def translate(text, model='gpt-4o'):
    for i in range(10):
        try:
            prompt = f"""
            Please translate the following from Hebrew to English:
            "{text}"
        
            ** Output JSON format: **
            {{
                "translated_text": "<translated text>"
            }}
            """.strip()

            response = completion(
                model=model,
                temperature=0,
                messages=[{"content": prompt, "role": "user"}]
            )
            return extract_json(response['choices'][0]['message']['content'])['translated_text']
        except Exception as e:
            print(f'Retrying to translate ({i+1})...')

    return ''