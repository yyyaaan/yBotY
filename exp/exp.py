# %% Use Docker or yyy env
import base64
from openai import OpenAI


with open("../tmp/7024.JPG", "rb") as f:
    base64_image = base64.b64encode(f.read()).decode('utf-8')


client = OpenAI()

# %% Image > text understanding only
response = client.chat.completions.create(
    model="gpt-4-vision-preview",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Can you transform this image to anime style?"
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
