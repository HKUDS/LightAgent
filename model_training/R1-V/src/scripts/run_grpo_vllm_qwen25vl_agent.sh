#!/bin/bash


# The latest vllm==0.7.3 is required for this script: pip3 install vllm==0.7.3
# The latest transformers is required too, install by: pip install git+https://github.com/huggingface/transformers.git@a40f1ac602fe900281722254c52ce3773f28eb0e



export DEBUG_MODE="true"
export LOG_PATH="./vllm_run.txt"
export WANDB_API_KEY="WANDB_API_KEY"
export WANDB_BASE_URL="WANDB_BASE_URL"
export WANDB_ENTITY="WANDB_ENTITY"

QWEN_PATH="SFT_MODEL_PATH"
HF_DATASET="HF_DATASET" 
OUTPUT_DIR="OUTPUT_DIR"
if [ ! -d "$OUTPUT_DIR" ]; then
 mkdir -p "$OUTPUT_DIR"
fi
RUN_NAME="RUN_NAME"
DS_CONFIG="./../r1-v/local_scripts/zero3_offload_fix.json"  

# NOTE: you are expected to use X + 1 cards for X training proc and 1 vLLM proc 
# e.g., the visible devices should be 0,1,2,3,4 for 5 cards, and  --nproc_per_node="4"

# Create a timestamp for unique log files
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
NOHUP_LOG="./nohup_${TIMESTAMP}.log"

# Export CUDA_VISIBLE_DEVICES before running nohup
export CUDA_VISIBLE_DEVICES="1,2,4,6"

# Run with nohup
nohup torchrun \
    --nproc_per_node="3" \
    --nnodes="1" \
    --node_rank="0" \
    --master_addr="127.0.0.1" \
    --master_port="12345" \
    ./../r1-v/src/open_r1/grpo_agent.py \
    --use_vllm true \
    --output_dir ${OUTPUT_DIR} \
    --model_name_or_path ${QWEN_PATH} \
    --dataset_name ${HF_DATASET} \
    --max_prompt_length 6144 \
    --max_completion_length 1024 \
    --per_device_train_batch_size 1 \
    --per_device_eval_batch_size 1 \
    --gradient_accumulation_steps 50 \
    --learning_rate 5e-6 \
    --lr_scheduler_type "constant" \
    --logging_steps 1 \
    --bf16 true \
    --gradient_checkpointing true \
    --attn_implementation flash_attention_2 \
    --min_pixels 3136 \
    --max_pixels 2500000 \
    --num_train_epochs 5 \
    --run_name ${RUN_NAME} \
    --save_steps 15 \
    --save_total_limit 15 \
    --save_only_model true \
    --report_to wandb \
    --temperature 1.0 \
    --num_generations 4 \
    --vllm_device "cuda:3" \
    --vllm_gpu_memory_utilization 0.9 \
    --beta 5e-4 \
    --deepspeed ${DS_CONFIG} \
    > "${NOHUP_LOG}" 2>&1 &

# Print the process ID
echo "Training process started in background. Process ID: $!"
echo "Logs are being written to: ${NOHUP_LOG}"
