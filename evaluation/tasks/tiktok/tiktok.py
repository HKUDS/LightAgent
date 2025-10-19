from evaluation.task import *
from evaluation.tasks.llm_evaluator import LLMEvaluator
import base64
import requests
import os
from typing import Dict, Any, List
import json
import traceback

class SingleTask_TikTok_LLM_1(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = (
            "Please analyze this TikTok profile screenshot and verify: "
            "Is this the homepage/profile page of 'IShowSpeed' (e.g., profile name shows 'IShowSpeed' or handle like '@ishowspeed')? "
            'Respond in JSON as {"on_ishowspeed_home": bool}'
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
                return {"judge_page": True, "1": llm_result.get("on_ishowspeed_home", False), "complete": llm_result.get("on_ishowspeed_home", False)}
            except Exception as e:
                print(f"LLM analysis failed: {e}")
        return {"judge_page": True, "1": False, "complete": False}


class SingleTask_TikTok_LLM_2(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = (
            "Please analyze this text (final answer logs) and determine whether it states the user does NOT follow this blogger. "
            'Respond in JSON as {"not_following": bool}'
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
                ok = llm_result.get("not_following", False)
                return {"judge_page": True, "1": ok, "complete": ok}
            except Exception as e:
                print(f"LLM analysis failed: {e}")
        return {"judge_page": True, "1": False, "complete": False}


class SingleTask_TikTok_LLM_3(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = (
            "Please analyze this TikTok screenshot and verify: Is the current page the search results for 'iphone 17' "
            '(i.e., the search query shows "iphone 17" and results are shown)? '
            'Respond in JSON as {"on_iphone17_search": bool}'
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
                ok = llm_result.get("on_iphone17_search", False)
                return {"judge_page": True, "1": ok, "complete": ok}
            except Exception as e:
                print(f"LLM analysis failed: {e}")
        return {"judge_page": True, "1": False, "complete": False}


class SingleTask_TikTok_LLM_4(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = (
            'Please analyze this text (final answer logs) and check the reported Messi account ID. '
            'Determine whether it equals exactly "messi.18642". '
            'Respond in JSON as {"correct_id": bool}'
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
                ok = llm_result.get("correct_id", False)
                return {"judge_page": True, "1": ok, "complete": ok}
            except Exception as e:
                print(f"LLM analysis failed: {e}")
        return {"judge_page": True, "1": False, "complete": False}


class SingleTask_TikTok_LLM_5(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = (
            "Please analyze this TikTok screenshot and verify: Is a video opened that is posted by 'LALIGA' "
            "and is about the Real Madrid vs Barcelona match (El Clásico)? "
            'Respond in JSON as {"laliga_el_clasico": bool}'
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
                ok = llm_result.get("laliga_el_clasico", False)
                return {"judge_page": True, "1": ok, "complete": ok}
            except Exception as e:
                print(f"LLM analysis failed: {e}")
        return {"judge_page": True, "1": False, "complete": False}


class SingleTask_TikTok_LLM_6(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = (
            "Please analyze this TikTok screenshot and verify: Is a video about Messi winning the 2022 Qatar World Cup opened "
            "(e.g., mentions of Messi winning in 2022 World Cup in Qatar, trophy scenes, or related captions)? "
            'Respond in JSON as {"messi_wc22": bool}'
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
                ok = llm_result.get("messi_wc22", False)
                return {"judge_page": True, "1": ok, "complete": ok}
            except Exception as e:
                print(f"LLM analysis failed: {e}")
        return {"judge_page": True, "1": False, "complete": False}

