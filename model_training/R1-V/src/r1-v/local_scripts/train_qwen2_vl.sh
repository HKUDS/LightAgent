#!/bin/bash

export NCCL_BLOCKING_WAIT=0
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=8
export NCCL_IB_DISABLE=0
export NCCL_IB_GID_INDEX=3
export NCCL_SOCKET_IFNAME=eth0
export NCCL_DEBUG=INFO

GPUS="0,1,2,3,4,5,6,7"

# 取 worker0 第一个 port
ports=($(echo $METIS_WORKER_0_PORT | tr ',' ' '))
port=${ports[0]}
port_in_cmd="$(echo "${METIS_WORKER_0_PORT:-2000}" | awk -F',' '{print $1}')"

echo "total workers: ${ARNOLD_WORKER_NUM}"
echo "cur worker id: ${ARNOLD_ID}"
echo "gpus per worker: ${ARNOLD_WORKER_GPU}"
echo "master ip: ${METIS_WORKER_0_HOST}"
echo "master port: ${port}"
echo "master port in cmd: ${port_in_cmd}"

# export WANDB_BASE_URL=https://api.wandb.ai
# export WANDB_API_KEY="<PLACEHOLDER_WANDB_KEY_1>"
# wandb login $WANDB_API_KEY

export WANDB_BASE_URL=https://api.wandb.ai
export WANDB_PROJECT=vision-reasoning
export WANDB_API_KEY="<PLACEHOLDER_WANDB_KEY_2>"
export WANDB_RUN_NAME=Qwen-VL-2B-GRPO-$(date +%Y-%m-%d-%H-%M-%S)
wandb login $WANDB_API_KEY

cd /home/tiger/multimodal-open-r1
# pip3 install vllm==0.6.6.post1
pip3 install -e ".[dev]"
pip3 install wandb==0.18.3

torchrun --nproc_per_node="${ARNOLD_WORKER_GPU}" \
    --nnodes="${ARNOLD_WORKER_NUM}" \
    --node_rank="${ARNOLD_ID}" \
    --master_addr="${METIS_WORKER_0_HOST}" \
    --master_port="${port_in_cmd}" \
    src/open_r1/grpo.py \
    --deepspeed scripts/zero3.json \
    --output_dir checkpoints/${WANDB_RUN_NAME} \
    --model_name_or_path Qwen/Qwen2-VL-2B-Instruct \
    --dataset_name luodian/${DATASET_NAME} \
    --max_prompt_length 8192 \
    --per_device_train_batch_size 1 \
    --gradient_accumulation_steps 1 \
    --logging_steps 1 \
    --bf16 \
    --report_to wandb \
    --gradient_checkpointing true \
    --attn_implementation flash_attention_2 \
    --max_pixels 2359296 \
    --save_total_limit 8 \
    --num_train_epochs 1 \
    --run_name $WANDB_RUN_NAME
