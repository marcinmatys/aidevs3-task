from common.HttpUtil import HttpUtil
from tasks.base_task import BaseTask
from dotenv import load_dotenv
import os
from typing import Dict, List, Any
import traceback
from llmService.openaiService import OpenAIService
import json
from common.HttpUtil import HttpUtil, ResponseType
import io
import base64
from visionService.openaiVService import OpenAIVService
from common.cache import persistent_cache

load_dotenv()
base_url = os.getenv('CENTRALA_BASE_URL')
api_key = os.getenv('API_KEY')


class S04E01(BaseTask):
    def __init__(self):
        super().__init__(base_url,"photos")

        self.available_functions = [
            {"function": "REPAIR", "description":"fixing a photo with noise/glitches"},
            {"function": "DARKEN", "description":"brightening a photo"},
            {"function": "BRIGHTEN", "description":"darkening a photo"}
        ]

    def run(self) -> Dict[str, Any]:

        try:

            image_urls = self.get_imageurls()

            image_functions = self.get_image_functions(image_urls)

            improved_images = self.get_improved_images(image_functions)

            final_images = []
            for improved_image in improved_images:
                http_util = HttpUtil(base_url)
                content = http_util.getData(f"dane/barbara/{improved_image}", ResponseType.CONTENT)

                image = io.BytesIO(content)
                image_base64 = base64.b64encode(image.read()).decode('utf-8')
                final_images.append({"base64":image_base64})

            prompt = f"""
            Your task is to prepare detail description of one woman on provided images.
            Focus on distinguishing features and their location, overall appearance, hair color, style and length.
            
            Response in json format {{"_thinking": "", "description":"detail description}}
            Think out loud about your task in "_thinking" field
            
            Steps:
            - Identify one woman on all images
            - skip the image without this woman
            - Prepare and return description in polish language
            """

            #prompt = f"""
            #Opisz główną kobietę ze zdjęcia. Uwzględnij: kolor włosów, oczu, karnację i charakterystyczne cechy wyglądu.
            #"""

            response = OpenAIVService().get_completion(prompt, final_images, response_format="json_object")
            response_json = json.loads(response)
            self.logger.info(f"response_json:  {response_json}")

            self.verify(response_json['description'],"/report")

            # dla każdego obrazu, zdecyduj jaką akcję wykonać
            # wykonaj akcję i pobierz zmienione zdjęcie
            # przekaż wszystkie zdjęcia i pobierz rysopis kobiety


        except Exception as e:
            print(f"An error occurred: {e}")
            traceback.print_exc()

    @persistent_cache(__file__)
    def get_improved_images(self, image_functions):
        improved_images = []
        for image_function in image_functions:
            http_util = HttpUtil(base_url)
            params = {
                "task": "photos",
                "apikey": api_key,
                "answer": f"{image_function['function']} {image_function['img']}"
            }
            changed_image_answer = http_util.sendData(params, "report")
            self.logger.info(f"changed_image_answer:  {changed_image_answer}")

            prompt = f"""
                your task is to extract image name from context and return as json.
                Return image name or empty when filename not exists.
                
                Response in json format {{"image":"image name or empty string"}}
                
                <context>
                {changed_image_answer}
                </context>
                """
            response = OpenAIService().get_completion(prompt, response_format="json_object")
            response_json = json.loads(response)
            image_name = response_json['image']
            self.logger.info(f"image_name:  {image_name}")
            improved_images.append(image_name or image_function['img'])

        self.logger.info(f"improved_images:  {improved_images}")
        return improved_images

    @persistent_cache(__file__)
    def get_image_functions(self, image_urls):
        image_functions = []

        available_functions_str = "\n".join(
            f"{item['function']} - {item['description']}" for item in self.available_functions
        )
        self.logger.info(f"available_functions_str:  {available_functions_str}")

        for image_url in image_urls:
            http_util = HttpUtil(base_url)
            content = http_util.getData(image_url, ResponseType.CONTENT)

            image = io.BytesIO(content)
            image_base64 = base64.b64encode(image.read()).decode('utf-8')

            prompt = f"""
                Your task is to choose best function to improve provided image.
                We need improve image to find woman description. 
                
                Available functions:
                {available_functions_str}
                
                Response in json format {{"function":"selected function name REPAIR|DARKEN|BRIGHTEN"}}
                
                Think it over carefully and find best function.
                """

            response = OpenAIVService().get_completion(prompt, [{"base64": image_base64}],
                                                       response_format="json_object")
            response_json = json.loads(response)
            function = response_json['function']
            image_functions.append({"img": os.path.basename(image_url), "function": function})

        self.logger.info(f"image_functions:  {image_functions}")
        return image_functions

    @persistent_cache(__file__)
    def get_imageurls(self):

        http_util = HttpUtil(base_url)
        params = {
            "task": "photos",
            "apikey": api_key,
            "answer": "START"
        }
        images = http_util.sendData(params, "report")
        self.logger.info(f"images:  {images}")
        images_message = images['message']
        prompt = f"""
            your task is to extract image urls from context and return as json.
            
            Response in json format {{"images":[images urls]}}
            Omit base url: https://centrala.ag3nts.org
            
            <context>
            {images_message}
            </context>
            """
        url_response = OpenAIService().get_completion(prompt, response_format="json_object")
        url_response_json = json.loads(url_response)
        image_urls = url_response_json['images']
        self.logger.info(f"image_urls:  {image_urls}")
        return image_urls


