from evaluation.task import *
from evaluation.tasks.llm_evaluator import LLMEvaluator
import base64
import requests
import os
from typing import Dict, Any, List
import json
import traceback

class SingleTask_Chrome_LLM_1(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = (
            "Please analyze this text and verify whether the final answer correctly states both: "
            "(1) The University of Hong Kong (HKU) was founded on March 30, 1911; "
            "(2) Its main campus is located at Pokfulam Road, Hong Kong. "
            "Respond in JSON with keys: {\"has_correct_info\": bool}"
        )
        self.standard_answer = (
            "The University of Hong Kong (HKU) was founded on March 30, 1911, and its main campus is located at Pokfulam Road, Hong Kong."
        )

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
                return {"judge_page": True, "1": llm_result.get("has_correct_info", False), "complete": llm_result.get("has_correct_info", False)}
            except Exception as e:
                print(f"LLM analysis failed: {e}")
        return {"judge_page": True, "1": False, "complete": False}


class SingleTask_Chrome_LLM_2(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = (
            "Please analyze this Chrome screenshot and verify: Is Chrome currently set to dark mode "
            "(i.e., the browser UI appears predominantly dark/black)? Respond in JSON as {\"is_dark_mode\": bool}"
        )

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
                return {"judge_page": True, "1": llm_result.get("is_dark_mode", False), "complete": llm_result.get("is_dark_mode", False)}
            except Exception as e:
                print(f"LLM analysis failed: {e}")
        return {"judge_page": True, "1": False, "complete": False}


class SingleTask_Chrome_LLM_3(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = (
            "Please analyze this text (final answer logs) and verify whether the bookmarked website found in "
            "Mobile Bookmarks is 'Google Scholar'. Respond in JSON with keys: {\"has_correct_bookmark\": bool}"
        )
        self.standard_answer = "Google Scholar"

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
                return {"judge_page": True, "1": llm_result.get("has_correct_bookmark", False), "complete": llm_result.get("has_correct_bookmark", False)}
            except Exception as e:
                print(f"LLM analysis failed: {e}")
        return {"judge_page": True, "1": False, "complete": False}


class SingleTask_Chrome_LLM_4(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = (
            "Please analyze this Chrome screenshot and verify: Is the current page the Wikipedia page for "
            "'Hyperbolic functions' (e.g., title shows 'Hyperbolic functions' and the site is Wikipedia)? "
            "Respond in JSON as {\"on_wikipedia_hyperbolic\": bool}"
        )

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
                return {"judge_page": True, "1": llm_result.get("on_wikipedia_hyperbolic", False), "complete": llm_result.get("on_wikipedia_hyperbolic", False)}
            except Exception as e:
                print(f"LLM analysis failed: {e}")
        return {"judge_page": True, "1": False, "complete": False}


class SingleTask_Chrome_LLM_5(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = (
            "Please analyze this Chrome screenshot and verify: Is the current page the GitHub homepage "
            "(e.g., recognizable GitHub branding and 'github.com' visible)? Respond in JSON as {\"on_github_home\": bool}"
        )

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
                return {"judge_page": True, "1": llm_result.get("on_github_home", False), "complete": llm_result.get("on_github_home", False)}
            except Exception as e:
                print(f"LLM analysis failed: {e}")
        return {"judge_page": True, "1": False, "complete": False}


class SingleTask_Chrome_LLM_6(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = (
            "Please analyze this Chrome screenshot and verify: Is the current page the Nike Hong Kong site "
            "(e.g., 'Nike Hong Kong' or 'nike.com/hk' indications)? Respond in JSON as {\"on_nike_hk\": bool}"
        )

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
                return {"judge_page": True, "1": llm_result.get("on_nike_hk", False), "complete": llm_result.get("on_nike_hk", False)}
            except Exception as e:
                print(f"LLM analysis failed: {e}")
        return {"judge_page": True, "1": False, "complete": False}


class SingleTask_Chrome_LLM_7(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = (
            "Please analyze this Chrome screenshot and verify: Is a new Incognito window currently open? "
            "Look for indicators like 'Incognito' text, incognito icon (spy/mask symbol), or dark theme "
            "that typically indicates an Incognito browsing session. Respond in JSON as {\"incognito_window_open\": bool}"
        )

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
                return {"judge_page": True, "1": llm_result.get("incognito_window_open", False), "complete": llm_result.get("incognito_window_open", False)}
            except Exception as e:
                print(f"LLM analysis failed: {e}")
        return {"judge_page": True, "1": False, "complete": False}


