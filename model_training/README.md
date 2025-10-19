## Training Scripts

### SFT Training Scripts

The SFT (Supervised Fine-Tuning) related scripts are located in the `llama_factory_scripts` directory. To use these training scripts, you need to first download the latest [LLaMA Factory](https://github.com/hiyouga/LLaMA-Factory) project.

#### Qwen2.5-VL-3B Training Script

The script `full_tuning_setting_3B_vl_fix.sh` is specifically designed for training the Qwen2.5-VL-3B model with the following specifications:

- Maximum context length: 6144 tokens
- Maximum image pixels: 2500000
- Hardware requirement: 2x A100 40GB GPUs
- Training configuration:
  - Uses DeepSpeed ZeRO-3 optimization
  - Batch size: 1 per device
  - Gradient accumulation steps: 6
  - Learning rate: 1e-5
  - Training epochs: 3.0
  - BF16 precision training
  - Gradient checkpointing enabled

### GRPO Training Scripts

The GRPO (Generative Reward Policy Optimization) related scripts are based on the [R1-V project](https://github.com/StarsfieldAI/R1-V). These scripts provide implementation for reward modeling and policy optimization in vision-language tasks.

#### Training Script and Hardware Requirements

The script `R1-V/src/scripts/run_grpo_vllm_qwen25vl_agent.sh` is used for GRPO training. For Qwen2.5-VL-3B model, it requires at least 4x A100 40GB GPUs with the following allocation:
- 3 GPUs for model optimization
- 1 GPU dedicated to vllm inference support

#### Reward Settings and Dataset Sampling

The reward settings are implemented in `R1-V/src/r1-v/src/open_r1/grpo_agent.py`. We have added a crucial dataset sampling code:

```python
dataset = dataset.shuffle(seed=42)  # Shuffle before sampling for randomness
dataset[script_args.dataset_train_split] = dataset[script_args.dataset_train_split].select(range(5550))
```

This sampling code is essential for successful training. The number of sampled data points (5550 in the example) must be a multiple of:
```
per_device_train_batch_size * nproc_per_node * gradient_accumulation_steps
```

⚠️ Important: If this requirement is not met, the training will fail at the end of an epoch when it encounters incomplete batch data.
