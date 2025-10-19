from typing import List, Dict, Any

import backoff
import requests
from openai import OpenAI

from agent.utils import *
from templates.android_screenshot_template import *

from PIL import Image
import io
import base64

def handle_giveup(details):
    print(
        "Backing off {wait:0.1f} seconds afters {tries} tries calling fzunction {target} with args {args} and kwargs {kwargs}"
        .format(**details))


def handle_backoff(details):
    args = str(details['args'])[:1000]
    print(f"Backing off {details['wait']:0.1f} seconds after {details['tries']} tries "
          f"calling function {details['target'].__name__} with args {args} and kwargs ")

    import traceback
    print(traceback.format_exc())


class Agent:
    name: str

    @backoff.on_exception(
        backoff.expo, Exception,
        on_backoff=handle_backoff,
        on_giveup=handle_giveup,
    )
    def act(self, messages: List[Dict[str, Any]]) -> str:
        raise NotImplementedError

    def prompt_to_message(self, prompt, images):
        raise NotImplementedError

    def system_prompt(self, instruction) -> str:
        raise NotImplementedError

class OpenAIAgent(Agent):
    def __init__(
            self,
            api_key: str = '',
            api_base: str = '',
            model_name: str = '',
            max_new_tokens: int = 16384,
            temperature: float = 0,
            top_p: float = 0.7,
            **kwargs
    ) -> None:
        self.client = OpenAI(api_key=api_key, base_url=api_base)
        self.model_name = model_name
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.kwargs = kwargs
        self.name = "OpenAIAgent"


    @backoff.on_exception(
        backoff.expo, Exception,
        on_backoff=handle_backoff,
        on_giveup=handle_giveup,
        max_tries=10
    )

    def act(self, messages: List[Dict[str, Any]]) -> str:
        r = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
        )

        print("-------------------------------")
        print(r.choices[0].message.content)
        print('-------------------------------')
 
        return r.choices[0].message.content

    def prompt_to_message(self, prompt, images):
        content = [
            {
                "type": "text",
                "text": prompt
            }
        ]

        for img in images:
            base64_img = image_to_base64(img)
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_img}"
                }
            })
        message = {
            "role": "user",
            "content": content
        }

        return message
    
    def prompt_to_message_cloud(self, prompt, images):
        content = [
            {
                "type": "text",
                "text": prompt
            }
        ]

        for img in images:
            base64_img = image_to_base64(img)
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_img}"
                }
            })
        messages = [{
            "role": "user",
            "content": content
        }]

        return messages

    def prompt_to_message_text(self, prompt):
        message = {
            "role": "user",
            "content": prompt
        }
        return message
    
    def prompt_to_message_visual(self, prompt,img, max_width=1000, max_height=2200):
        messages = []
        content = []

        img_obj = Image.open(img).convert("RGB")
            
        byte_io = io.BytesIO()
        img_obj.save(byte_io, format='PNG')  

        content.append({
            "type": "image",
            "image": base64.b64encode(byte_io.getvalue()).decode('utf-8')
        })

        content.append({
            "type": "text",
            "text": prompt
        })

        messages.append({
            "role": "user",
            "content": content
        })
            
        return messages


    def system_prompt(self, instruction) -> str:
        return SYSTEM_PROMPT_ANDROID_MLLM_DIRECT + f"\n\nTask Instruction: {instruction}"


class HTTPAgent(Agent):
    def __init__(
            self,
            url: str,
            headers: Dict[str, Any] = {},
            body: Dict[str, Any] = {},
            return_format: str = "{response[choices][0][message][content]}"
    ) -> None:
        self.url = url
        self.headers = headers
        self.body = body
        self.return_format = return_format

    def update_messages(self, body: Dict[str, Any], messages: List[Dict[str, Any]]):
        body.update({"messages": messages})
        return body

    @backoff.on_exception(
        backoff.expo, Exception,
        on_backoff=handle_backoff,
        on_giveup=handle_giveup,
    )
    def act(self, messages: List[Dict[str, Any]]):
        body = self.update_messages({**self.body}, messages)
        response = requests.post(
            self.url, headers=self.headers, body=body
        )
        return self.return_format.format(response=response)
