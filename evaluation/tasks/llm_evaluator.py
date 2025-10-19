import base64
import requests
import os
from typing import Dict, Any
import json
import traceback


class LLMEvaluator:
    def __init__(self, api_key: str = "API_KEY"):
        self.api_key = api_key
        self.api_url = "API_BASE_URL"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}" if api_key else "",
        }

    def encode_image(self, image_path: str) -> str:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def _post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            if response.status_code != 200:
                print(f"API request failed with status code {response.status_code}: {response.text}")
                return {}
            return response.json()
        except Exception as e:
            print(f"Unexpected error during API call: {str(e)}")
            print("Traceback:", traceback.format_exc())
            return {}

    def _extract_message_content(self, response_json: Dict[str, Any]) -> str:
        if not response_json:
            return ""
        if "choices" in response_json and len(response_json["choices"]) > 0:
            return response_json["choices"][0].get("message", {}).get("content", "")
        return ""

    def _parse_json_content(self, content: str) -> Dict[str, Any]:
        try:
            content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except Exception as e:
            print(f"Failed to parse JSON from content: {content}")
            print(f"JSON parse error: {e}")
            return {}

    def analyze_text(self, text: str, task_prompt: str) -> Dict[str, Any]:
        payload = {
            "model": "google/gemini-2.5-flash",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": task_prompt + "\n\nText to analyze:\n" + text}
                    ],
                }
            ],
        }
        response_json = self._post(payload)
        content = self._extract_message_content(response_json)
        result = self._parse_json_content(content)
        return result if result else {}

    def analyze_screenshot(self, image_path: str, task_prompt: str) -> Dict[str, Any]:
        base64_image = self.encode_image(image_path)
        payload = {
            "model": "google/gemini-2.5-flash",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": task_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                    ],
                }
            ],
        }
        response_json = self._post(payload)
        content = self._extract_message_content(response_json)
        result = self._parse_json_content(content)
        return result if result else {} 