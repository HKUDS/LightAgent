from evaluation.task import *
import requests
import json
import base64
import traceback
import os
from typing import Dict, Any
from evaluation.tasks.llm_evaluator import LLMEvaluator


class SingleTask_Contacts_1(SingleTask):

    def judge_page(self, xml_compressed_tree):
        # 判断是否包含 "Contact" 和 "John"
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "Contact"):
            return False
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "John"):
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        outcome = {"judge_page": False, "1": False, "2": False, "complete": False}

        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        outcome["judge_page"] = True

        # 检查 "John"
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "John")
        if outs:
            outcome["1"] = True

        # 检查 "1 (234) 567-8"
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "1 (234) 567-8")
        if outs:
            outcome["2"] = True

        # 判断 complete
        if outcome["1"] and outcome["2"]:
            outcome["complete"] = True

        return outcome


class SingleTask_Contacts_2(SingleTask):

    def judge_page(self, xml_compressed_tree):
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "Contact"):
            return False
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "John Smith"):
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        outcome = {"judge_page": True, "1": False, "2": False, "complete": False}
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "1 (234) 567-8")

        for out in outs:
            for single_out in out.values():
                for key in single_out.keys():
                    key = key.split(";")[-1]
                    if key == "Call Mobile 1 (234) 567-8 ":
                        outcome["1"] = True
                    if key == "Email Work 123456@qq.com ":
                        outcome["2"] = True
                    if outcome["1"] and outcome["2"]:
                        outcome["complete"] = True
                        return outcome

        return outcome


class SingleTask_Contacts_3(SingleTask):

    def judge_page(self, xml_compressed_tree):
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "Contact"):
            return False
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "Xu"):
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        outcome = {"judge_page": True, "1": False, "2": False, "complete": False}
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "1 (234) 567-8")

        for out in outs:
            for single_out in out.values():
                for key in single_out.keys():
                    key = key.split(";")[-1]
                    if key == "Call Work 1 (234) 567-8 ":
                        outcome["1"] = True
                    if key == "Call Mobile (876) 543-21 ":
                        outcome["2"] = True
                    if outcome["1"] and outcome["2"]:
                        outcome["complete"] = True
                        return outcome

        return outcome


class SingleTask_Contacts_4(SingleTask):

    def judge_page(self, xml_compressed_tree):
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "Contact"):
            return False
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "Chen"):
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        outcome = {"judge_page": True, "1": False, "complete": False}
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Contact photo ")

        for out in outs:
            for single_out in out.values():
                for key in single_out.keys():
                    key = key.split(";")[-1]
                    if key == "Tsinghua University ":
                        outcome["1"] = True
                        outcome["complete"] = True
                        return outcome

        return outcome


class SingleTask_Contacts_5(SingleTask):

    def judge_page(self, xml_compressed_tree):
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "work • l"):
            return False
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "Add contacts"):
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        outcome = {"judge_page": True, "1": False, "2": False, "3": False, "complete": False}
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "work • ")

        for out in outs:
            for single_out in out.values():
                for key, value in single_out.items():
                    if "work • " in key:
                        key = key.split(";")[-1]
                        if "contacts" in key and not "3 contacts " in key:
                            return {"judge_page": True, "1": False}
                    try:
                        for it in value.keys():
                            key = it.split(";")[-1]
                            if key == "Chen Chen ":
                                outcome["1"] = True
                            elif key == "Lee Lee ":
                                outcome["2"] = True
                            elif key == "Xu Xu ":
                                outcome["3"] = True
                            if outcome["1"] and outcome["2"] and outcome["3"]:
                                outcome["complete"] = True
                                return outcome
                    except:
                        pass

        return outcome


class SingleTask_Contacts_6(SingleTask):

    def judge_page(self, xml_compressed_tree):
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "Contact"):
            return False
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "ABC"):
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        outcome = {"judge_page": True, "1": False, "complete": False}
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "00112233 ")

        if len(outs) > 0:
            outcome["1"] = True
            outcome["complete"] = True

        return outcome


class SingleTask_Contacts_7(SingleTask):

    def judge_page(self, xml_compressed_tree):
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "Contact"):
            return False
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "ABC"):
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        outcome = {"judge_page": True, "1": False, "complete": False}
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Birthday ")

        for out in outs:
            for single_out in out.values():
                for key in single_out.keys():
                    key = key.split(";")[-1]
                    if key == "October 24, 1996 ":
                        outcome["1"] = True
                        outcome["complete"] = True
                        return outcome

        return outcome


class SingleTask_Contacts_8(SingleTask):

    def judge_page(self, xml_compressed_tree):
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "Contact"):
            return False
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "ABC"):
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        outcome = {"judge_page": True, "1": False, "complete": False}

        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "abc.github.com")
        if len(outs) > 0:
            outcome["1"] = True
            outcome["complete"] = True

        return outcome


class SingleTask_Contacts_9(SingleTask):

    def judge_page(self, xml_compressed_tree):
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "Texting with ABC"):
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        key_1 = False
        key_2 = False
        outcome = {"judge_page": True, "1": False, "2": False, "complete": False}

        if find_subtrees_of_parents_with_key(xml_compressed_tree, "Texting with ABC"):
            key_1 = True
            if find_subtrees_of_parents_with_key(xml_compressed_tree, "Nice to meet you"):
                key_2 = True

        outcome["1"] = key_1
        outcome["2"] = key_2
        outcome["complete"] = key_1 and key_2

        return outcome


class SingleTask_Contacts_10(SingleTask):

    def judge_page(self, xml_compressed_tree):
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "End call"):
            return False
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "ABC"):
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        return {"judge_page": True, "1": True, "complete": True}


class SingleTask_Contacts_11(SingleTask):

    def judge_page(self, xml_compressed_tree):
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "ABC ABC"):
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        judge_key = not find_subtrees_of_parents_with_key(xml_compressed_tree, "AAA AAA ")

        return {"judge_page": True, "1": judge_key, "complete": judge_key}


class SingleTask_Contacts_12(SingleTask):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        answer = "22331144 or (223) 311-44"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_Contacts_13(SingleTask):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        answer = "22334455@gmail.com"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_Contacts_14(SingleTask):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        answer = "April 21, 2000"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_Contacts_15(SingleTask):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        answer = "Tsinghua university"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_Contacts_16(SingleTask):

    def judge_page(self, xml_compressed_tree):
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "Search contacts "):
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Search contacts ")
        if len(outs) == 0:
            return {"judge_page": True, "1": False, "complete": False}

        return {"judge_page": True, "1": True, "complete": True}

class SingleTask_Contacts_LLM_1(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is there a contact named "John" with a mobile phone number "12345678"?
Note: The number may be in the format of "12345678" or "(123) 456-78" or other formats.
Respond in JSON format with keys: {"contact_added": bool, "number_correct": bool}"""

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
                    "1": llm_result["contact_added"] and llm_result["number_correct"],
                    "complete": llm_result["contact_added"] and llm_result["number_correct"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}")
                return {"judge_page": True, "1": False, "complete": False}
        
        return {"judge_page": True, "1": False, "complete": False}

class SingleTask_Contacts_LLM_2(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is there a contact named "John Smith"?
2. Does this contact have a mobile number "12345678" and work email "123456@gmail.com"?
Respond in JSON format with keys: {"contact_added": bool, "details_correct": bool}"""

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
                    "1": llm_result["contact_added"],
                    "2": llm_result["details_correct"],
                    "complete": llm_result["contact_added"] and llm_result["details_correct"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}")
                return {"judge_page": True, "1": False, "2": False, "complete": False}
        
        return {"judge_page": True, "1": False, "2": False, "complete": False}

class SingleTask_Contacts_LLM_3(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is there a contact named "Xu"?
2. Does this contact have a work phone number "12345678" and mobile number "87654321"?
Respond in JSON format with keys: {"contact_added": bool, "numbers_correct": bool}"""

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
                    "1": llm_result["contact_added"],
                    "2": llm_result["numbers_correct"],
                    "complete": llm_result["contact_added"] and llm_result["numbers_correct"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}")
                return {"judge_page": True, "1": False, "2": False, "complete": False}
        
        return {"judge_page": True, "1": False, "2": False, "complete": False}

class SingleTask_Contacts_LLM_4(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is there a contact named "Chen" with company information showing "Tsinghua University"?
Respond in JSON format with keys: {"contact_added": bool, "company_correct": bool}"""

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
                    "1": llm_result["contact_added"] and llm_result["company_correct"],
                    "complete": llm_result["contact_added"] and llm_result["company_correct"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}")
                return {"judge_page": True, "1": False, "complete": False}
        
        return {"judge_page": True, "1": False, "complete": False}

class SingleTask_Contacts_LLM_5(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is there a "work" label created?
2. Are contacts "AAA" and "ABC" added to this work label?
Respond in JSON format with keys: {"label_created": bool, "contacts_added": bool}"""

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
                    "1": llm_result["label_created"],
                    "2": llm_result["contacts_added"],
                    "complete": llm_result["label_created"] and llm_result["contacts_added"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}")
                return {"judge_page": True, "1": False, "2": False, "complete": False}
        
        return {"judge_page": True, "1": False, "2": False, "complete": False}

class SingleTask_Contacts_LLM_6(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Does contact "ABC" have a work phone number "00112233"?
Respond in JSON format with keys: {"number_added": bool}"""

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
                    "1": llm_result["number_added"],
                    "complete": llm_result["number_added"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}")
                return {"judge_page": True, "1": False, "complete": False}
        
        return {"judge_page": True, "1": False, "complete": False}

class SingleTask_Contacts_LLM_7(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is the birthday for contact "AAA" set to "October 24, 1996"?
Respond in JSON format with keys: {"birthday_set": bool}"""

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
                    "1": llm_result["birthday_set"],
                    "complete": llm_result["birthday_set"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}")
                return {"judge_page": True, "1": False, "complete": False}
        
        return {"judge_page": True, "1": False, "complete": False}

class SingleTask_Contacts_LLM_8(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is the website for contact "ABC" set to "abc.github.com"?
Respond in JSON format with keys: {"website_set": bool}"""

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
                    "1": llm_result["website_set"],
                    "complete": llm_result["website_set"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}")
                return {"judge_page": True, "1": False, "complete": False}
        
        return {"judge_page": True, "1": False, "complete": False}

class SingleTask_Contacts_LLM_9(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is there a message draft to "ABC"?
2. Does the message content show "Nice to meet you"?
Respond in JSON format with keys: {"message_drafted": bool, "content_correct": bool}"""

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
                    "1": llm_result["message_drafted"],
                    "2": llm_result["content_correct"],
                    "complete": llm_result["message_drafted"] and llm_result["content_correct"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}")
                return {"judge_page": True, "1": False, "2": False, "complete": False}
        
        return {"judge_page": True, "1": False, "2": False, "complete": False}

class SingleTask_Contacts_LLM_10(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is there an active call screen with contact "ABC"?
Respond in JSON format with keys: {"call_active": bool}"""

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
                    "1": llm_result["call_active"],
                    "complete": llm_result["call_active"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}")
                return {"judge_page": True, "1": False, "complete": False}
        
        return {"judge_page": True, "1": False, "complete": False}

class SingleTask_Contacts_LLM_11(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is contact "AAA" no longer visible in the contacts list?
Respond in JSON format with keys: {"contact_deleted": bool}"""

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
                    "1": llm_result["contact_deleted"],
                    "complete": llm_result["contact_deleted"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}")
                return {"judge_page": True, "1": False, "complete": False}
        
        return {"judge_page": True, "1": False, "complete": False}

class SingleTask_Contacts_LLM_12(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text output and verify:
1. Does the text correctly identify ABC's phone number as "22331144" or "(223) 311-44"?
Respond in JSON format with keys: {"answer_correct": bool}"""

    def judge_page(self, line):
        if line["parsed_action"]["action"] != "finish":
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(line):
            return {"judge_page": False}
        
        try:
            text_output = json.dumps(line["parsed_action"])
            if not text_output:
                return {"judge_page": True, "1": False, "complete": False}
            
            llm_result = self.llm_evaluator.analyze_text(text_output, self.task_prompt)
            
            result = {
                "judge_page": True,
                "1": llm_result["answer_correct"],
                "complete": llm_result["answer_correct"]
            }
            return result
        except Exception as e:
            print(f"LLM analysis failed: {e}")
            return {"judge_page": True, "1": False, "complete": False}

class SingleTask_Contacts_LLM_13(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text output and verify:
1. Does the text correctly identify Li's work email as "22334455@gmail.com"?
Respond in JSON format with keys: {"answer_correct": bool}"""

    def judge_page(self, line):
        if line["parsed_action"]["action"] != "finish":
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(line):
            return {"judge_page": False}
        
        try:
            text_output = json.dumps(line["parsed_action"])
            if not text_output:
                return {"judge_page": True, "1": False, "complete": False}
            
            llm_result = self.llm_evaluator.analyze_text(text_output, self.task_prompt)
            
            result = {
                "judge_page": True,
                "1": llm_result["answer_correct"],
                "complete": llm_result["answer_correct"]
            }
            return result
        except Exception as e:
            print(f"LLM analysis failed: {e}")
            return {"judge_page": True, "1": False, "complete": False}

class SingleTask_Contacts_LLM_14(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text output and verify:
1. Does the text correctly identify ABC's birthday as "April 21, 2000"?
Respond in JSON format with keys: {"answer_correct": bool}"""

    def judge_page(self, line):
        if line["parsed_action"]["action"] != "finish":
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(line):
            return {"judge_page": False}
        
        try:
            text_output = json.dumps(line["parsed_action"])
            if not text_output:
                return {"judge_page": True, "1": False, "complete": False}
            
            llm_result = self.llm_evaluator.analyze_text(text_output, self.task_prompt)
            
            result = {
                "judge_page": True,
                "1": llm_result["answer_correct"],
                "complete": llm_result["answer_correct"]
            }
            return result
        except Exception as e:
            print(f"LLM analysis failed: {e}")
            return {"judge_page": True, "1": False, "complete": False}

class SingleTask_Contacts_LLM_15(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text output and verify:
1. Does the text correctly identify AAA's company as "Tsinghua university"?
Respond in JSON format with keys: {"answer_correct": bool}"""

    def judge_page(self, line):
        if line["parsed_action"]["action"] != "finish":
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(line):
            return {"judge_page": False}
        
        try:
            text_output = json.dumps(line["parsed_action"])
            if not text_output:
                return {"judge_page": True, "1": False, "complete": False}
            
            llm_result = self.llm_evaluator.analyze_text(text_output, self.task_prompt)
            
            result = {
                "judge_page": True,
                "1": llm_result["answer_correct"],
                "complete": llm_result["answer_correct"]
            }
            return result
        except Exception as e:
            print(f"LLM analysis failed: {e}")
            return {"judge_page": True, "1": False, "complete": False}

class SingleTask_Contacts_LLM_16(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is the search contacts interface visible and active?
Respond in JSON format with keys: {"search_active": bool}"""

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
                    "1": llm_result["search_active"],
                    "complete": llm_result["search_active"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}")
                return {"judge_page": True, "1": False, "complete": False}
        
        return {"judge_page": True, "1": False, "complete": False}
