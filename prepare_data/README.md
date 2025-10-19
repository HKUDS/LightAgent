## Overview

This directory provides scripts and datasets for generating fine-tuning data with long reasoning chains and reflection signals using LLMs, and for converting that data into formats suitable for LLaMA-Factory SFT and Hugging Face GRPO training.

## Contents

- **visual_model_data/data_maker.py**: Uses an LLM to generate visual Chain-of-Thought (CoT) data that includes long reasoning and reflection information.
- **visual_model_data/o1_data_visual_cot_all.json**: Raw data produced by `data_maker.py`.
- **visual_model_data/sft_data_maker.py**: Converts the raw data into an Alpaca-style format compatible with LLaMA-Factory supervised fine-tuning (SFT).
- **visual_model_data/alpaca_format_o1_data_visual_cot.json**: The SFT-ready dataset output by `sft_data_maker.py`.
- **rl/convert_to_hf_vl.py**: Further converts the SFT dataset into a Hugging Face vision-language dataset for GRPO training.
- **visual_model_data/android_lab_o1_visual_hf/**: The resulting Hugging Face-formatted dataset used for GRPO.

## Typical Workflow

Before starting, please place the fine-tuning data 'android-lab-train' provided by AndroidLab benchmark in the ./ground_data directory. This data can be downloaded directly from the original AndroidLab project or through this project's Hugging Face repository.

1. Generate raw data (long reasoning + reflection) with the LLM:
   - Run `visual_model_data/data_maker.py` to produce `visual_model_data/o1_data_visual_cot_all.json`.
2. Convert raw data to LLaMA-Factory SFT format:
   - Run `visual_model_data/sft_data_maker.py` to produce `visual_model_data/alpaca_format_o1_data_visual_cot.json`.
3. Convert SFT data to Hugging Face V+L format for GRPO:
   - Run `rl/convert_to_hf_vl.py` to create/update `visual_model_data/android_lab_o1_visual_hf/`.

> **Note:** The current `o1_data_visual_cot_all.json` does **not** include data related to the "pimusic" app. Data for this app is provided separately in `o1_data_visual_cot_pimusic.json`. We plan to merge these two data files as soon as possible.