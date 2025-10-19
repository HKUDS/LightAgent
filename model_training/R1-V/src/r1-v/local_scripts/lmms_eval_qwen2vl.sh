export HF_HOME="<CACHE_DIR>"
export HF_TOKEN="<HF_TOKEN>"
export HF_HUB_ENABLE_HF_TRANSFER="1"

export API_TYPE="<API_TYPE>"
export AZURE_ENDPOINT="<AZURE_ENDPOINT>"
export AZURE_API_KEY="<API_KEY>"
export API_VERSION="<API_VERSION>"
export MODEL_VERSION="<MODEL_VERSION>"
export NAVIT_ATTENTION_IMPLEMENTATION="eager"

# Prompt for installation with 3-second timeout
read -t 3 -p "Do you want to install dependencies? (YES/no, timeout in 3s): " install_deps || true
if [ "$install_deps" = "YES" ]; then
    # Prepare the environment
    pip3 install --upgrade pip
    pip3 install -U setuptools

    cd <PROJECT_ROOT>
    if [ ! -d "maas_engine" ]; then
        git clone <REPO_URL>
    else
        echo "maas_engine directory already exists, skipping clone"
    fi
    cd maas_engine
    git pull
    git checkout <BRANCH_NAME>
    pip3 install --no-cache-dir --no-build-isolation -e ".[standalone]"

    current_version=$(pip3 show transformers | grep Version | cut -d' ' -f2)
    if [ "$current_version" != "4.46.2" ]; then
        echo "Installing transformers 4.46.2 (current version: $current_version)"
        pip3 install transformers==4.46.2
    else
        echo "transformers 4.46.2 is already installed"
    fi

    cd <LMMS_EVAL_DIR>
    rm -rf <TARGET_DIR>
    pip3 install -e .
    pip3 install -U pydantic
    pip3 install Levenshtein
    pip3 install nltk
    python3 -c "import nltk; nltk.download('wordnet', quiet=True); nltk.download('punkt', quiet=True)"
fi

TASKS=mmmu_val,mathvista_testmini,mmmu_pro
MODEL_BASENAME=qwen2_vl

model_checkpoint="<MODEL_CHECKPOINT_PATH>"
echo "MODEL_BASENAME: ${MODEL_BASENAME}"
cd <LMMS_EVAL_DIR>

python3 -m accelerate.commands.launch --num_processes=8 --main_process_port=12345 lmms_eval \
    --model qwen2_vl \
    --model_args=pretrained=${model_checkpoint},max_pixels=2359296 \
    --tasks ${TASKS} \
    --batch_size 1 \
    --log_samples \
    --log_samples_suffix ${MODEL_BASENAME} \
    --output_path ./logs