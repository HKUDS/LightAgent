import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import random
from typing import List, Dict
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import datasets

import io
from datasets import load_dataset, load_from_disk, concatenate_datasets
from PIL import Image
from tqdm import tqdm
from functools import partial
from pillow_avif import AvifImagePlugin
from datasets import Dataset
import json
import yaml
import os
import re
import time
import random
import base64
from openai import AzureOpenAI
import concurrent.futures
from typing import List, Dict
import argparse
import time


def extract_problem_solution(gpt4o_response):
    # Split the response into parts
    parts = gpt4o_response.split("<think>")

    # Extract the problem (first part before any <think> tags)
    problem = parts[0].strip()
    # Remove "Question:" prefix if it exists
    problem = re.sub(r"^Question:\s*", "", problem)
    # Remove "Answer:" at the end of the problem
    problem = re.sub(r"\s*Answer:\s*$", "", problem).strip()

    # Combine all the reasoning steps into a single <think> block
    think_parts = [p.split("</think>")[0].strip() for p in parts[1:] if "</think>" in p]
    solution = f"<think>{' '.join(think_parts)}</think>"

    # Add the final answer if it exists, removing "Answer:" prefix
    if "<answer>" in gpt4o_response:
        final_answer = (
            gpt4o_response.split("<answer>")[-1].split("</answer>")[0].strip()
        )
        final_answer = re.sub(r"^Answer:\s*", "", final_answer)
        solution += f"\n\n<answer>{final_answer}</answer>"

    return problem, solution


def load_image_from_path(image_path):
    try:
        img = Image.open(image_path)
        return img
    except Exception as e:
        print(f"Error loading image {image_path}: {str(e)}")
        return None


def process_raw_data(raw_data):
    # Parse the raw data if it's a string
    if isinstance(raw_data, str):
        data = json.loads(raw_data)
    else:
        data = raw_data

    # Extract problem and solution
    try:
        problem, solution = extract_problem_solution(data["gpt4o_response"])
        image = load_image_from_path(data["image_path"])

        return {
            "image": image,
            "problem": problem,
            "solution": solution,
            "original_question": data["question"],
            "original_answer": data["answer"],
        }
    except Exception as e:
        print(f"Error processing data {data}: {str(e)}")
        return {
            "image": None,
            "problem": None,
            "solution": None,
            "original_question": None,
            "original_answer": None,
        }


raw_data_list = [
    "/path/to/reasoning_data_with_response_90k_verified",
]

raw_data = concatenate_datasets([load_from_disk(path) for path in raw_data_list])

processed_data = raw_data.map(process_raw_data, num_proc=128).shuffle(seed=42)

hf_dict = {
    "image": [],
    "problem": [],
    "solution": [],
    "original_question": [],
    "original_answer": [],
}

for item in tqdm(processed_data):
    hf_dict["image"].append(item["image"])
    hf_dict["problem"].append(item["problem"])
    hf_dict["solution"].append(item["solution"])
    hf_dict["original_question"].append(item["original_question"])
    hf_dict["original_answer"].append(item["original_answer"])


features = datasets.Features(
    {
        "image": datasets.Image(),
        "problem": datasets.Value("string"),
        "solution": datasets.Value("string"),
        "original_question": datasets.Value("string"),
        "original_answer": datasets.Value("string"),
    }
)


def has_empty_tags(text):
    # Pattern to match empty tags like <tag></tag>
    pattern = r"<[^>]+></[^>]+>"
    return bool(re.search(pattern, text))


def has_answer_pattern(text):
    if "Answer:" in text:
        return True
    return False


def has_valid_image_size(example): # for Qwen2-VL-2B's processor requirement
    # Assuming the image is in a format that can be checked for dimensions
    # You might need to adjust this depending on how the image is stored in your dataset
    try:
        image = example["image"]  # or however your image is accessed
        if isinstance(image, dict) and "height" in image and "width" in image:
            return image["height"] >= 28 and image["width"] >= 28
        # If image is a PIL Image or similar
        return image.height >= 28 and image.width >= 28
    except:
        return False


ds = datasets.Dataset.from_dict(hf_dict, features=features)
ds = ds.filter(
    lambda x: not has_empty_tags(x["solution"])
    and not has_answer_pattern(x["problem"])
    and has_valid_image_size(x)
    and x["image"] is not None,
    num_proc=128,
)
# Push to Hugging Face Hub
ds.push_to_hub("path/to/your/dataset")
