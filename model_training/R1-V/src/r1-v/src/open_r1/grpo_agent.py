# Copyright 2025 The HuggingFace Team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import re
import io
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional

from datasets import load_dataset, load_from_disk
from transformers import Qwen2VLForConditionalGeneration

from math_verify import parse, verify
from open_r1.trainer import Qwen2VLGRPOTrainer, Qwen2VLGRPOVLLMTrainer, Qwen2VLGRPOVLLMTrainerModified
from trl import GRPOConfig, GRPOTrainer, ModelConfig, ScriptArguments, TrlParser, get_peft_config

from PIL import Image

from sentence_transformers import SentenceTransformer, util

import base64

semantic_model = SentenceTransformer('all-MiniLM-L6-v2')

def extract_function_call(text):
    pattern = r'<CALLED_FUNCTION>\s*(.*?)\s*</CALLED_FUNCTION>'

    match = re.search(pattern, text, re.DOTALL)

    return match.group(1) if match else None

def extract_state_assessment(text):
	pattern = r'<STATE_ASSESSMENT>\s*(.*?)\s*</STATE_ASSESSMENT>'
	
	match = re.search(pattern, text, re.DOTALL)
	
	return match.group(1) if match else None

def extract_thinking(text):
	pattern = r'<REASONING>\s*(.*?)\s*</REASONING>'
	
	match = re.search(pattern, text, re.DOTALL)
	
	return match.group(1) if match else None

def calculate_semantic_similarity(text1, text2):
    embedding1 = semantic_model.encode(text1, convert_to_tensor=True)
    embedding2 = semantic_model.encode(text2, convert_to_tensor=True)
    
    cosine_similarity = util.pytorch_cos_sim(embedding1, embedding2).item()
    
    return max(0, min(1, cosine_similarity))

@dataclass
class GRPOScriptArguments(ScriptArguments):
    """
    Script arguments for the GRPO training script.

    Args:
        reward_funcs (`list[str]`):
            List of reward functions. Possible values: 'accuracy', 'format'.
    """

    reward_funcs: list[str] = field(
        default_factory=lambda: ["accuracy", "format"],
        metadata={"help": "List of reward functions. Possible values: 'accuracy', 'format'"},
    )
    max_pixels: Optional[int] = field(
        default=12845056,
        metadata={"help": "Maximum number of pixels for the image"},
    )
    min_pixels: Optional[int] = field(
        default=3136,
        metadata={"help": "Minimum number of pixels for the image"},
    )


def accuracy_reward(completions, solution, **kwargs):
    """
    Reward function that checks if the function call in the completion matches the ground truth.
    Gives 0.55 reward for matching function calls.
    """

    contents = [completion[0]["content"] for completion in completions]
    # contents = completions
    rewards = []
    current_time = datetime.now().strftime("%d-%H-%M-%S-%f")
    for content, gt in zip(contents, solution):
        # Extract function calls
        func = extract_function_call(content)
        gt_func = extract_function_call(gt)
        
        if gt_func.startswith("finish") and gt_func != "finish(\"The task has been finished.\")" and func != None:
            if calculate_semantic_similarity(func, gt_func) < 0.7:
                reward = 0.0
            else:
                reward = 1.0
        else:
            reward = 1.0 if func == gt_func else 0.0
        
        rewards.append(reward)
        
        if os.getenv("DEBUG_MODE") == "true":
            log_path = os.getenv("LOG_PATH")
            # local_rank = int(os.getenv("LOCAL_RANK", 0))
            with open(log_path, "a") as f:
                f.write(f"------------- {current_time} Accuracy reward: {reward} -------------\n")
                f.write(f"Content: {content}\n")
                f.write(f"Solution: {gt}\n")

    return rewards

def format_reward(completions, **kwargs):
    """
    Reward function that checks if the completion has the expected format components.
    Gives 0.3 for each component: thinking, state assessment, function call.
    Also checks that the output contains only these three components.
    """
    contents = [completion[0]["content"] for completion in completions]
    # contents = completions
    rewards = []

    for content in contents:
        # Extract components
        thinking = extract_thinking(content)
        state = extract_state_assessment(content)
        func = extract_function_call(content)
        
        # Calculate format reward (0.3 for each component)
        reward = 0.0
        if thinking is not None:
            reward += 0.3
        if state is not None:
            reward += 0.3
        if func is not None:
            reward += 0.4
        
        # Check if output contains only the three required components
        # Remove the three components from the content to check for extra content
        content_clean = content
        if thinking is not None:
            content_clean = re.sub(r'<REASONING>\s*.*?\s*</REASONING>', '', content_clean, flags=re.DOTALL)
        if state is not None:
            content_clean = re.sub(r'<STATE_ASSESSMENT>\s*.*?\s*</STATE_ASSESSMENT>', '', content_clean, flags=re.DOTALL)
        if func is not None:
            content_clean = re.sub(r'<CALLED_FUNCTION>\s*.*?\s*</CALLED_FUNCTION>', '', content_clean, flags=re.DOTALL)
        
        # Remove whitespace and check if there's any remaining content
        content_clean = content_clean.strip()
        if content_clean:
            # If there's extra content, reduce the reward
            reward *= 0.5
            
        rewards.append(reward)
        
    return rewards

reward_funcs_registry = {
    "accuracy": accuracy_reward,
    "format": format_reward,
}

def main(script_args, training_args, model_args):
    # Get reward functions
    reward_funcs = [reward_funcs_registry[func] for func in script_args.reward_funcs]

    # Load the dataset
    # dataset = load_dataset(script_args.dataset_name, name=script_args.dataset_config)
    dataset = load_from_disk(script_args.dataset_name)

    FORMATTED_PROMPT = "{Instruction}\n\n{Input}\n"

    def make_conversation_image(example):
        # Convert PIL Image to bytes if necessary
        image = example["image"]

        if hasattr(image, 'convert'):  # Check if it's a PIL Image
            # Calculate current image size in pixels
            # width, height = image.size
            # current_pixels = width * height
            
            # If image exceeds max_pixels, resize it while maintaining aspect ratio
            # if current_pixels > script_args.max_pixels:
            #     ratio = (script_args.max_pixels / current_pixels) ** 0.5
            #     new_width = int(width * ratio)
            #     new_height = int(height * ratio)
            #     image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # # If image is smaller than min_pixels, resize it while maintaining aspect ratio
            # elif current_pixels < script_args.min_pixels:
            #     ratio = (script_args.min_pixels / current_pixels) ** 0.5
            #     new_width = int(width * ratio)
            #     new_height = int(height * ratio)
            #     image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
            image_bytes = io.BytesIO()
            image.save(image_bytes, format='PNG')
            image = image_bytes.getvalue()
            
        # Create a consistent prompt structure
        prompt = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": example["system"]
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": FORMATTED_PROMPT.format(
                            Instruction=example["instruction"],
                            Input=example["input"]
                        ).replace("<image>\n", "")
                    },
                    {   
                        "type": "image"
                    },
                ]
            }
        ]

        completion = [
            {
                "role": "assistant",
                "content": example["solution"]
            }
        ]
            
        return {
            "prompt": prompt,
            "image": image,
            "completion": completion,
            "solution": example["solution"]
        }

    if "image" in dataset[script_args.dataset_train_split].features:
        print("has image in dataset")
        dataset = dataset.map(
            make_conversation_image,
            desc="Processing dataset",
            remove_columns=dataset[script_args.dataset_train_split].column_names
        )
        
        dataset = dataset.shuffle(seed=42)  # Shuffle before sampling for randomness
        dataset[script_args.dataset_train_split] = dataset[script_args.dataset_train_split].select(range(5550))
        print(f"Sampled dataset size: {len(dataset[script_args.dataset_train_split])}")
    else:
        print("no image in dataset")
        exit()
        
    trainer_cls = Qwen2VLGRPOTrainer if not training_args.use_vllm else Qwen2VLGRPOVLLMTrainerModified
    print("using: ", trainer_cls)

    # Initialize the GRPO trainer
    trainer = trainer_cls(
        model=model_args.model_name_or_path,
        reward_funcs=reward_funcs,
        args=training_args,
        train_dataset=dataset[script_args.dataset_train_split],
        eval_dataset=dataset[script_args.dataset_test_split] if training_args.eval_strategy != "no" else None,
        peft_config=get_peft_config(model_args),
        attn_implementation=model_args.attn_implementation,
        max_pixels=script_args.max_pixels,
        min_pixels=script_args.min_pixels
    )

    # Train and push the model to the Hub
    trainer.train()

    # Save and push to hub
    trainer.save_model(training_args.output_dir)


if __name__ == "__main__":
    parser = TrlParser((GRPOScriptArguments, GRPOConfig, ModelConfig))
    script_args, training_args, model_args = parser.parse_args_and_config()
    
    main(script_args, training_args, model_args)
