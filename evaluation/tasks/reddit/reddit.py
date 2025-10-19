from evaluation.task import *
from evaluation.tasks.llm_evaluator import LLMEvaluator
import base64
import requests
import os
from typing import Dict, Any, List
import json
import traceback

class SingleTask_Reddit_LLM_1(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = (
            "Please analyze this Reddit screenshot and verify whether the user has successfully joined "
            "the ChatGPT discussion group (e.g., shows 'Joined' or membership status for r/ChatGPT). "
            "Respond in JSON as {\"joined_chatgpt_group\": bool}"
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
                return {
                    "judge_page": True,
                    "1": llm_result.get("joined_chatgpt_group", False),
                    "complete": llm_result.get("joined_chatgpt_group", False),
                }
            except Exception as e:
                print(f"LLM analysis failed: {e}")
        return {"judge_page": True, "1": False, "complete": False}


class SingleTask_Reddit_LLM_2(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = (
            "Please analyze this Reddit screenshot and verify whether the current tab/page is 'Popular'. "
            "Respond in JSON as {\"on_popular_page\": bool}"
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
                return {
                    "judge_page": True,
                    "1": llm_result.get("on_popular_page", False),
                    "complete": llm_result.get("on_popular_page", False),
                }
            except Exception as e:
                print(f"LLM analysis failed: {e}")
        return {"judge_page": True, "1": False, "complete": False}


class SingleTask_Reddit_LLM_3(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = (
            "Please analyze this Reddit screenshot and verify both: "
            "(1) the search query text is exactly or semantically 'Qwen'; "
            "(2) the time filter is set to 'Today'. "
            "Respond in JSON as {\"searched_qwen\": bool, \"time_filter_today\": bool}"
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
                searched_qwen = llm_result.get("searched_qwen", False)
                time_today = llm_result.get("time_filter_today", False)
                return {
                    "judge_page": True,
                    "1": searched_qwen,
                    "2": time_today,
                    "complete": searched_qwen and time_today,
                }
            except Exception as e:
                print(f"LLM analysis failed: {e}")
        return {"judge_page": True, "1": False, "2": False, "complete": False}


class SingleTask_Reddit_LLM_4(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = (
            "Please analyze this Reddit screenshot and verify both: "
            "(1) the search query text is exactly or semantically 'Qwen'; "
            "(2) the results are sorted by 'New' (latest). "
            "Respond in JSON as {\"searched_qwen\": bool, \"sorted_by_new\": bool}"
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
                searched_qwen = llm_result.get("searched_qwen", False)
                sorted_by_new = llm_result.get("sorted_by_new", False)
                return {
                    "judge_page": True,
                    "1": searched_qwen,
                    "2": sorted_by_new,
                    "complete": searched_qwen and sorted_by_new,
                }
            except Exception as e:
                print(f"LLM analysis failed: {e}")
        return {"judge_page": True, "1": False, "2": False, "complete": False}


class SingleTask_Reddit_LLM_5(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = (
            "Please analyze this Reddit screenshot and verify whether the user is not a member of r/ChatGPT (i.e., has left). "
            "Evidence should include the presence of a 'Join' button instead of 'Joined'."
            "Respond in JSON as {\"left_chatgpt_group\": bool}"
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
                return {
                    "judge_page": True,
                    "1": llm_result.get("left_chatgpt_group", False),
                    "complete": llm_result.get("left_chatgpt_group", False),
                }
            except Exception as e:
                print(f"LLM analysis failed: {e}")
        return {"judge_page": True, "1": False, "complete": False}