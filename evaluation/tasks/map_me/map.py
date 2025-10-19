from evaluation.task import *
from evaluation.tasks.llm_evaluator import LLMEvaluator
import base64
import requests
import os
import json
import traceback

class SingleTask_Mapme_1(SingleTask):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        answer = "73 km, 12 hr 58 min"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_Mapme_2(SingleTask):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        answer = "7.0 km, 8 min"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_Mapme_3(SingleTask):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        answer = "4 hr 7 min"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_Mapme_4(SingleTask):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        answer = "subway 824 and subway EB"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_Mapme_5(SingleTask):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        answer = "public transportation"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_Mapme_6(SingleTask):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        answer = "public transportation"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_Mapme_7(SingleTask):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        answer = "Teléferic Barcelona"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_Mapme_8(SingleTask):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        answer = "Teléferic Barcelona, about 3min"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_Mapme_9(SingleTask):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        answer = "The Clement Hotel - All Inclusive"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_Mapme_10(SingleTask):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        answer = "9min"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_Mapme_11(SingleTask):

    def judge_page(self, xml_compressed_tree):
        # 判断是否包含 "My places "、"Home" 和 "Work "
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "My places "):
            return False
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "Home"):
            return False
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "Work "):
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        judge_key = False
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Work ")
        for out in outs:
            for single_out in out.values():
                try:
                    for value in single_out.keys():
                        value = value.split(";")[-1]
                        if value == "18th Street, 3180 • 50.6 km ":
                            judge_key = True
                except:
                    pass
        return {"judge_page": True, "1": judge_key, "complete": judge_key}


class SingleTask_Mapme_12(SingleTask):

    def judge_page(self, xml_compressed_tree):
        # 判断是否包含 "Stanford"、"My location" 和 "Start"
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "Stanford"):
            return False
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "My location"):
            return False
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "Start"):
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        return {"judge_page": True, "1": True, "complete": True}


class SingleTask_Mapme_13(SingleTask):

    def judge_page(self, xml_compressed_tree):
        # 判断是否包含 "Stanford"、"My location" 和 "Start"
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "University South"):
            return False
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "My location"):
            return False
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "Start"):
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        return {"judge_page": True, "1": True, "complete": True}


class SingleTask_Mapme_14(SingleTask):

    def judge_page(self, xml_compressed_tree):
        # 判断是否包含 "Stanford"、"My location" 和 "Start"
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "OpenAI"):
            return False
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "My location"):
            return False
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "Start"):
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        return {"judge_page": True, "1": True, "complete": True}


class SingleTask_Mapme_15(SingleTask):

    def judge_page(self, xml_compressed_tree):
        # 判断是否包含 "Stanford"、"My location" 和 "Start"
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "University of California, Berkeley"):
            return False
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "My location"):
            return False
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "Start"):
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        return {"judge_page": True, "1": True, "complete": True}


class SingleTask_Mapme_LLM_1(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text and verify:
1. Is the walking distance and time between Bus Stop of Stanford Campus Oval and Bus Stop of Oxford Street & University Avenue shown as "73 km, 12 hr 58 min"?
Respond in JSON format with keys: {"has_correct_distance_time": bool}"""

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
                    "1": llm_result["has_correct_distance_time"],
                    "complete": llm_result["has_correct_distance_time"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        answer = "73 km, 12 hr 58 min"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome

class SingleTask_Mapme_LLM_2(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text and verify:
1. Is the driving distance and time between Bus stop of 2700 Coast Avenue and Bus Stop Route 51 shown as "7.0 km, 8 min"?
Respond in JSON format with keys: {"has_correct_distance_time": bool}"""

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
                    "1": llm_result["has_correct_distance_time"],
                    "complete": llm_result["has_correct_distance_time"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        answer = "7.0 km, 8 min"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome

class SingleTask_Mapme_LLM_3(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text and verify:
1. Is the riding time between Bus Stop of Stanford Campus Oval and Bus Stop of Oxford Street & University Avenue shown as "4 hr 7 min"?
Respond in JSON format with keys: {"has_correct_time": bool}"""

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
                    "1": llm_result["has_correct_time"],
                    "complete": llm_result["has_correct_time"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        answer = "4 hr 7 min"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome

class SingleTask_Mapme_LLM_4(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text and verify:
1. Are the public transportation routes between Bus stop of 2700 Coast Avenue and Bus Stop Route 51 shown as "subway 824 and subway EB"?
Respond in JSON format with keys: {"has_correct_route": bool}"""

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
                    "1": llm_result["has_correct_route"],
                    "complete": llm_result["has_correct_route"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        answer = "subway 824 and subway EB"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome

class SingleTask_Mapme_LLM_5(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text and verify:
1. Is public transportation shown as the faster option for travel between Bus stop of 2700 Coast Avenue and Bus Stop Route 51?
Respond in JSON format with keys: {"has_correct_comparison": bool}"""

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
                    "1": llm_result["has_correct_comparison"],
                    "complete": llm_result["has_correct_comparison"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        answer = "public transportation"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome

class SingleTask_Mapme_LLM_6(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text and verify:
1. Is public transportation shown as the faster option for travel between Bus Stop of Stanford Campus Oval and Bus Stop of Oxford Street & University Avenue?
Respond in JSON format with keys: {"has_correct_comparison": bool}"""

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
                    "1": llm_result["has_correct_comparison"],
                    "complete": llm_result["has_correct_comparison"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        answer = "public transportation"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome

class SingleTask_Mapme_LLM_7(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text and verify:
1. Is "Teléferic Barcelona" shown as the nearest restaurant?
Respond in JSON format with keys: {"has_correct_restaurant": bool}"""

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
                    "1": llm_result["has_correct_restaurant"],
                    "complete": llm_result["has_correct_restaurant"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        answer = "Teléferic Barcelona"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome

class SingleTask_Mapme_LLM_8(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text and verify:
1. Is "Teléferic Barcelona" shown as the nearest restaurant with a walking time of about 3 minutes?
Respond in JSON format with keys: {"has_correct_restaurant_time": bool}"""

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
                    "1": llm_result["has_correct_restaurant_time"],
                    "complete": llm_result["has_correct_restaurant_time"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        answer = "Teléferic Barcelona, about 3min"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome

class SingleTask_Mapme_LLM_9(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text and verify:
1. Is "The Clement Hotel - All Inclusive" shown as the nearest hotel?
Respond in JSON format with keys: {"has_correct_hotel": bool}"""

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
                    "1": llm_result["has_correct_hotel"],
                    "complete": llm_result["has_correct_hotel"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        answer = "The Clement Hotel - All Inclusive"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome

class SingleTask_Mapme_LLM_10(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text and verify:
1. Is the driving time to the nearest IKEA shown as 9 minutes?
Respond in JSON format with keys: {"has_correct_time": bool}"""

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
                    "1": llm_result["has_correct_time"],
                    "complete": llm_result["has_correct_time"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        answer = "9min"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome

class SingleTask_Mapme_LLM_11(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Has the OpenAI address been successfully added to the Work place in My Places?
Respond in JSON format with keys: {"has_added_work_address": bool}"""

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
                    "1": llm_result["has_added_work_address"],
                    "complete": llm_result["has_added_work_address"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        judge_key = False
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Work ")
        for out in outs:
            for single_out in out.values():
                try:
                    for value in single_out.keys():
                        value = value.split(";")[-1]
                        if value == "18th Street, 3180 • 50.6 km ":
                            judge_key = True
                except:
                    pass
        return {"judge_page": True, "1": judge_key, "complete": judge_key}

class SingleTask_Mapme_LLM_12(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is the navigation route from current location to Stanford University displayed?
Respond in JSON format with keys: {"has_correct_navigation": bool}"""

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
                    "1": llm_result["has_correct_navigation"],
                    "complete": llm_result["has_correct_navigation"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "Stanford"):
            return {"judge_page": False}
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "My location"):
            return {"judge_page": False}
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "Start"):
            return {"judge_page": False}
        return {"judge_page": True, "1": True, "complete": True}

class SingleTask_Mapme_LLM_13(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is the navigation route from current location to University South displayed?
Respond in JSON format with keys: {"has_correct_navigation": bool}"""

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
                    "1": llm_result["has_correct_navigation"],
                    "complete": llm_result["has_correct_navigation"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "University South"):
            return {"judge_page": False}
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "My location"):
            return {"judge_page": False}
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "Start"):
            return {"judge_page": False}
        return {"judge_page": True, "1": True, "complete": True}

class SingleTask_Mapme_LLM_14(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is the navigation route from current location to OpenAI displayed?
Respond in JSON format with keys: {"has_correct_navigation": bool}"""

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
                    "1": llm_result["has_correct_navigation"],
                    "complete": llm_result["has_correct_navigation"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "OpenAI"):
            return {"judge_page": False}
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "My location"):
            return {"judge_page": False}
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "Start"):
            return {"judge_page": False}
        return {"judge_page": True, "1": True, "complete": True}

class SingleTask_Mapme_LLM_15(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is the navigation route from current location to University of California, Berkeley displayed?
Respond in JSON format with keys: {"has_correct_navigation": bool}"""

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
                    "1": llm_result["has_correct_navigation"],
                    "complete": llm_result["has_correct_navigation"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "University of California, Berkeley"):
            return {"judge_page": False}
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "My location"):
            return {"judge_page": False}
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "Start"):
            return {"judge_page": False}
        return {"judge_page": True, "1": True, "complete": True}
