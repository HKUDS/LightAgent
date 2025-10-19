import templates.seeact_screenshot_prompts as SeeActPrompts
from evaluation.definition import *
from evaluation.utils import *
from templates import *
import re

from templates.android_screenshot_template import SYSTEM_PROMPT_ANDROID_MLLM_CLOUD_V0

from agent.model import OpenAIAgent

class AutoTask():
    def __init__(self, instruction, controller, page_executor, agent, record, command_per_step, **kwargs):
        self.controller = controller
        self.page_executor = page_executor
        self.agent = agent
        self.record = record
        self.kwargs = kwargs
        self.set_system_prompt(instruction)
        self.record.command_per_step = [command_per_step]
        # pimusic and map.me need ac to fetch xml
        if "map.me" in instruction or "pimusic" in instruction:
            self.accessibility = self.controller.check_ac_survive()
        else:
            self.accessibility = False

        self.instruction = instruction
        self.cloud_status = False

    def set_system_prompt(self, instruction):
        self.record.history = [{
            "role": "system",
            "content": self.agent.system_prompt(instruction)
        }]

    def run_step(self, round_count):
        self.record.update_before(controller=self.controller, need_screenshot=True, ac_status=self.accessibility)
        compressed_xml_json = self.record.get_latest_xml()

        prompt = f"" if round_count == 0 else "** XML **\n"
        try:
            current_message = {"role": "user", "content": prompt + compressed_xml_json}
            if self.agent.name == "GLMModelAgent":
                current_message["current_app"] = self.controller.get_current_activity()
            rsp = self.agent.act([*self.record.history, current_message])
        except Exception as e:
            print_with_color(f"Error: {e}", "red")

        exe_res = self.page_executor(get_code_snippet(rsp))
        self.record.update_after(exe_res, rsp)
        self.record.turn_number += 1


class TextOnlyTask(AutoTask):
    def set_system_prompt(self, instruction):
        self.record.history = [{
            "role": "system",
            "content": SYSTEM_PROMPT_ANDROID_TEXT_GPT + f"\n\nTask Instruction: {instruction}"
        }]

class ScreenshotTask(TextOnlyTask):
    def run_step(self, round_count):
        if round_count == 1:
            self.starter_agent = OpenAIAgent(api_key="API_KEY", api_base="API_BASE", model_name="google/gemini-2.5-pro")
            self.starter_system_prompt_norm = [{
                "role": "system",
                "content": SYSTEM_PROMPT_ANDROID_MLLM_CONTROL_STARTER
            }]
            
            starter_prompt = f"Task: {self.instruction}"
            starter_message = self.starter_agent.prompt_to_message_text(starter_prompt)
            starter_response = self.starter_agent.act([*self.starter_system_prompt_norm, starter_message])
            
            self.parse_starter_response(starter_response)
            
            self.cloud_agent = OpenAIAgent(api_key="API_KEY", api_base="API_BASE", model_name="google/gemini-2.5-pro")
            self.cloud_system_prompt_norm = [{
                "role": "system",
                "content": SYSTEM_PROMPT_ANDROID_MLLM_CLOUD_V0
            }]

            self.control_agent = OpenAIAgent(api_key="API_KEY", api_base="API_BASE", model_name="google/gemini-2.5-pro")
            self.control_system_prompt_norm = [{
                "role": "system",
                "content": SYSTEM_PROMPT_ANDROID_MLLM_CONTROL_V0
            }]

        # Reset control-related flags for this round
        self.control_used_this_round = False
        
        self.record.update_before(controller=self.controller, need_screenshot=True, ac_status=self.accessibility,
                                  need_labeled=True)
        try:
            xml = self.record.get_latest_xml()
            image_path = self.record.labeled_current_screenshot_path

            def build_prompt(prefix=""):
                base = self.instruction + "\nHistory Information: " + str(self.record.history) + "\n Current Information: <image>"
                return (prefix + base) if prefix else base

            def use_cloud_agent(prompt_text):
                current_message = self.cloud_agent.prompt_to_message_cloud(prompt_text, [image_path])
                return self.cloud_agent.act([*self.cloud_system_prompt_norm, *current_message])

            def use_local_agent(prompt_text):
                current_message = self.agent.prompt_to_message_visual(prompt_text, image_path)
                return self.agent.act([*self.system_prompt, *current_message])

            def should_switch_to_cloud(round_count):
                if (round_count >= self.monitoring_start_from and 
                    (round_count - self.monitoring_start_from) % self.monitoring_frequency == 0):
                    control_prompt = build_prompt("Task: ")
                    current_message = self.control_agent.prompt_to_message_cloud(control_prompt, [image_path])
                    rsp_control = self.control_agent.act([*self.control_system_prompt_norm, *current_message])
                    print("Control Agent Response: ", rsp_control)
                    self.control_used_this_round = True
                    return rsp_control == "CLOUD"
                return False

            def determine_agent_strategy():
                if self.cloud_status:
                    return True, "Already in cloud mode"
                elif round_count == 1 and self.initial_intervention:
                    return True, "First round use cloud (starter decision)"
                elif should_switch_to_cloud(round_count):
                    return True, "Need to switch to cloud (control decision)"
                else:
                    return False, "Use local agent"

            def execute_with_agent():
                use_cloud, reason = determine_agent_strategy()
                control_used = getattr(self, 'control_used_this_round', False)
                
                if use_cloud:
                    rsp = use_cloud_agent(build_prompt())
                    if reason == "Need to switch to cloud (control decision)":
                        self.cloud_status = True
                        print("Switch to cloud")
                else:
                    rsp = use_local_agent(build_prompt())
                
                return rsp, use_cloud, reason, control_used

            rsp, used_cloud_agent, agent_reason, control_used = execute_with_agent()
            
            pattern = r'<STATE_ASSESSMENT>\s*(.*?)\s*</STATE_ASSESSMENT>'
            match = re.search(pattern, rsp, re.DOTALL)

            if match:
                prompt_his = match.group(1)
            else:
                prompt_his = None

        except Exception as e:
            import traceback
            print(traceback.print_exc())

        exe_res = self.page_executor(get_code_snippet_cot(rsp))
        
        if used_cloud_agent:
            print("Cloud Agent Used")
            self.record.update_after_cot(exe_res, rsp, prompt_his, get_code_snippet_cot_v3(rsp), cloud_status=True, control_status=control_used)
        else:
            print("Local Agent Used")
            self.record.update_after_cot(exe_res, rsp, prompt_his, get_code_snippet_cot_v3(rsp), control_status=control_used)

        self.record.turn_number += 1

    def parse_starter_response(self, response):
        try:
            self.initial_intervention = True
            
            start_match = re.search(r'<MONITORING START FROM>\s*(\d+)\s*</MONITORING START FROM>', response, re.IGNORECASE | re.DOTALL)
            if start_match:
                self.monitoring_start_from = int(start_match.group(1))
            else:
                self.monitoring_start_from = 5
            
            freq_match = re.search(r'<MONITORING FREQUENCY>\s*(\d+)\s*</MONITORING FREQUENCY>', response, re.IGNORECASE | re.DOTALL)
            if freq_match:
                self.monitoring_frequency = int(freq_match.group(1))
            else:
                self.monitoring_frequency = 5
            
            print(f"Monitoring Start From={self.monitoring_start_from}, "
                  f"Monitoring Frequency={self.monitoring_frequency}")
            
        except Exception as e:
            print(f"Error parsing starter response: {e}")
            self.monitoring_start_from = 5
            self.monitoring_frequency = 5


class CogAgentTask(TextOnlyTask):
    def run_step(self, round_count):
        self.record.update_before(controller=self.controller, need_screenshot=True, ac_status=self.accessibility,
                                  need_labeled=True)
        prompt = f"" if round_count == 0 else json.dumps({"current_app": self.controller.get_current_app()},
                                                         ensure_ascii=False)
        try:
            image_path = self.page_executor.current_screenshot
            current_message = self.agent.prompt_to_message(prompt, [image_path])
            rsp = self.agent.act([*self.record.history, current_message])
        except Exception as e:
            import traceback
            print(traceback.print_exc())
            # print_with_color(f"Error: {e}", "red")

        exe_res = self.page_executor(get_code_snippet(rsp))
        self.record.update_after(exe_res, rsp)
        self.record.turn_number += 1

    def set_system_prompt(self, instruction):
        self.record.history = [{
            "role": "system",
            "content": SYSTEM_PROMPT_ANDROID_MLLM_CogAgent + f"\n\nTask Instruction: {instruction}"
        }]


class ScreenshotReactTask(ScreenshotTask):
    def set_system_prompt(self, instruction):
        self.record.history = [{
            "role": "system",
            "content": SYSTEM_PROMPT_ANDROID_MLLM_DIRECT_REACT + f"\n\nTask Instruction: {instruction}"
        }]

class ScreenshotReactTask_Cloud_hyper(ScreenshotTask):
    def set_system_prompt(self, instruction):
        sys_content = SYSTEM_PROMPT_ANDROID_MLLM_CLOUD_SMALL
        self.system_prompt = [{
            "role": "system",
            "content": sys_content
        }]

class ScreenSeeActTask(TextOnlyTask):

    def set_system_prompt(self, instruction):
        self.record.history = [{
            "role": "system",
            "content": SeeActPrompts.QUERY_SYSTEM_PROMPT
        }]
        self.stage_one_record = []
        self.instruction = instruction

    def run_step(self, round_count):
        self.record.update_before(controller=self.controller, need_screenshot=True, ac_status=self.accessibility,
                                  need_labeled=False)
        try:
            xml_tree = self.record.get_latest_xml_tree()
            choices_list = extract_bounds(xml_tree)
            image_path = self.page_executor.current_screenshot
            system_prompt = SeeActPrompts.QUERY_SYSTEM_PROMPT
            query_user_prompt = SeeActPrompts.QUERY_USER_PROMPT.format(
                task=self.instruction,
                previous_actions=("\n\n".join(self.stage_one_record) or "None")
            )
            query_message = self.agent.prompt_to_message(query_user_prompt, [image_path])
            referring_user_prompt = SeeActPrompts.REFERRING_USER_PROMPT.format(
                option_prompt="\n".join(f"{item['key']} | {item['value']}" for item in choices_list)
            )

            messages = [
                {"role": "system", "content": system_prompt},
                query_message,
            ]

            # Stage 1. Query
            print(">> Stage 1. Query")
            with open("monitor.log", "w") as f:
                f.write(json.dumps(messages, indent=4))
            description = self.agent.act(messages)
            print(description, end="\n\n")
            with open("monitor.log", "w") as f:
                f.write(description)
            messages.append({"role": "assistant", "content": description})
            messages.append({"role": "user", "content": referring_user_prompt})

            # Stage 2. Referring
            print(">> Stage 2. Referring")
            with open("monitor.log", "w") as f:
                f.write(json.dumps(messages, indent=4))

            referring = self.agent.act(messages)
            print(referring, end="\n\n")
            with open("monitor.log", "w") as f:
                f.write(referring)


        except Exception as e:
            import traceback
            print(traceback.print_exc())
            # print_with_color(f"Error: {e}", "red")
            # exit(1)
        referring = referring.split("Final Answer:")[-1].strip()
        exe_res = self.page_executor(get_code_snippet(referring))
        self.stage_one_record.append(description)
        self.record.update_after(exe_res, description + "\n\n==========\n\n" + referring)
        self.record.turn_number += 1


class TextOnlyReactTask(TextOnlyTask):
    def set_system_prompt(self, instruction):
        self.record.history = [{
            "role": "system",
            "content": SYSTEM_PROMPT_ANDROID_TEXT_ReAct + f"\n\nTask Instruction: {instruction}"
        }]


class TextOnlyFineTuneTask(TextOnlyTask):
    def set_system_prompt(self, instruction):
        self.record.history = [{
            "role": "system",
            "content": SYSTEM_PROMPT_ANDROID_TEXT_GLM_v1_5 + f"\n\nTask Instruction: {instruction}"
        }]

    def run_step(self, round_count):
        self.record.update_before(controller=self.controller, need_screenshot=True, ac_status=self.accessibility)
        compressed_xml_json = self.record.get_latest_xml()

        # prompt = f"" if round_count == 0 else "** XML **\n"
        try:
            app_info = f"{json.dumps({'current_app': self.controller.get_current_app()}, ensure_ascii=False)}\n"
            current_message = {"role": "user", "content": app_info + compressed_xml_json}
            rsp = self.agent.act([*self.record.history, current_message])
        except Exception as e:
            print_with_color(f"Error: {e}", "red")

        exe_res = self.page_executor(get_code_snippet(rsp))
        self.record.update_after(exe_res, rsp)
        self.record.turn_number += 1


class TextOnlyFineTuneTask_long(TextOnlyFineTuneTask):
    def set_system_prompt(self, instruction):
        self.record.history = [{
            "role": "system",
            "content": SYSTEM_PROMPT_ANDROID_TEXT_GPT + f"\n\nTask Instruction: {instruction}"
        }]
