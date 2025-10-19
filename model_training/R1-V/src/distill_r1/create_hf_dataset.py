import json
import os
import random
from datasets import load_dataset
from tqdm import tqdm

random.seed(1234)
VAL_NUM = 5000


def create_r1_train_dataset(
    valid_pair_json,
    data_dir,
    img_dir="/home/lilei/Visual-R1/CLEVR_CoGenT_v1.0/images/trainA/",
):
    os.makedirs(data_dir, exist_ok=True)
    pairs = [json.loads(line) for line in open(valid_pair_json, "r")]
    mapped_pairs = []

    for idx, pair in tqdm(enumerate(pairs)):
        img_filename = pair["img_filename"]
        new_pair = {}
        try:
            new_pair["thinking"] = (
                pair["r1_response"]
                .split("<think>")[1]
                .split("</think>")[0]
                .replace("scene description", "image")
            )
        except Exception as e:
            print(f"Error processing pair response: ", pair["r1_response"])
            continue  # skip this pair
        # add index to distinguish the same image
        dataset_filename = (
            img_filename.split(".")[0] + "_" + str(idx) + "." + img_filename.split(".")[1]
        )
        if not os.path.exists(f"{data_dir}/{img_filename}"):
            os.system(f"cp {img_dir}/{img_filename} {data_dir}/{dataset_filename}")
        q, a = pair["q"], pair["a"]
        new_pair["problem"] = q
        # get the thinking path
        
        new_pair["thinking"] = "<think>" + new_pair["thinking"] + "</think>"
        new_pair["solution"] = f"<answer> {a} </answer>"
        new_pair["file_name"] = dataset_filename
        mapped_pairs.append(new_pair)
    with open(f"{data_dir}/metadata.jsonl", "w") as f:
        for pair in mapped_pairs:
            f.write(json.dumps(pair) + "\n")

    train_dataset = load_dataset(
        "imagefolder",
        data_dir=data_dir,
        split="train",
    )
    return train_dataset


def create_val_dataset(
    json_file,
    data_dir,
    val_num=VAL_NUM,
    image_dir="/home/lilei/Visual-R1/CLEVR_CoGenT_v1.0/images/valB",
):
    os.makedirs(data_dir, exist_ok=True)
    val = json.load(open(json_file))
    random.shuffle(val)
    val = val[:val_num]
    val_pairs = []
    for idx, pair in tqdm(enumerate(val)):
        q, a = pair["q"], pair["a"]
        img_filename = pair["img_filename"]
        # copy images to the DATA_DIR
        val_filename = (
            img_filename.split(".")[0] + f"_{idx}." + img_filename.split(".")[1]
        )
        if not os.path.exists(f"{data_dir}/{img_filename}"):
            os.system(f"cp {image_dir}/{img_filename} {data_dir}/{val_filename}")
        new_pair = {}
        new_pair["problem"] = q
        new_pair["solution"] = f"<answer> {a} </answer>"
        new_pair["file_name"] = val_filename
        val_pairs.append(new_pair)
    with open(f"{data_dir}/metadata.jsonl", "w") as f:
        for pair in val_pairs:
            f.write(json.dumps(pair) + "\n")
    val_dataset = load_dataset("imagefolder", data_dir=data_dir, split="train")
    return val_dataset


# valA split
VALA_DATA_DIR = "data/Clevr_CoGenT_ValA"
VALB_DATA_DIR = "data/Clevr_CoGenT_ValB"
valA_json = (
    "/home/lilei/Visual-R1/data/clever_counting_problems_clevr_cogent_v1.0_valA.json"
)
valB_json = (
    "/home/lilei/Visual-R1/data/clever_counting_problems_clevr_cogent_v1.0_valB.json"
)
TRAIN_DATADIR = "data/Clevr_CoGenT_TrainA_R1"
train_dataset = create_r1_train_dataset(
    "/home/lilei/Visual-R1/filter_results_v2/valid_pairs.jsonl",
    TRAIN_DATADIR,
)

# print(train_dataset)
valA_dataset = create_val_dataset(
    valA_json,
    VALA_DATA_DIR,
    image_dir="/home/lilei/Visual-R1/CLEVR_CoGenT_v1.0/images/valA",
)
valB_dataset = create_val_dataset(
    valB_json,
    VALB_DATA_DIR,
    image_dir="/home/lilei/Visual-R1/CLEVR_CoGenT_v1.0/images/valB",
)
valA_dataset.push_to_hub("MMInstruction/Clevr_CoGenT_ValA")
valB_dataset.push_to_hub("MMInstruction/Clevr_CoGenT_ValB")
train_dataset.push_to_hub("MMInstruction/Clevr_CoGenT_TrainA_R1")
