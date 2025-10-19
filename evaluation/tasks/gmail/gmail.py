from evaluation.task import *
import base64
import requests
import os
from typing import Dict, Any, List
import json
import traceback
from evaluation.tasks.llm_evaluator import LLMEvaluator


class SingleTask_Gmail_LLM_1(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this Gmail screenshot and verify:
1. Is this the email composition/editing page?
2. Is the recipient field filled with "user_test@gmail.com"?
3. Is the subject field filled with "Inquire about academic collaboration opportunities,"?
4. Does the email content convey the same meaning as "Can I have an online meeting with you at 5pm today to discuss this?" (allowing for slight variations in wording while maintaining the same intent)?
Respond in JSON format with keys: {"is_compose_page": bool, "correct_recipient": bool, "correct_subject": bool, "correct_content": bool}"""

    def judge_page(self, line):
        if line["parsed_action"]["action"] != "finish":
            return False
        return True

    def _get_screenshot_path(self, line):
        if not line:
            return None
        base_screenshot = line.get("image")
        if not base_screenshot:
            return None
        return base_screenshot

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(line):
            return {"judge_page": False}
        
        screenshot_path = self._get_screenshot_path(line)
        
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                llm_result = self.llm_evaluator.analyze_screenshot(screenshot_path, self.task_prompt)
                
                result = {
                    "judge_page": llm_result["is_compose_page"],
                    "1": llm_result["correct_recipient"],
                    "2": llm_result["correct_subject"],
                    "3": llm_result["correct_content"],
                    "complete": (llm_result["is_compose_page"] and llm_result["correct_recipient"] and 
                               llm_result["correct_subject"] and llm_result["correct_content"])
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")


class SingleTask_Gmail_LLM_2(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this Gmail screenshot and verify:
1. Is this the email reply composition page?
2. Is the original email subject "Ask about project progress" visible?
3. Does the reply content convey the same meaning as "The main experimental part has been completed and the ablation experiment is underway." (allowing for slight variations in wording while maintaining the same intent)?
Respond in JSON format with keys: {"is_reply_page": bool, "correct_subject": bool, "correct_content": bool}"""

    def judge_page(self, line):
        if line["parsed_action"]["action"] != "finish":
            return False
        return True

    def _get_screenshot_path(self, line):
        if not line:
            return None
        base_screenshot = line.get("image")
        if not base_screenshot:
            return None
        return base_screenshot

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(line):
            return {"judge_page": False}
        
        screenshot_path = self._get_screenshot_path(line)
        
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                llm_result = self.llm_evaluator.analyze_screenshot(screenshot_path, self.task_prompt)
                
                result = {
                    "judge_page": llm_result["is_reply_page"],
                    "1": llm_result["correct_subject"],
                    "2": llm_result["correct_content"],
                    "complete": (llm_result["is_reply_page"] and llm_result["correct_subject"] and 
                               llm_result["correct_content"])
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}")


class SingleTask_Gmail_LLM_3(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text and verify:
Is the date of the online meeting about TA's task correctly identified as August 20, 2025 (or equivalent formats like 2025.08.20, 08/20/2025, etc.)?

Please provide the answer in JSON format with keys: {"has_correct_date": bool}"""

    def judge_page(self, line):
        if line["parsed_action"]["action"] != "finish":
            return False
        return True

    def _get_text_content(self, line):
        if not line:
            return None
        return json.dumps(line["parsed_action"])

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(line):
            return {"judge_page": False}
        
        text_content = self._get_text_content(line)
        
        if text_content:
            try:
                llm_result = self.llm_evaluator.analyze_text(text_content, self.task_prompt)
                
                result = {
                    "judge_page": True,
                    "1": llm_result.get("has_correct_date", False),
                    "complete": llm_result.get("has_correct_date", False)
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}")


class SingleTask_Gmail_LLM_4(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this Gmail screenshot and verify:
The email titled "Congratulations! You've Won a Free Gift!" should be marked as spam, and after being marked as spam it should NOT be visible in the current mailbox interface (e.g., Inbox).

Note: If the email is still visible in the current mailbox interface, the task is NOT complete.

Respond in JSON format with keys: {"spam_email_not_visible": bool}"""

    def judge_page(self, line):
        if line["parsed_action"]["action"] != "finish":
            return False
        return True

    def _get_screenshot_path(self, line):
        if not line:
            return None
        base_screenshot = line.get("image")
        if not base_screenshot:
            return None
        return base_screenshot

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(line):
            return {"judge_page": False}
        
        screenshot_path = self._get_screenshot_path(line)
        
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                llm_result = self.llm_evaluator.analyze_screenshot(screenshot_path, self.task_prompt)
                
                result = {
                    "judge_page": True,
                    "1": llm_result.get("spam_email_not_visible", False),
                    "complete": llm_result.get("spam_email_not_visible", False)
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}")


class SingleTask_Gmail_LLM_5(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this Gmail screenshot and verify:
Is the current Gmail interface displayed in dark mode (e.g., the interface appears black or dark)?

Respond in JSON format with keys: {"is_dark_mode": bool}"""

    def judge_page(self, line):
        if line["parsed_action"]["action"] != "finish":
            return False
        return True

    def _get_screenshot_path(self, line):
        if not line:
            return None
        base_screenshot = line.get("image")
        if not base_screenshot:
            return None
        return base_screenshot

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(line):
            return {"judge_page": False}
        
        screenshot_path = self._get_screenshot_path(line)
        
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                llm_result = self.llm_evaluator.analyze_screenshot(screenshot_path, self.task_prompt)
                
                result = {
                    "judge_page": True,
                    "1": llm_result.get("is_dark_mode", False),
                    "complete": llm_result.get("is_dark_mode", False)
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}")


class SingleTask_Gmail_LLM_6(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text and verify:
Is the title of the email with attachment "TA arrangement for 2025-2026"?

Please provide the answer in JSON format with keys: {"correct_title": bool}"""

    def judge_page(self, line):
        if line["parsed_action"]["action"] != "finish":
            return False
        return True

    def _get_text_content(self, line):
        if not line:
            return None
        return json.dumps(line["parsed_action"])

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(line):
            return {"judge_page": False}
        
        text_content = self._get_text_content(line)
        
        if text_content:
            try:
                llm_result = self.llm_evaluator.analyze_text(text_content, self.task_prompt)
                
                result = {
                    "judge_page": True,
                    "1": llm_result.get("correct_title", False),
                    "complete": llm_result.get("correct_title", False)
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}")
                return {"judge_page": False}
        
        return {"judge_page": False}


class SingleTask_Gmail_LLM_7(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text and verify:
Is the title of the starred email "TA arrangement for 2025-2026"?

Please provide the answer in JSON format with keys: {"correct_title": bool}"""

    def judge_page(self, line):
        if line["parsed_action"]["action"] != "finish":
            return False
        return True

    def _get_text_content(self, line):
        if not line:
            return None
        return json.dumps(line["parsed_action"])

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(line):
            return {"judge_page": False}
        
        text_content = self._get_text_content(line)
        
        if text_content:
            try:
                llm_result = self.llm_evaluator.analyze_text(text_content, self.task_prompt)
                
                result = {
                    "judge_page": True,
                    "1": llm_result.get("correct_title", False),
                    "complete": llm_result.get("correct_title", False)
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}")
                return {"judge_page": False}
        
        return {"judge_page": False}
