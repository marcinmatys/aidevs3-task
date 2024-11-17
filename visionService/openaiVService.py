import openai
import os
from dotenv import load_dotenv, find_dotenv
from .visionService import VisionService
from typing import Dict, List, Any


class OpenAIVService(VisionService):
    def __init__(self, api_key:str = None):
        _ = load_dotenv(find_dotenv())
        api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.client = openai.OpenAI(api_key=api_key)

    def get_completion(self, prompt: str, images: List[Dict[str, Any]], model: str = "gpt-4o", temperature: float = 1, response_format: str = "text") -> str:

        content = [{"type": "text", "text": prompt}]

        for image in images:
            # For base64 images, construct the full data URL
            if "base64" in image:
                image_url = f"data:image/jpeg;base64,{image['base64']}"
            else:
                image_url = image["url"]

            image_content = {
                "type": "image_url",
                "image_url": {
                    "url": image_url,
                    "detail": image.get("detail", "auto")
                }
            }
            content.append(image_content)

        messages = [{"role": "user", "content": content}]

        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            response_format={"type": response_format}
        )
        return response.choices[0].message.content
