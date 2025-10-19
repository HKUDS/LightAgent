import json
import re
import os
import random
import time
import logging
from typing import List, Dict, Any
import base64

import backoff
import requests
from openai import OpenAI, APIError, APITimeoutError, RateLimitError
from requests.exceptions import RequestException, Timeout

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT_VIS_THINKING = '''
You are an interface analysis assistant for smartphones.

You are provided with a screenshot of a smartphone interface. 

The interactive elements within the UI are marked with numeric tags starting from 1.

For each operable UI element, include the following details:  
1. **Type of action:** Describe the type of interaction available (e.g., navigation, text input, toggle, etc.).  
2. **Text information:** Any visible text associated with the UI element (e.g., labels, placeholders, or descriptions).  
3. **Action:** Summarize what happens when the element is interacted with (e.g., "Tap to navigate to settings," "Toggle to enable/disable Wi-Fi").  
4. **State:** If the element has a state (e.g., switches for Bluetooth, Wi-Fi), specify whether it is currently "On" or "Off." If no state applies, write "None."  
5. **Array Indexes:** If an element has multiple numeric tags, list all the indexes corresponding to that element.

You can call the following functions to interact with those labeled elements to control the smartphone:

1. **tap(index: int)**  
   Simulates a tap action on the UI element labeled with the specified number.

2. **text(input_str: str)**  
   Inserts the provided text into an input field.

3. **long_press(index: int)**  
   Simulates a long press action on the UI element labeled with the specified number.

4. **swipe(index: int, direction: str, dist: str)**  
   Performs a swipe gesture on the specified UI element.  
   - **direction**: One of the four options: "up", "down", "left", "right".  
   - **dist**: Represents the swipe distance, which can be "short", "medium", or "long".

5. **back()**  
   Simulates pressing the back button on the smartphone.

6. **home()**  
   Simulates pressing the home button on the smartphone.

7. **wait(interval: int)**  
   Pauses execution for the specified number of seconds (default is 5 seconds).

8. **finish(message: str)**  
   Completes the task and provides the final output as a string.

### Reasoning Process
You will use a step-by-step reasoning process ("Chain of Thought") to determine the appropriate actions required to accomplish the task. Your reasoning should follow this structure:

1. **Analyze Current State**
   - Determine whether the current page indicates that the task to be completed has been finished
   - Review the current UI elements and their positions
   - Identify relevant interactive elements for the task

2. **History Assessment**
   - Evaluate whether previous actions achieved their intended goals
   - Analyze how the current state relates to the history of actions
   - Determine if any course correction is needed based on previous outcomes

3. **State Assessment**
   - Describe the current state of the page in relation to the task
   - Explain how the planned action will change this state
   - Clarify the specific goal of the action in progressing toward task completion

4. **Plan Actions**
   - Break down the task into sequential steps
   - Identify which UI elements need to be interacted with

5. **Determine Functions**
   - For each step, specify which function is needed
   - Include the exact parameters required for each function
   - Your conclusion MUST match exactly with the provided CALLED FUNCTION

Your reasoning must explicitly connect your analysis to the function calls you'll make, ending with the exact function call that matches the provided CALLED FUNCTION.

### Input Structure
You will receive the following input components:

1. **Task Instruction**  
   A description of the task to be completed.  
   Example:  
   ```  
   <TASK INSTRUCTION>  
   {TASK_INSTRUCTION}  
   </TASK INSTRUCTION>  
   ```

2. **Screenshot**  
   Example:  
   ```  
   <SCREENSHOT>  
   {SCREENSHOT}  
   </SCREENSHOT>  
   ```

3. **History Info**  
   Information about previous states, actions, and their intended goals.
   Example:  
   ```  
   <HISTORY INFO>
   {HISTORY_INFO}
   </HISTORY INFO>  
   ```

4. **Called Function**  
   The specific function you need to justify through your reasoning.
   Example:  
   ```  
   <CALLED FUNCTION>
   {CALLED_FUNCTION}
   </CALLED FUNCTION>  
   ```

5. **Reasoning**  
   A detailed analysis following the five-step reasoning process above, concluding with the specific function to be called.
   Your reasoning MUST lead to and justify the exact function provided in CALLED FUNCTION.
   Example:  
   ```  
   <REASONING>
   1. Current State Analysis:
      - [Analysis of UI elements]
   2. History Assessment:
      - [Evaluation of previous actions]
      - [Analysis of how current state relates to action history]
      - [Determination if course correction is needed]
   3. State Assessment:
      - [Current page state description]
      - [How the planned action will change this state]
      - [Goal of the action in task progression]
   4. Action Planning:
      - [Step-by-step plan]
   5. Function Determination:
      - [Function selection with parameters]
      Therefore, I will call: tap(2)  // Must match CALLED FUNCTION exactly
   </REASONING>  
   ```

### Your Task
Based on the provided task instructions, UI description, and history information, you will:  
1. Analyze the information.  
2. Evaluate previous actions and their outcomes.
3. Formulate a clear reasoning process.
4. Ensure your reasoning concludes with and justifies the exact function provided in CALLED FUNCTION.

Your reasoning should naturally lead to and explain why the given CALLED FUNCTION is the appropriate action to take.
'''

SYSTEM_PROMPT_REASONING_FORMAT = '''
You are an AI assistant specializing in converting formal UI interaction reasoning into natural, human-like internal dialogue while preserving all technical details and observations. Your goal is to demonstrate how a person would naturally think through smartphone interface interactions without losing any important information from the original reasoning.

INPUT STRUCTURE:
You will receive reasoning in this format:
<REASONING>
{formal technical reasoning}
</REASONING>

<CALLED_FUNCTION>
{specific function to be called}
</CALLED_FUNCTION>

YOUR TASK:
Transform the formal reasoning into natural internal dialogue that:
1. Maintains ALL logical steps, technical details, and conclusions - no information should be omitted
2. Reads like someone thinking out loud while being technically precise
3. Shows progressive understanding while preserving specific observations
4. Leads naturally to the specified action through detailed reasoning
5. Retains all numerical references, technical terms, and specific UI element descriptions

DIALOGUE STYLE REQUIREMENTS:

1. THOUGHT PROCESS
- Use first-person perspective ("I")
- Show real-time thinking and discovery
- Include self-corrections and realizations
- Express natural uncertainty and consideration
- Build connections between observations
- Preserve all technical details in natural language form

2. LANGUAGE PATTERNS FOR PRESERVING DETAILS
Natural transitions while maintaining precision:
- Detailed observations: "I see element {X} which appears to be {detailed description}..."
- Technical realizations: "Looking at the interface more closely, I notice that {specific technical detail}..."
- Analytical consideration: "Given that element {X} has {specific properties}, I need to consider..."
- Technical connections: "This element's state being {X} means that {technical implication}..."
- Precise decisions: "Based on {specific details}, the most appropriate action would be..."

3. CONTENT STRUCTURE
Your response should follow this detailed progression:
a) Initial screen observation (including all visible elements and their states)
b) Detailed analysis of key UI elements (preserving all technical properties)
c) Comprehensive understanding of their purpose and current state
d) Technical connections between elements and task requirements
e) Detailed plan formation incorporating all relevant factors
f) Precise decision making based on complete analysis

4. OUTPUT FORMAT
Your response MUST contain these components in order:

<REASONING>
{Your natural, conversational reasoning that preserves ALL technical details and leads to the action}
</REASONING>

<STATE_ASSESSMENT>
Current State: {Detailed description of what's currently visible and relevant, including all technical aspects}
Required Change: {Precise description of what needs to be different, including technical requirements}
Action Need: {Detailed explanation of why this specific action is necessary, including technical justification}
</STATE_ASSESSMENT>

<CALLED_FUNCTION>
{exact function call from input}
</CALLED_FUNCTION>

CRITICAL GUIDELINES:
- Preserve every technical detail while making it conversational
- Convert formal observations into natural language without losing specificity
- Maintain all numerical references and technical terms
- Build logical connections while keeping all original information
- Ensure technical accuracy while making it accessible
- Never omit or simplify technical details
- Ensure the final action matches the input exactly

EXAMPLE STRUCTURE:
<REASONING>
"Let me carefully examine what's on the screen... I can see the settings menu which contains multiple configuration options. The WiFi toggle element, labeled as element 1, is positioned at the top of the interface - this placement is logical given its frequent usage. Looking at its current state more closely, I can see the toggle indicator is in the leftmost position, showing it's currently disabled. The toggle has a grey color scheme typical of disabled states, and the accompanying status text reads 'Off'. Given that our task specifically requires enabling WiFi functionality, I'll need to interact with this toggle element to change its state from disabled to enabled. The element is clearly interactive as indicated by its standard toggle switch design pattern..."
</REASONING>

<STATE_ASSESSMENT>
Current State: WiFi toggle (element 1) is visible and in disabled state, indicated by left position and grey coloring
Required Change: WiFi toggle needs to transition from disabled to enabled state
Action Need: Direct interaction with toggle element 1 is required to trigger state transition from disabled to enabled
</STATE_ASSESSMENT>

<CALLED_FUNCTION>
tap(1)
</CALLED_FUNCTION>
'''

def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

class Agent:
    name: str

    def act(self, messages: List[Dict[str, Any]]) -> str:
        raise NotImplementedError

    def prompt_to_message(self, prompt, images):
        raise NotImplementedError

    def system_prompt(self, instruction) -> str:
        raise NotImplementedError
    
class VisualInterfaceAgent(Agent):
    def __init__(
            self,
            api_key: str = '',
            api_base: str = '',
            model_name: str = '',
            max_new_tokens: int = 16384,
            temperature: float = 0,
            top_p: float = 0.7,
            **kwargs
    ) -> None:
        self.client = OpenAI(
            api_key=api_key,
            base_url=api_base
        )
        self.model_name = model_name
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.kwargs = kwargs
        self.name = "OpenAIAgent"

    def act(self, messages: List[Dict[str, Any]]) -> str:

        retry_count = 0

        res = None

        while retry_count < 10:
            try:
                retry_count += 1
                r = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    max_tokens=self.max_new_tokens,
                    temperature=self.temperature,
                    top_p=self.top_p,
                )

                res = r.choices[0].message.content
                break
            except Exception as e:
                logger.error(f"Error parsing API response: {e}")
                logger.error(f"Full response: {r}")
                time.sleep(3)

        if res is None:
            raise Exception("Failed to get response from API")

        return res

    def prompt_to_message(self, image, content_text):
        content = [
            {
                "type": "text",
                "text": content_text
            }
        ]

        base64_img = image_to_base64(image)
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_img}"
            }
        })
        message = {
            "role": "user",
            "content": content
        }

        return message
    
class GPTAgent(Agent):
    def __init__(
            self,
            api_key: str = '',
            api_base: str = '',
            model_name: str = '',
            max_new_tokens: int = 16384,
            temperature: float = 0,
            top_p: float = 0.7,
            **kwargs
    ) -> None:
        self.client = OpenAI(
            api_key=api_key,
            base_url=api_base
        )
        self.model_name = model_name
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.kwargs = kwargs
        self.name = "OpenAIAgent"

    def act(self, messages: List[Dict[str, Any]]) -> str:
        r = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            max_tokens=self.max_new_tokens,
            temperature=self.temperature,
            top_p=self.top_p
        )

        try:
            res = r.choices[0].message.content
            return res
        except Exception as e:
            logger.error(f"Error parsing API response: {e}")
            logger.error(f"Full response: {r}")

    def prompt_to_message(self, content):
        message = {
            "role": "user",
            "content": content
        }

        return message 

def extract_function_call(text):
    pattern = r'(tap|text|long_press|swipe|back|home|wait|finish)\((?:[^()]*|"[^"]*"|\'[^\']*\')*\)'
    
    match = re.search(pattern, text)
    
    return match.group(0) if match else None

def extract_state_assessment(text):
    pattern = r'<STATE_ASSESSMENT>\s*(.*?)\s*</STATE_ASSESSMENT>'
    
    match = re.search(pattern, text, re.DOTALL)
    
    return match.group(1).strip() if match else None

def extract_reasoning(text):
    pattern = r'<REASONING>\s*(.*?)\s*</REASONING>'
    
    match = re.search(pattern, text, re.DOTALL)
    
    return match.group(1).strip() if match else None

API_KEY = "API_KEY"
API_BASE = "API_BASE"
MAX_NEW_TOKENS = 16384

def parse_interaction_history(history):
    rounds = history.split('Round')[1:]
    task_match = re.search(r'<\|user\|>\n(.*?)\n\n<\|assistant\|>', rounds[0], re.DOTALL)
    task = task_match.group(1).strip() if task_match else None
    actions = []

    for round_str in rounds:
        action_match = re.search(r'<\|assistant\|>\n(.*?)\n', round_str, re.DOTALL)
        if action_match:
            action = action_match.group(1).strip()
            actions.append(action)

    return task, actions

def list_sorted_files_in_directory(directory):
    try:
        files = os.listdir(directory)
        full_paths = [os.path.join(directory, f) for f in files if os.path.isfile(os.path.join(directory, f))]
        sorted_paths = sorted(full_paths)
        return sorted_paths
    except Exception as e:
        print(f"Error: {e}")
        return []
    
with open('./../../ground_data/android-lab-train/androidlab-som-train.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

data_list = []

for round_data in data:
    messages = round_data['messages']
    if 'finish(' in messages[1]['content'] and messages[1]['role'] == 'assistant':
        image_path = round_data["images"][0]
        image_path = image_path.split('/')[1]
        data_list.append((messages[0]['content'] + messages[1]['content'] + '\n', image_path))

print(len(data_list))

temp_data_list = []

for single_data, _ in data_list:
    if 'setting' in single_data or 'Setting' in single_data:
        temp_data_list.append((single_data, _, 'setting'))
    elif 'bluecoins' in single_data or 'Bluecoins' in single_data:
        temp_data_list.append((single_data, _, 'bluecoins'))
    elif 'calendar' in single_data or 'Calendar' in single_data:
        temp_data_list.append((single_data, _, 'calendar'))
    elif 'cantook' in single_data or 'Cantook' in single_data:
        temp_data_list.append((single_data, _, 'cantook'))
    elif 'clock' in single_data or 'Clock' in single_data:
        temp_data_list.append((single_data, _, 'clock'))
    elif 'contacts' in single_data or 'Contacts' in single_data:
        temp_data_list.append((single_data, _, 'contacts'))
    elif 'maps.me' in single_data or 'Maps.me' in single_data or 'map.me' in single_data or 'Map.me' in single_data:
        temp_data_list.append((single_data, _, 'maps.me'))
    elif 'piMusic' in single_data or 'PiMusic' in single_data or 'pimusicplayer' in single_data or 'PiMusicPlayer' in single_data:
        temp_data_list.append((single_data, _, 'pi_music'))
    elif 'zoom' in single_data or 'Zoom' in single_data:
        temp_data_list.append((single_data, _, 'zoom'))
    else:
        print("wrong!!!")

print(len(temp_data_list))

data_list = temp_data_list

result_list = []

reasoning_agent = VisualInterfaceAgent(api_key=API_KEY, api_base=API_BASE, model_name="google/gemini-2.5-pro", max_new_tokens=MAX_NEW_TOKENS)
format_agent = GPTAgent(api_key=API_KEY, api_base=API_BASE, model_name="qwen/qwen3-32b", max_new_tokens=MAX_NEW_TOKENS)

result_list = []

with open('./o1_data_visual_cot_all.json', 'w', encoding='utf-8') as json_file:
    json_file.write('[\n')

counter = 0

for i in range(len(data_list)):
    if i % 10 == 0:
        print(i)

    record, image_path, app_name = data_list[i]
    task, actions = parse_interaction_history(record)
    images_path = list_sorted_files_in_directory('./../../ground_data/android-lab-train/images/' + image_path)

    round_num = len(actions)

    reasoning_agent_sys = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT_VIS_THINKING
        }
    ]

    format_agent_sys = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT_REASONING_FORMAT
        }
    ]

    history_state = []

    for j in range(round_num):

        current_action = actions[j]
        current_action = current_action.replace('type(', 'text(')

        while True:
            record_dict = {}
            record_dict["task"] = 'You should use ' + app_name + ' to complete the following task: ' + task

            prompt = f"<TASK INSTRUCTION> \n {task} \n </TASK INSTRUCTION> \n <CALLED FUNCTION> \n {current_action} \n </CALLED FUNCTION> \n <HISTORY INFO> \n {str(history_state)} \n </HISTORY INFO> \n\n Please output <REASONING>...</REASONING> part with Chain of Thought format step by step."

            message = reasoning_agent.prompt_to_message(images_path[j], prompt)
            res = reasoning_agent.act([*reasoning_agent_sys, message])

            prompt = f"<REASONING> \n {res} \n </REASONING> \n <CALLED FUNCTION> \n {current_action} \n </CALLED FUNCTION>."

            message = format_agent.prompt_to_message(prompt)
            format_res = format_agent.act([*format_agent_sys, message])

            state_assessment = extract_state_assessment(format_res)
            called_function = extract_function_call(format_res)
            reasoning = extract_reasoning(format_res)

            if state_assessment == None:
                continue

            if reasoning == None:
                continue

            if called_function == None:
                continue

            round_str = f"round {j+1}"
            record_dict["id"] = counter
            record_dict["round"] = round_str
            record_dict["action"] = current_action
            record_dict["reasoning"] = format_res
            record_dict["image_path"] = images_path[j]
            record_dict["history_state"] = str(history_state)

            with open('./o1_data_visual_cot_all.json', 'a', encoding='utf-8') as json_file:
                json.dump(record_dict, json_file, ensure_ascii=False, indent=4)
                if i < len(data_list) - 1:
                    json_file.write(',\n')
                else:
                    json_file.write('\n')

            result_list.append(record_dict)

            counter += 1

            history_state.append(state_assessment)

            break

with open('./o1_data_visual_cot_all.json', 'a', encoding='utf-8') as json_file:
    json_file.write(']')

print(len(result_list))