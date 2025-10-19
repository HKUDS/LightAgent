from evaluation.task import *
from evaluation.tasks.llm_evaluator import LLMEvaluator
import base64
import requests
import os
from typing import Dict, Any, List
import json
import traceback

class SingleTask_Zoom_1(SingleTask):

    def judge_page(self, xml_compressed_tree):
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "Join with a personal link name"):
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "123 456 7890")
        if len(outs) > 0:
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_Zoom_2(SingleTask):

    def judge_page(self, xml_compressed_tree):
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "Join with a personal link name"):
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        judge_key1 = False
        judge_key2 = False
        outs1 = find_subtrees_of_parents_with_key(xml_compressed_tree, "098 765 4321")
        outs2 = find_subtrees_of_parents_with_key(xml_compressed_tree, "Alice")
        if len(outs1) > 0:
            judge_key1 = True
        if len(outs2) > 0:
            judge_key2 = True
        outcome = {"judge_page": True, "1": judge_key1, "2": judge_key2, "complete": judge_key1 and judge_key2}
        return outcome


class SingleTask_Zoom_3(SingleTask):

    def judge_page(self, xml_compressed_tree):
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "Join with a personal link name"):
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        judge_key1 = False
        judge_key2 = False
        judge_key3 = False
        outs1 = find_subtrees_of_parents_with_key(xml_compressed_tree, "123 456 7890")
        outs2_tree = find_subtrees_of_parents_with_key(xml_compressed_tree, "Don't Connect To Audio")
        outs2 = find_subtrees_of_parents_with_key(outs2_tree[0], "On, switch")
        outs3_tree = find_subtrees_of_parents_with_key(xml_compressed_tree, "Turn Off My Video")
        outs3 = find_subtrees_of_parents_with_key(outs3_tree[0], "On, switch")
        if len(outs1) > 0:
            judge_key1 = True
        if len(outs2) > 0:
            judge_key2 = True
        if len(outs3) > 0:
            judge_key3 = True
        outcome = {"judge_page": True, "1": judge_key1, "2": judge_key2, "3": judge_key3,
                   "complete": judge_key1 and judge_key2 and judge_key3}
        return outcome


class SingleTask_Zoom_4(SingleTask):

    def judge_page(self, xml_compressed_tree):
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "Auto-connect to audio"):
            return False
        return True

    def _get_screenshot_path(self, line):
        if not line or "image" not in line:
            return None
        image_path = line["image"]
        if not image_path:
            return None
        return image_path

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        
        # Try to get the screenshot if available
        screenshot_path = self._get_screenshot_path(line)
        
        judge_key = False
        outs_tree = find_subtrees_of_parents_with_key(xml_compressed_tree, "Auto-connect to audio")
        outs = find_subtrees_of_parents_with_key(outs_tree[0], "WiFi or cellular data")
        if len(outs) > 0:
            judge_key = True
        outcome = {"judge_page": True, "1": judge_key, "complete": judge_key}
        
        # Add screenshot path to outcome if found
        if screenshot_path:
            outcome["screenshot"] = screenshot_path
            
        return outcome


class SingleTask_Zoom_5(SingleTask):

    def judge_page(self, xml_compressed_tree):
        if (not find_subtrees_of_parents_with_key(xml_compressed_tree, "Reaction skin tone")
                or not find_subtrees_of_parents_with_key(xml_compressed_tree, "Medium-light")):
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        judge_key = False
        outs_tree = find_subtrees_of_parents_with_key(xml_compressed_tree, "Medium-light")
        outs = find_subtrees_of_parents_with_key(outs_tree[0], "Selected")
        if len(outs) > 0:
            judge_key = True
        outcome = {"judge_page": True, "1": judge_key, "complete": judge_key}
        return outcome


class SingleTask_Zoom_LLM_1(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is this the 'Join with a personal link' page?
2. Is the number '123 456 7890' visible on the screen?
Respond in JSON format with keys: {"is_join_page": bool, "has_number": bool}"""

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
                    "judge_page": llm_result["is_join_page"],
                    "1": llm_result["has_number"],
                    "complete": llm_result["is_join_page"] and llm_result["has_number"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "Join with a personal link name"):
            return {"judge_page": False}
            
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "123 456 7890")
        if len(outs) > 0:
            return {"judge_page": True, "1": True, "complete": True}
        return {"judge_page": True, "1": False, "complete": False}


class SingleTask_Zoom_LLM_2(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is this the 'Join with a personal link' page?
2. Is the number '098 765 4321' visible on the screen?
3. Is the name 'Alice' visible on the screen?
Respond in JSON format with keys: {"is_join_page": bool, "has_number": bool, "has_name": bool}"""

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
                    "judge_page": llm_result["is_join_page"],
                    "1": llm_result["has_number"],
                    "2": llm_result["has_name"],
                    "complete": llm_result["is_join_page"] and llm_result["has_number"] and llm_result["has_name"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "Join with a personal link name"):
            return {"judge_page": False}
            
        judge_key1 = judge_key2 = False
        outs1 = find_subtrees_of_parents_with_key(xml_compressed_tree, "098 765 4321")
        outs2 = find_subtrees_of_parents_with_key(xml_compressed_tree, "Alice")
        if len(outs1) > 0:
            judge_key1 = True
        if len(outs2) > 0:
            judge_key2 = True
        return {"judge_page": True, "1": judge_key1, "2": judge_key2, "complete": judge_key1 and judge_key2}


class SingleTask_Zoom_LLM_3(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is this the 'Join with a personal link' page?
2. Is the number '123 456 7890' visible on the screen?
3. Is the 'Don't Connect To Audio' switch turned ON?
4. Is the 'Turn Off My Video' switch turned ON?
Respond in JSON format with keys: {"is_join_page": bool, "has_number": bool, "audio_off": bool, "video_off": bool}"""

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
                    "judge_page": llm_result["is_join_page"],
                    "1": llm_result["has_number"],
                    "2": llm_result["audio_off"],
                    "3": llm_result["video_off"],
                    "complete": (llm_result["is_join_page"] and llm_result["has_number"] and 
                               llm_result["audio_off"] and llm_result["video_off"])
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "Join with a personal link name"):
            return {"judge_page": False}
            
        judge_key1 = judge_key2 = judge_key3 = False
        outs1 = find_subtrees_of_parents_with_key(xml_compressed_tree, "123 456 7890")
        outs2_tree = find_subtrees_of_parents_with_key(xml_compressed_tree, "Don't Connect To Audio")
        outs2 = find_subtrees_of_parents_with_key(outs2_tree[0], "On, switch") if outs2_tree else []
        outs3_tree = find_subtrees_of_parents_with_key(xml_compressed_tree, "Turn Off My Video")
        outs3 = find_subtrees_of_parents_with_key(outs3_tree[0], "On, switch") if outs3_tree else []
        if len(outs1) > 0:
            judge_key1 = True
        if len(outs2) > 0:
            judge_key2 = True
        if len(outs3) > 0:
            judge_key3 = True
        return {"judge_page": True, "1": judge_key1, "2": judge_key2, "3": judge_key3,
                "complete": judge_key1 and judge_key2 and judge_key3}


class SingleTask_Zoom_LLM_4(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is this the 'Auto-connect to audio' settings page?
2. Is 'WiFi or cellular data' option selected?
Respond in JSON format with keys: {"is_settings_page": bool, "wifi_selected": bool}"""

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
                    "judge_page": llm_result["is_settings_page"],
                    "1": llm_result["wifi_selected"],
                    "complete": llm_result["is_settings_page"] and llm_result["wifi_selected"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "Auto-connect to audio"):
            return {"judge_page": False}
            
        judge_key = False
        outs_tree = find_subtrees_of_parents_with_key(xml_compressed_tree, "Auto-connect to audio")
        outs = find_subtrees_of_parents_with_key(outs_tree[0], "WiFi or cellular data") if outs_tree else []
        if len(outs) > 0:
            judge_key = True
        return {"judge_page": True, "1": judge_key, "complete": judge_key}


class SingleTask_Zoom_LLM_5(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is this the 'Reaction skin tone' settings page?
2. Is the 'Medium-light' skin tone option selected?
Respond in JSON format with keys: {"is_settings_page": bool, "medium_light_selected": bool}"""

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
                    "judge_page": llm_result["is_settings_page"],
                    "1": llm_result["medium_light_selected"],
                    "complete": llm_result["is_settings_page"] and llm_result["medium_light_selected"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        if (not find_subtrees_of_parents_with_key(xml_compressed_tree, "Reaction skin tone")
                or not find_subtrees_of_parents_with_key(xml_compressed_tree, "Medium-light")):
            return {"judge_page": False}
            
        judge_key = False
        outs_tree = find_subtrees_of_parents_with_key(xml_compressed_tree, "Medium-light")
        outs = find_subtrees_of_parents_with_key(outs_tree[0], "Selected") if outs_tree else []
        if len(outs) > 0:
            judge_key = True
        return {"judge_page": True, "1": judge_key, "complete": judge_key}
