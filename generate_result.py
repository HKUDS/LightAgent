import argparse
import concurrent.futures
import datetime
import os
import re
from tqdm import tqdm
from collections import defaultdict
from glob import glob
from os.path import join, isdir, isfile, relpath
from typing import List, Dict

import jsonlines
import pandas as pd

from evaluation.configs import AppConfig
from evaluation.task import Evaluation_Task
from evaluation.definition import detect_answer_test


def find_all_task_files(all_task_config_path) -> List[str]:
    tasks = []
    for task in all_task_config_path:
        if isdir(task):
            tasks += [relpath(path, ".") for path in glob(join(task, "**/*.yaml"), recursive=True)]
        elif isfile(task):
            tasks.append(task)
        else:
            print(f"'{task}' is not a valid file or directory, ignored.")
    return tasks


def find_all_traces_files(traces_path_fold) -> Dict[str, Dict[str, str]]:
    traces_path = os.listdir(traces_path_fold)
    traces = {}
    for trace in traces_path:
        app_name = trace.split('_')[0]
        app_id = trace.split('_')[1]
        task_id = f"{app_name}_{app_id}"
        trace_root = os.path.join(traces_path_fold, trace)
        trace_file = os.path.join(trace_root, "traces", "trace.jsonl")
        xml_path = os.path.join(trace_root, "xml")
        trace_item = {
            "task_id": task_id,
            "trace_file": trace_file,
            "xml_path": xml_path,
            "trace_root": trace_root
        }
        traces[task_id] = trace_item
    return traces


def evaluate_all_tasks(tasks: List[Evaluation_Task]):
    for task in tqdm(tasks):
        try:
            task.evaluate()
            del task
        except Exception as e:
            import traceback
            print(traceback.format_exc())


def evaluate_input_dir(input_dir, task_yamls, create_time, args):
    test_name = input_dir.split('/')[-1]
    output_root_dir = os.path.join(args.output_folder, test_name + "_" + create_time)
    if not os.path.exists(output_root_dir):
        os.makedirs(output_root_dir)

    task_files = find_all_task_files(task_yamls)
    print(f"Found {len(task_files)} task config files")
    
    traces = find_all_traces_files(input_dir)
    print(f"Found {len(traces)} trace files")
    print("Trace files found for tasks:", list(traces.keys()))

    tasks = []
    print("> Loading task configs")
    for app_task_config_path in task_files:
        app_config = AppConfig(app_task_config_path, output_dir=output_root_dir)
        app_task = Evaluation_Task(app_config, traces, args, detail=True)
        print(f"    Evaluation_Task '{app_task.name}' loaded from config {app_task_config_path}")
        print(f"    Available metrics for tasks: {list(app_config.metrics.keys())}")
        tasks.append(app_task)
    print(f"> Successfully load {len(tasks)} task{'s' if len(tasks) > 1 else ''}")
    evaluate_all_tasks(tasks)


def calculate_cloud_percentage(output_folder, agent_name, input_folder):
    cloud_yes_steps = 0
    control_yes_steps = 0
    total_steps = 0
    successful_task_count = 0
    
    results_file = os.path.join(output_folder, "results.jsonl")
    if not os.path.exists(results_file):
        return 0.0, 0.0, 0.0, 0.0, 0.0
    
    successful_tasks = set()
    with jsonlines.open(results_file) as f:
        for line in f:
            task_id = line.get("task_id")
            result = line.get("result", {})
            complete = result.get("complete", False)
            if task_id and complete:  
                task_name = task_id
                successful_tasks.add(task_name)
    
    if not successful_tasks:
        return 0.0, 0.0, 0.0, 0.0, 0.0
    
    agent_input_dir = None
    for item in os.listdir(input_folder):
        if item.startswith(agent_name) and os.path.isdir(os.path.join(input_folder, item)):
            agent_input_dir = os.path.join(input_folder, item)
            break
    
    if not agent_input_dir:
        return 0.0, 0.0, 0.0, 0.0, 0.0
    
    for item in os.listdir(agent_input_dir):
        task_dir = os.path.join(agent_input_dir, item)
        if not os.path.isdir(task_dir):
            continue
            
        task_name = re.sub(r'_\d{4}[-_]?\d{2}[-_]?\d{2}[_-]\d{2}[-_]?\d{2}[-_]?\d{2}.*$', '', item)
        
        if task_name not in successful_tasks:
            continue
            
        trace_file = os.path.join(task_dir, "traces", "trace.jsonl")
        if not os.path.exists(trace_file):
            continue
            
        task_cloud_steps = 0
        task_control_steps = 0
        task_total_steps = 0
        
        with jsonlines.open(trace_file) as trace_f:
            for step in trace_f:
                task_total_steps += 1
                if step.get("cloud") == "Yes":
                    task_cloud_steps += 1
                if step.get("control") == "Yes":
                    task_control_steps += 1
        
        total_steps += task_total_steps
        cloud_yes_steps += task_cloud_steps
        control_yes_steps += task_control_steps
        successful_task_count += 1
    
    if total_steps == 0:
        return 0.0, 0.0, 0.0, 0.0, 0.0
    
    cloud_percentage = (cloud_yes_steps / total_steps) * 100
    avg_total_steps = total_steps / successful_task_count
    avg_cloud_steps = cloud_yes_steps / successful_task_count
    avg_control_steps = control_yes_steps / successful_task_count
    
    return cloud_percentage, avg_total_steps, avg_cloud_steps, avg_control_steps, successful_task_count


def output_to_excel(args):
    output_df = pd.DataFrame()
    base_folder = args.output_folder
    outputs = os.listdir(base_folder)

    for output in outputs:
        output_folder = os.path.join(base_folder, output)
        agent_name = output.split("_2025")[0]
        if not os.path.exists(os.path.join(output_folder, "total.jsonl")):
            continue
        with jsonlines.open(os.path.join(output_folder, "total.jsonl")) as f:
            dict = defaultdict(list)
            total_num = 0
            for line in f:
                # total = line["Total"]
                # App = line["App"]
                for key, value in line.items():
                    if key == "App":
                        dict["App"].append(1)
                    elif key == "Total":
                        dict[key].append(value)
                        total_num += value
                    elif "Sum_" in key or key == "Complete_Correct":
                        dict[key].append(value)
            tt_correct = sum(dict["Complete_Correct"])
            output_dict = {}
            output_dict["agent_name"] = agent_name
            for key, value in dict.items():
                if key == "App":
                    output_dict[key] = len(value)
                elif key == "Total":
                    output_dict[key] = sum(value)
                elif key == "Sum_RRR":
                    if tt_correct == 0:
                        output_dict[key] = 0
                    else:
                        output_dict[key] = 100 * sum(value) / tt_correct
                elif key == "Complete_Correct" or "Sum_" in key:
                    output_dict[key] = 100 * sum(value) / args.total_num
            print(output_dict)
            output_dict["Acc"] = tt_correct / total_num
            output_dict["correct"] = tt_correct
            
            _, _, _, _, successful_task_count = calculate_cloud_percentage(output_folder, agent_name, args.input_folder)
            output_dict["Total_Successful_Tasks"] = successful_task_count
            
            output_df = output_df._append(output_dict, ignore_index=True)
    output_df.to_excel(args.output_excel)
    print(output_df)


def parse_args():
    parser = argparse.ArgumentParser(add_help=False)
    group = parser.add_argument_group("evaluation", "Evaluation configurations")
    group.add_argument("--input_folder", type=str, default="logs/evaluation")
    group.add_argument("--output_folder", type=str, default="outputs")
    group.add_argument("--output_excel", type=str, default="output.xlsx")
    group.add_argument("--total_num", type=int, default=138)
    group.add_argument("--judge_model", type=str, default="glm4")
    group.add_argument("--api_base", type=str, default="")
    group.add_argument("--api_key", type=str, default="439150ab4245c97b3a99bf11671503ac.frQoavSHwVINb8Fn")
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    assert args.judge_model in ["glm4", "gpt-4o-2024-05-13"], "We only support glm4 or gpt-4o for judge model"
    # detect_answer_test(args)
    task_yamls = os.listdir('evaluation/config')
    task_yamls = ["evaluation/config/" + i for i in task_yamls if i.endswith(".yaml")]
    create_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    input_folder = args.input_folder

    input_dirs = [os.path.join(input_folder, input_dir) for input_dir in os.listdir(input_folder)]

    if not os.path.exists(args.output_folder):
        os.makedirs(args.output_folder)
    already_output = os.listdir(args.output_folder)

    agent_list = []
    for output in already_output:
        agent_name = output.split("_2025")[0]
        agent_list.append(agent_name)

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(evaluate_input_dir, input_dir, task_yamls, create_time, args) for input_dir in
                   input_dirs]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                import traceback
                traceback.print_exc()
                print(f'Generated an exception: {exc}')

    output_to_excel(args)
    df = pd.DataFrame()
    files = os.listdir(args.output_folder)
    for file in files:
        output_folder = os.path.join(args.output_folder, file)
        agent_name = file.split("_2025")[0]
        if not os.path.exists(os.path.join(output_folder, "total.jsonl")):
            continue
        output_dict = {"agent_name": agent_name}
        
        successful_task_count = calculate_cloud_percentage(output_folder, agent_name, args.input_folder)
        output_dict["Total_Successful_Tasks"] = successful_task_count
        
        with jsonlines.open(os.path.join(output_folder, "total.jsonl")) as f:
            for line in f:
                app = line["App"]
                correct = line["Complete_Correct"]
                output_dict[app] = correct
        df = df._append(output_dict, ignore_index=True)
        df.to_excel(args.output_excel.replace(".xlsx", "_detail.xlsx"))


if __name__ == "__main__":
    main()
