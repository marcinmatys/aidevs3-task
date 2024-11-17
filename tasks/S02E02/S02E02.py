from tasks.base_task import BaseTask
import os
from typing import Dict, List, Any
from common.ImageUtil import encode_image
from visionService.openaiVService import OpenAIVService


class S02E02(BaseTask):

    def run(self) -> Dict[str, Any]:

        images = self.get_images()

        prompt = self.get_prompt()

        response = OpenAIVService().get_completion(prompt, images, response_format="json_object")
        self.logger.info(f"response: {response}")

    def get_prompt(self):

        # Add in Rules: - Think out loud(in polish) about your task in the "_thinking" field
        # and json format {{"_thinking":"", city:"city name"}}
        # if you want to see model reasoning

        prompt = f"""
        Your task is to find Poland city name based on provided images
        
        Rules:
        - 3 of 4 images are connected with city you search
        - In the city you are looking for there are (in polish): Spichlerze i twierdze
        
        Response in json format:
        {{city:"city name"}}
        """
        return prompt

    def get_images(self):

        # Get the path to the 'resource' directory
        script_dir = os.path.dirname(__file__)  # Directory of the script
        resource_dir = os.path.join(script_dir, 'resources')

        images = []
        for filename in os.listdir(resource_dir):
            if not filename.endswith(".png"):  # Skip files that are not .m4a
                continue
            file_path = os.path.join(resource_dir, filename)  # Construct full file path
            image_base64 = encode_image(file_path)
            images.append({"base64": image_base64})

        return images