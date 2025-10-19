import json
import re
import random  
from PIL import Image
def extract_function_call(text):
    pattern = r'<CALLED_FUNCTION>\s*(.*?)\s*</CALLED_FUNCTION>'

    match = re.search(pattern, text, re.DOTALL)

    return match.group(1) if match else None

def extract_state_assessment(text):
	pattern = r'<STATE_ASSESSMENT>\s*(.*?)\s*</STATE_ASSESSMENT>'
	
	match = re.search(pattern, text, re.DOTALL)
	
	return match.group(1) if match else None

def extract_state_assessment_full(text):
	pattern = r'<STATE_ASSESSMENT>\s*(.*?)\s*</STATE_ASSESSMENT>'
	
	match = re.search(pattern, text, re.DOTALL)
	
	return match.group(0) if match else None

def extract_thinking(text):
	pattern = r'<REASONING>\s*(.*?)\s*</REASONING>'
	
	match = re.search(pattern, text, re.DOTALL)
	
	return match.group(1) if match else None

def extract_function_call_detail(text):
    pattern = r'(tap|text|long_press|swipe|back|home|wait|finish)\((?:[^()]*|"[^"]*"|\'[^\']*\')*\)'
    
    match = re.search(pattern, text)
    
    return match.group(0) if match else None

def print_image_size(image_path):
    try:
        img = Image.open(image_path)
        
        width, height = img.size
        
        return width, height
        
    except Exception as e:
        print(f"读取图片时发生错误: {e}")

SYSTEM_PROMPT_ANDROID_SFT_o1 = '''
You are an intelligent agent that performs smartphone tasks by interacting with UI elements labeled with numeric tags.

## Available Functions
1. **tap(index: int)** - Tap UI element  
2. **text(input_str: str)** - Insert text (tap field first)
3. **long_press(index: int)** - Long press UI element
4. **swipe(index: int, direction: str, dist: str)** - Swipe element
   - direction: "up", "down", "left", "right" 
   - dist: "short", "medium", "long"
5. **back()** - Press back button
6. **home()** - Press home button
7. **wait(interval: int)** - Pause (default: 5 seconds)
8. **finish(message: str)** - Complete task

## Required Output Format

<REASONING>
[Analyze current screen, task progress, chosen action rationale, and expected outcome]
</REASONING>

<STATE_ASSESSMENT>
Current State: [Screen description]
Task Progress: [Completion status]
Next Required Action: [What's needed]
Expected Outcome: [Action result]
Potential Issues: [Risk considerations]
</STATE_ASSESSMENT>

<CALLED_FUNCTION>
[Single function call only]
</CALLED_FUNCTION>

## Guidelines
- Execute one action per step
- Verify elements exist before interaction
- Tap input fields before using text()
- Monitor progress to avoid redundant actions
- Use finish() only when task complete
- Choose direct, efficient paths to completion
'''

def convert_to_alpaca(data):

    max_length = -1
    alpaca_data = []

    right_counter = 0

    for i in range(len(data)):
        item = data[i]

        thinking = extract_thinking(item["reasoning"])
        state = extract_state_assessment(item["reasoning"])
        func = extract_function_call(item["reasoning"])
        func_detail = extract_function_call_detail(item["reasoning"])

        if thinking is None or state is None or func is None or func_detail is None:
            continue

        state_full = extract_state_assessment_full(item["reasoning"])

        output_new = item["reasoning"]

        width, height = print_image_size(item["image_path"])

        if width != 1440 or height != 3120:
            print("error!")
            exit()

        alpaca_entry = {
            "instruction": item["task"],
            "input": "History Information:" + item["history_state"] + "\nCurrent Information: <image>",
            "output": output_new,
            "system": SYSTEM_PROMPT_ANDROID_SFT_o1,
            "images":[
                item["image_path"].replace("./../../", "./")
            ]
        }

        all_string = alpaca_entry["instruction"] + alpaca_entry["input"] + alpaca_entry["output"] + alpaca_entry["system"]

        if len(all_string) > 12000: # 12000 is the max length of the input of the model that GPU can handle, you can change it to a larger number if you have a better GPU server
            continue
        max_length = max(max_length, len(all_string))

        alpaca_data.append(alpaca_entry)
        right_counter += 1

    print(right_counter)
    print(len(data))
    print(max_length)
    return alpaca_data

with open('./o1_data_visual_cot_all.json', 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

alpaca_data = convert_to_alpaca(raw_data)

with open('./alpaca_format_o1_data_visual_cot.json', 'w', encoding='utf-8') as f:
    json.dump(alpaca_data, f, ensure_ascii=False, indent=2)

print(f"\nTotal items: {len(alpaca_data)}")