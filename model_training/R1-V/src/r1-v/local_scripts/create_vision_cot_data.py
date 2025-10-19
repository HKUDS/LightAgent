import argparse
import base64
import concurrent.futures
import io
import json
import os
import random
import re
import time
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from io import BytesIO
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datasets import Dataset, concatenate_datasets, load_dataset, load_from_disk
from tqdm import tqdm

import bytedtos
import seaborn as sns
import yaml
from openai import AzureOpenAI
from PIL import Image
from pillow_avif import AvifImagePlugin


PROMPT_FORMAT = """I will provide you with an image, an original question, and its answer related to the image. Your task is to rewrite the question in such a way that answering it requires step-by-step Chain-of-Thought (CoT) reasoning with numerical or mathematical expressions where applicable. The reasoning process can include expressions like "let me think," "oh, I see," or other natural language thought expressions.

Please make sure your question is to ask for a certain answer with a certain value, do not ask for open-ended answer, and the answer is correct and easy to verify via simple protocol, like "2" or "A".

Please strictly do not include "Answer:" in the question part to avoid confusion and leakage.

Input Format:
Original Question: {original_question}
Original Answer: {original_answer}

Output Format:
Question: [rewrite the question if necessary]
Answer: [answer with reasoning steps, including calculations where applicable]
<think>step-by-step reasoning process</think>
<answer>easy to verify answer</answer>
"""


def get_image_data_url(image_input):
    if isinstance(image_input, str) and image_input.startswith("data:"):
        return image_input

    if isinstance(image_input, str) and image_input.startswith("http"):
        image_input = load_image(image_input)

    if isinstance(image_input, str):
        image_input = Image.open(image_input)

    if not isinstance(image_input, Image.Image):
        raise ValueError("Unsupported image input type")

    if image_input.mode != "RGB":
        image_input = image_input.convert("RGB")

    buffer = BytesIO()
    image_input.save(buffer, format="JPEG")
    img_bytes = buffer.getvalue()
    base64_data = base64.b64encode(img_bytes).decode("utf-8")
    return f"data:image/jpeg;base64,{base64_data}"


def gpt4o_query(image, prompt, max_retries=5, initial_delay=3):
    if image is None:
        return None

    data_url_list = [get_image_data_url(image)]
    client = AzureOpenAI(
        azure_endpoint="YOUR_AZURE_ENDPOINT",
        api_version="2023-07-01-preview",
        api_key="YOUR_API_KEY",
    )

    for attempt in range(max_retries):
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert to analyze the image and provide useful information for users.",
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                    ],
                },
            ]

            for data_url in data_url_list:
                messages[1]["content"].insert(
                    0, {"type": "image_url", "image_url": {"url": data_url}}
                )

            response = client.chat.completions.create(
                model="gpt-4o-2024-08-06",
                messages=messages,
                temperature=0.2,
                max_tokens=8192,
            )
            return response.choices[0].message.content

        except Exception as e:
            if attempt == max_retries - 1:
                raise Exception(
                    f"Failed after {max_retries} attempts. Last error: {str(e)}"
                )
            delay = initial_delay * (2**attempt) + random.uniform(
                0, 0.1 * initial_delay * (2**attempt)
            )
            time.sleep(delay)


def process_single_item(example):
    try:
        image_path = example["image_path"]
        formatted_prompt = PROMPT_FORMAT.format(
            original_question=example["question"], original_answer=example["answer"]
        )

        response = gpt4o_query(image_path, formatted_prompt)
        example["gpt4o_response"] = response
        return example
    except Exception as e:
        print(f"Error processing item: {str(e)}")
        example["gpt4o_response"] = None
        return example


def main():
    dataset_path = "path/to/your/dataset"
    full_dataset = load_from_disk(dataset_path)

    processed_dataset = full_dataset.map(
        function=partial(process_single_item),
        num_proc=256,
        desc="Processing dataset with GPT-4o",
        keep_in_memory=True,
    )

    output_path = f"{dataset_path}_processed"
    processed_dataset.save_to_disk(output_path)
    print(f"Processed dataset saved to: {output_path}")


if __name__ == "__main__":
    main()
