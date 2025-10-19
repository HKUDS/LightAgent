import json
import random
import os 
from openai import OpenAI
from tqdm import tqdm
import concurrent.futures
from typing import List, Dict, Optional
from datetime import datetime
from threading import Lock
import time 
from prompt import R1_SYS_PROMPT 
# Initialize the client
client = OpenAI(
    api_key=os.environ.get("SL_KEY", "YOUR_SILCONFLOW_KEY"),
    base_url="https://api.siliconflow.cn/v1",
)

# Create a lock for thread-safe file writing
file_lock = Lock()

def format_query(qa_dict: Dict, v2=False) -> str:
    query = "Answer the question according to scene description.\n\n"
    query += qa_dict["description"]
    query += f"\nQuestion:\n{qa_dict['q']}"
    if v2:
        query += "\nInstructions:\n"
        query += "1. Carefully analyze the scene description\n"
        query += "2. Provide your reasoning if necessary\n"
        query += "3. For the final answer, start a new line with '**The answer is: **' followed by your answer\n"
    return query

def write_to_jsonl(result: Dict, filename: str):
    """Thread-safe function to write a result to JSONL file"""
    with file_lock:
        with open(filename, 'a') as f:
            f.write(json.dumps(result) + '\n')

def query_r1(qa_pair: Dict, output_file: str, model: str = "deepseek-ai/DeepSeek-R1", v2=False) -> Optional[Dict]:
    query = format_query(qa_pair, v2=v2)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": R1_SYS_PROMPT},
                {"role": "user", "content": query}],
            stream=False,
            max_tokens=4096 
        )
        result = {
            **qa_pair,
            "r1_response": response.choices[0].message.content,
            "timestamp": datetime.now().isoformat()
        }
        # Write result immediately
        write_to_jsonl(result, output_file)
        time.sleep(4)
        return result
    except Exception as e:
        print(f"Error processing query: {e}")
        error_result = {
            **qa_pair,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        write_to_jsonl(error_result, f"errors_{output_file}")
        time.sleep(10)
        return None

def process_qa_pairs_parallel(qa_pairs: List[Dict], output_file: str, max_workers: int = 10) -> List[Dict]:
    successful_count = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Create futures for all qa_pairs
        futures = [executor.submit(query_r1, qa_pair, output_file, v2="v2" in output_file) for qa_pair in qa_pairs]
        
        # Process results as they complete with progress bar
        results = []
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures)):
            try:
                result = future.result()
                if result is not None:
                    results.append(result)
                    successful_count += 1
            except Exception as e:
                print(f"Failed to process query: {e}")
    
    return results

if __name__ == "__main__":
    # Load and shuffle QA pairs
    random.seed(1234)
    qa_pairs = json.load(open("/home/lilei/Visual-R1/data/clever_counting_problems_clevr_cogent_v1.0_trainA.json"))
    random.shuffle(qa_pairs)
    qa_pairs = qa_pairs[:10000]
    # Create output filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"r1_results_clevr_cogent_v1.0_trainA_v2.jsonl"
    
    finished = set() 
    with open(output_file, 'r') as f:
        for line in f:
            ins = json.loads(line)
            key = ins["img_filename"] + "-" + ins["q"] + "-"  + str(ins["a"])
            finished.add(key)
    qa_pairs = [ins for ins in qa_pairs if ins["img_filename"] + "-" + ins["q"] + "-" + str(ins["a"]) not in finished] 
    print("Finished: ", len(finished))
    print("Remaining: ", len(qa_pairs)) 
    # Process QA pairs in parallel
    r1_results = process_qa_pairs_parallel(qa_pairs, output_file)
    
    # Print final statistics
    print(f"Successfully processed {len(r1_results)} out of {len(qa_pairs)} queries")
    print(f"Results saved to {output_file}")
    print(f"Any errors were saved to errors_{output_file}")