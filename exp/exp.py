# %% Use Docker or yyy env
import base64
from openai import OpenAI


with open("../tmp/apps.png", "rb") as f:
    base64_image = base64.b64encode(f.read()).decode('utf-8')

prompt = "What app logs are there?"

client = OpenAI()

# %% Image > text understanding only
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}",
                    },
                },
            ],
        }
    ],
    max_tokens=999,
)

print(response.choices[0])

# %%
