import json
import pandas as pd
from datasets import Dataset, DatasetDict, Features, Image, Value
import os
import base64
from PIL import Image as PILImage
import io
import random

import numpy as np

def show_image_info(image, title):
    print(f"\n{title}:")
    print(f"Type: {type(image)}")
    if isinstance(image, np.ndarray):
        print(f"Shape: {image.shape}")
        print(f"Data Type: {image.dtype}")

def convert_json_to_hf_dataset(json_file_path, output_dir, test_size=0.01, seed=42):
    random.seed(seed)
    
    print(f"Reading JSON file from {json_file_path}...")
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    processed_data = {
        'instruction': [],
        'input': [],
        'solution': [],
        'system': [],
        'image': []
    }
    
    for i, item in enumerate(data):
        if i % 100 == 0 and i > 0:
            print(f"Processed {i}/{len(data)} items...")
        
        try:
            image_path = item["images"][0].replace("./ground_data/", "./../../ground_data/")
            processed_data['image'].append(image_path)
            processed_data['instruction'].append(item.get('instruction', ''))
            processed_data['input'].append(item.get('input', ''))
            processed_data['solution'].append(item.get('output', ''))
            processed_data['system'].append(item.get('system', ''))
        except Exception as e:
            print(f"Error processing item {i}: {e}")
            continue
    
    features = Features({
        'instruction': Value('string'),
        'input': Value('string'),
        'solution': Value('string'),
        'system': Value('string'),
        'image': Image()
    })
    
    total_size = len(processed_data['instruction'])
    split_idx = int(total_size * (1 - test_size))
    
    indices = list(range(total_size))
    random.shuffle(indices)
    
    train_indices = indices[:split_idx]
    test_indices = indices[split_idx:]
    
    train_data = {k: [v[i] for i in train_indices] for k, v in processed_data.items()}
    test_data = {k: [v[i] for i in test_indices] for k, v in processed_data.items()}
    
    train_dataset = Dataset.from_dict(train_data, features=features)
    test_dataset = Dataset.from_dict(test_data, features=features)
    
    dataset_dict = DatasetDict({
        'train': train_dataset,
        'test': test_dataset
    })
    
    print(f"Saving dataset to {output_dir}...")
    os.makedirs(output_dir, exist_ok=True)
    dataset_dict.save_to_disk(output_dir)
    
    print(f"Dataset saved successfully. Train size: {len(train_dataset)}, Test size: {len(test_dataset)}")
    
    return dataset_dict

if __name__ == "__main__":
    # Input and output paths
    input_json = "./../visual_model_data/alpaca_format_o1_data_visual_cot.json"
    output_dir = "./../visual_model_data/android_lab_o1_visual_hf"
    
    # Convert and save the dataset
    dataset = convert_json_to_hf_dataset(input_json, output_dir)
    print(f"Dataset has been created with train split: {len(dataset['train'])} examples and test split: {len(dataset['test'])} examples")
    print(f"Dataset features: {dataset['train'].features}")
    
    # Show a sample
    print("\nSample from the train dataset:")
    print(dataset['train'][0])
