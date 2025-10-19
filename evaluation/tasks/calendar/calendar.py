from evaluation.task import *
from evaluation.tasks.llm_evaluator import LLMEvaluator
import re
from typing import Dict
import base64
import requests
import os
from typing import Dict, Any, List
import json
import traceback

class SingleTask_calendar_1(SingleTask):

    def judge_page(self, xml_compressed_tree):
        # 判断是否包含 "Stanford"、"My location" 和 "Start"
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "work"):
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        key_1 = True
        key_2 = True
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Today")
        if (len(outs) == 0):
            key_1 = False
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "5:00 PM")
        if ((len(outs) == 0)):
            key_2 = False
        return {"judge_page": True, "1": True, "2": key_1, "3": key_2, "complete": key_1 and key_2}


class SingleTask_calendar_2(SingleTask):

    def judge_page(self, xml_compressed_tree):
        # 判断是否包含 "Stanford"、"My location" 和 "Start"
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "homework"):
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        key_2 = True
        key_3 = True
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "May 21")
        if ((len(outs) == 0)):
            key_2 = False
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "10 minutes before ")
        if ((len(outs) == 0)):
            key_3 = False
        return {"judge_page": True, "1": True, "2": key_2, "3": key_3, "complete": key_2 and key_3}


class SingleTask_calendar_3(SingleTask):

    def judge_page(self, xml_compressed_tree):
        # 判断是否包含 "Stanford"、"My location" 和 "Start"
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "meeting"):
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        key_2 = True
        key_3 = True
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "May 13")
        if ((len(outs) == 0)):
            key_2 = False
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "conference room B202 ")
        if ((len(outs) == 0)):
            key_3 = False
        return {"judge_page": True, "1": True, "2": key_2, "3": key_3, "complete": key_2 and key_3}


class SingleTask_calendar_4(SingleTask):

    def judge_page(self, xml_compressed_tree):
        # 判断是否包含 "Stanford"、"My location" 和 "Start"
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "new month"):
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        key_1 = True
        key_2 = True
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Jun 01")
        if (len(outs) == 0):
            key_1 = False
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Monthly")
        if ((len(outs) == 0)):
            key_2 = False
        return {"judge_page": True, "1": True, "2": key_1, "3": key_2, "complete": key_1 and key_2}


class SingleTask_calendar_5(SingleTask):

    def judge_page(self, xml_compressed_tree):
        # 判断是否包含 "Stanford"、"My location" 和 "Start"
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "work"):
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        key_1 = True
        key_2 = True
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Today")
        if (len(outs) == 0):
            key_1 = False
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "7:00 PM")
        if ((len(outs) == 0)):
            key_2 = False
        return {"judge_page": True, "1": True, "2": key_1, "3": key_2, "complete": key_1 and key_2}


class SingleTask_calendar_6(SingleTask):

    def judge_page(self, xml_compressed_tree):
        # 判断是否包含 "Stanford"、"My location" 和 "Start"
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "homework"):
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        self.edit_started_correctly = False
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        key = True
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "homework")
        if (len(outs) == 0):
            key = False
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "May 21")
        if (len(outs) == 0):
            key = False
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "10 minutes before ")
        if ((len(outs) == 0)):
            key = False
        if (key):
            self.edit_started_correctly = True
        key_1 = True
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "classroom 101")
        if (len(outs) == 0):
            key_1 = False
        return {"judge_page": True, "1": True, "2": self.edit_started_correctly, "3": key_1,
                "complete": self.edit_started_correctly and key_1}


class SingleTask_calendar_7(SingleTask):

    def judge_page(self, xml_compressed_tree):
        # 判断是否包含 "Stanford"、"My location" 和 "Start"
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "meeting"):
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        self.edit_started_correctly = False
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        key = True
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "meeting")
        if (len(outs) == 0):
            return False
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "May 13")
        if (len(outs) == 0):
            key = False
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "conference room B202 ")
        if ((len(outs) == 0)):
            key = False
        if (key):
            self.edit_started_correctly = True
        key_1 = True
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "30 minutes before")
        if (len(outs) == 0):
            key_1 = False
        return {"judge_page": True, "1": True, "2": self.edit_started_correctly, "3": key_1,
                "complete": self.edit_started_correctly and key_1}


class SingleTask_calendar_8(SingleTask):

    def judge_page(self, xml_compressed_tree):
        # 判断是否包含 "Stanford"、"My location" 和 "Start"
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "work"):
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        self.edit_started_correctly = False
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        key = True
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "work")
        if (len(outs) == 0):
            return False
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Today")
        if (len(outs) == 0):
            key = False
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "5:00 PM")
        if ((len(outs) == 0)):
            key = False
        if (key):
            self.edit_started_correctly = True
        key_1 = True
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "30 minutes before")
        if (len(outs) == 0):
            key_1 = False
        return {"judge_page": True, "1": True, "2": self.edit_started_correctly, "3": key_1,
                "complete": self.edit_started_correctly and key_1}


class SingleTask_calendar_9(SingleTask):

    def judge_page(self, xml_compressed_tree):
        # 判断是否包含 "Stanford"、"My location" 和 "Start"
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "work"):
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        self.edit_started_correctly = False
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        key = True
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "work")
        if (len(outs) == 0):
            return False
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Today")
        if (len(outs) == 0):
            key = False
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "5:00 PM")
        if ((len(outs) == 0)):
            key = False
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "30 minutes before")
        if ((len(outs) == 0)):
            key = False
        if (key):
            self.edit_started_correctly = True
        key_1 = True
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Daily")
        if (len(outs) == 0):
            key_1 = False
        return {"judge_page": True, "1": True, "2": self.edit_started_correctly, "3": key_1,
                "complete": self.edit_started_correctly and key_1}


class SingleTask_calendar_10(SingleTask):

    def judge_page(self, xml_compressed_tree):
        # 判断是否包含 "Stanford"、"My location" 和 "Start"
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "this_day"):
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        return {"judge_page": True, "1": True, "complete": True}


class SingleTask_calendar_11(SingleTask):

    def judge_page(self, xml_compressed_tree):
        # 判断是否包含 "Stanford"、"My location" 和 "Start"
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "this day"):
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        self.edit_started_correctly = True
        key_1 = True
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Weekly")
        if (len(outs) == 0):
            key_1 = False
        return {"judge_page": True, "1": True, "2": self.edit_started_correctly, "3": key_1,
                "complete": self.edit_started_correctly and key_1}


class SingleTask_calendar_12(SingleTask):

    def judge_page(self, xml_compressed_tree):
        # 判断是否包含 "Stanford"、"My location" 和 "Start"
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "this day"):
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Weekly")
        if (len(outs) > 0):
            self.edit_started_correctly = True
        else:
            self.edit_started_correctly = False
        key_1 = True
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Hello")
        if (len(outs) == 0):
            key_1 = False
        return {"judge_page": True, "1": True, "2": self.edit_started_correctly, "3": key_1,
                "complete": self.edit_started_correctly and key_1}


class SingleTask_calendar_13(SingleTask):

    def judge_page(self, xml_compressed_tree):
        # 判断是否包含 "Stanford"、"My location" 和 "Start"
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "exam"):
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        return {"judge_page": True, "1": True, "complete": True}


class SingleTask_calendar_14(SingleTask):

    def judge_page(self, xml_compressed_tree):
        # 判断是否包含 "Stanford"、"My location" 和 "Start"
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "exam"):
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        self.edit_started_correctly = True
        key_1 = True
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Yearly")
        if (len(outs) == 0):
            key_1 = False
        return {"judge_page": True, "1": True, "2": self.edit_started_correctly, "3": key_1,
                "complete": self.edit_started_correctly and key_1}

class SingleTask_calendar_LLM_1(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this calendar app screenshot and verify:
1. Is there an event titled "work"?
2. Is the event scheduled for today at 5:00 PM?
Respond in JSON format with keys: {"has_work_title": bool, "has_correct_time": bool}"""

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
                    "1": llm_result["has_work_title"],
                    "2": llm_result["has_correct_time"],
                    "3": True,
                    "complete": llm_result["has_work_title"] and llm_result["has_correct_time"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
        
        # Fallback to traditional check
        key_1 = key_2 = True
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Today")
        if (len(outs) == 0):
            key_1 = False
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "5:00 PM")
        if ((len(outs) == 0)):
            key_2 = False
        return {"judge_page": True, "1": True, "2": key_1, "3": key_2, "complete": key_1 and key_2}

class SingleTask_calendar_LLM_2(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this calendar app screenshot and verify:
1. Is there an event titled "homework"?
2. Is the event scheduled for May 21st?
3. Is there a notification set for 10 minutes before the event?
Respond in JSON format with keys: {"has_homework_title": bool, "has_correct_date": bool, "has_notification": bool}"""

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
                    "1": llm_result["has_homework_title"],
                    "2": llm_result["has_correct_date"],
                    "3": llm_result["has_notification"],
                    "complete": llm_result["has_homework_title"] and llm_result["has_correct_date"] and llm_result["has_notification"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
        
        # Fallback to traditional check
        key_2 = key_3 = True
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "May 21")
        if ((len(outs) == 0)):
            key_2 = False
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "10 minutes before ")
        if ((len(outs) == 0)):
            key_3 = False
        return {"judge_page": True, "1": True, "2": key_2, "3": key_3, "complete": key_2 and key_3}

class SingleTask_calendar_LLM_3(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this calendar app screenshot and verify:
1. Is there an event titled "meeting"?
2. Is the event scheduled for May 13th?
3. Is there a note mentioning "conference room B202"?
Respond in JSON format with keys: {"has_meeting_title": bool, "has_correct_date": bool, "has_room_note": bool}"""

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
                    "1": llm_result["has_meeting_title"],
                    "2": llm_result["has_correct_date"],
                    "3": llm_result["has_room_note"],
                    "complete": llm_result["has_meeting_title"] and llm_result["has_correct_date"] and llm_result["has_room_note"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
        
        # Fallback to traditional check
        key_2 = key_3 = True
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "May 13")
        if ((len(outs) == 0)):
            key_2 = False
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "conference room B202 ")
        if ((len(outs) == 0)):
            key_3 = False
        return {"judge_page": True, "1": True, "2": key_2, "3": key_3, "complete": key_2 and key_3}

class SingleTask_calendar_LLM_4(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this calendar app screenshot and verify:
1. Is there an event starting on June 1st, 2024?
2. Is the event set to repeat monthly?
Respond in JSON format with keys: {"has_correct_date": bool, "has_monthly_repeat": bool}"""

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
                    "1": llm_result["has_correct_date"],
                    "2": llm_result["has_monthly_repeat"],
                    "3": True,
                    "complete": llm_result["has_correct_date"] and llm_result["has_monthly_repeat"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
        
        # Fallback to traditional check
        key_1 = key_2 = True
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Jun 01")
        if (len(outs) == 0):
            key_1 = False
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Monthly")
        if ((len(outs) == 0)):
            key_2 = False
        return {"judge_page": True, "1": True, "2": key_1, "3": key_2, "complete": key_1 and key_2}

class SingleTask_calendar_LLM_9(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this calendar app screenshot and verify:
1. Is there an event titled "work"?
2. Has the recurrence been set to daily?
Respond in JSON format with keys: {"has_work_title": bool, "has_daily_recurrence": bool}"""

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
                    "1": llm_result["has_work_title"],
                    "2": llm_result["has_daily_recurrence"],
                    "3": True,
                    "complete": llm_result["has_work_title"] and llm_result["has_daily_recurrence"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
        
        # Fallback to traditional check
        key_1 = True
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Daily")
        if (len(outs) == 0):
            key_1 = False
        return {"judge_page": True, "1": True, "2": self.edit_started_correctly, "3": key_1,
                "complete": self.edit_started_correctly and key_1}

class SingleTask_calendar_LLM_10(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this calendar app screenshot and verify:
1. Is there an event titled "this day"?
Respond in JSON format with keys: {"has_this_day_title": bool}"""

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
                    "1": llm_result["has_this_day_title"],
                    "complete": llm_result["has_this_day_title"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
        
        return {"judge_page": True, "1": True, "complete": True}

class SingleTask_calendar_LLM_11(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this calendar app screenshot and verify:
1. Is there an event titled "this day"?
2. Has the recurrence been set to weekly?
Respond in JSON format with keys: {"has_this_day_title": bool, "has_weekly_recurrence": bool}"""

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
                    "1": llm_result["has_this_day_title"],
                    "2": llm_result["has_weekly_recurrence"],
                    "3": True,
                    "complete": llm_result["has_this_day_title"] and llm_result["has_weekly_recurrence"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
        
        # Fallback to traditional check
        self.edit_started_correctly = True
        key_1 = True
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Weekly")
        if (len(outs) == 0):
            key_1 = False
        return {"judge_page": True, "1": True, "2": self.edit_started_correctly, "3": key_1,
                "complete": self.edit_started_correctly and key_1}

class SingleTask_calendar_LLM_12(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this calendar app screenshot and verify:
1. Is there an event titled "Today"?
2. Has the note "Hello" been added to the event?
Respond in JSON format with keys: {"has_today_title": bool, "has_hello_note": bool}"""

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
                    "1": llm_result["has_today_title"],
                    "2": llm_result["has_hello_note"],
                    "3": True,
                    "complete": llm_result["has_today_title"] and llm_result["has_hello_note"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
        
        # Fallback to traditional check
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Weekly")
        if (len(outs) > 0):
            self.edit_started_correctly = True
        else:
            self.edit_started_correctly = False
        key_1 = True
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Hello")
        if (len(outs) == 0):
            key_1 = False
        return {"judge_page": True, "1": True, "2": self.edit_started_correctly, "3": key_1,
                "complete": self.edit_started_correctly and key_1}

class SingleTask_calendar_LLM_13(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this calendar app screenshot and verify:
1. Is there an event titled "exam"?
Respond in JSON format with keys: {"has_exam_title": bool}"""

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
                    "1": llm_result["has_exam_title"],
                    "complete": llm_result["has_exam_title"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
        
        return {"judge_page": True, "1": True, "complete": True}

class SingleTask_calendar_LLM_14(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this calendar app screenshot and verify:
1. Is there an event titled "exam"?
2. Has the event been set as an all-day event?
Respond in JSON format with keys: {"has_exam_title": bool, "is_all_day": bool}"""

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
                    "1": llm_result["has_exam_title"],
                    "2": llm_result["is_all_day"],
                    "3": True,
                    "complete": llm_result["has_exam_title"] and llm_result["is_all_day"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
        
        # Fallback to traditional check
        self.edit_started_correctly = True
        key_1 = True
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Yearly")
        if (len(outs) == 0):
            key_1 = False
        return {"judge_page": True, "1": True, "2": self.edit_started_correctly, "3": key_1,
                "complete": self.edit_started_correctly and key_1}

class SingleTask_calendar_LLM_5(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this calendar app screenshot and verify:
1. Is there an event titled "work"?
2. Has the end time been changed to 7:00 PM?
Respond in JSON format with keys: {"has_work_title": bool, "has_correct_end_time": bool}"""

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
                    "1": llm_result["has_work_title"],
                    "2": llm_result["has_correct_end_time"],
                    "3": True,
                    "complete": llm_result["has_work_title"] and llm_result["has_correct_end_time"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
        
        # Fallback to traditional check
        key_1 = key_2 = True
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Today")
        if (len(outs) == 0):
            key_1 = False
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "7:00 PM")
        if ((len(outs) == 0)):
            key_2 = False
        return {"judge_page": True, "1": True, "2": key_1, "3": key_2, "complete": key_1 and key_2}

class SingleTask_calendar_LLM_6(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this calendar app screenshot and verify:
1. Is there an event titled "homework"?
2. Has the note "classroom 101" been added to the event?
Respond in JSON format with keys: {"has_homework_title": bool, "has_classroom_note": bool}"""

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
                    "1": llm_result["has_homework_title"],
                    "2": llm_result["has_classroom_note"],
                    "3": True,
                    "complete": llm_result["has_homework_title"] and llm_result["has_classroom_note"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
        
        # Fallback to traditional check
        key_1 = True
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "classroom 101")
        if (len(outs) == 0):
            key_1 = False
        return {"judge_page": True, "1": True, "2": self.edit_started_correctly, "3": key_1,
                "complete": self.edit_started_correctly and key_1}

class SingleTask_calendar_LLM_7(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this calendar app screenshot and verify:
1. Is there an event titled "meeting"?
2. Has the notification time been changed to include both 5 minutes and 10 minutes before the event?
Respond in JSON format with keys: {"has_meeting_title": bool, "has_correct_notifications": bool}"""

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
                    "1": llm_result["has_meeting_title"],
                    "2": llm_result["has_correct_notifications"],
                    "3": True,
                    "complete": llm_result["has_meeting_title"] and llm_result["has_correct_notifications"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
        
        # Fallback to traditional check
        key_1 = True
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "30 minutes before")
        if (len(outs) == 0):
            key_1 = False
        return {"judge_page": True, "1": True, "2": self.edit_started_correctly, "3": key_1,
                "complete": self.edit_started_correctly and key_1}

class SingleTask_calendar_LLM_8(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this calendar app screenshot and verify:
1. Is there an event titled "work"?
2. Has the note "computer" been added to the event?
Respond in JSON format with keys: {"has_work_title": bool, "has_computer_note": bool}"""

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
                    "1": llm_result["has_work_title"],
                    "2": llm_result["has_computer_note"],
                    "3": True,
                    "complete": llm_result["has_work_title"] and llm_result["has_computer_note"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
        
        # Fallback to traditional check
        key_1 = True
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "30 minutes before")
        if (len(outs) == 0):
            key_1 = False
        return {"judge_page": True, "1": True, "2": self.edit_started_correctly, "3": key_1,
                "complete": self.edit_started_correctly and key_1}
