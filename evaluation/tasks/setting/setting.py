from evaluation.task import *
from evaluation.tasks.llm_evaluator import LLMEvaluator
import base64
import requests
import os
import json
import traceback

class SingleTask_Setting_0(SingleTask):

    def judge(self, xml_compressed_tree, line):
        if "command" not in line:
            return {"judge_page": False}
        command = line["command"]
        if command["adb shell settings get global airplane_mode_on"] == "0":
            return {"judge_page": True, "1": False, "complete": False}
        else:
            return {"judge_page": True, "1": True, "complete": True}


class SingleTask_Setting_1(SingleTask):

    def judge_page(self, xml_compressed_tree):
        # 判断是否包含 "Turn on Wi‑Fi automatically"
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Turn on Wi‑Fi automatically")
        if len(outs) == 0:
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Turn on Wi‑Fi automatically")
        for out in outs:
            for key, value in out.items():
                for judge_key, _ in value.items():
                    if "unchecked" in judge_key:
                        return {"judge_page": True, "1": True, "complete": True}
        return {"judge_page": True, "1": False, "complete": False}


class SingleTask_Setting_2(SingleTask):

    def judge_page(self, xml_compressed_tree):
        # 判断是否包含 "Private DNS provider hostname"
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Private DNS provider hostname")
        if len(outs) == 0:
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "dns.google")
        if len(outs) == 0:
            return {"judge_page": True, "1": False, "complete": False}
        else:
            return {"judge_page": True, "1": True, "complete": True}


class SingleTask_Setting_3(SingleTask):

    def judge(self, xml_compressed_tree, line):
        if "command" not in line:
            return {"judge_page": False}
        command = line["command"]
        if command["adb shell settings get global bluetooth_on"] == "1":
            return {"judge_page": True, "1": False, "complete": False}
        else:
            return {"judge_page": True, "1": True, "complete": True}


class SingleTask_Setting_4(SingleTask):

    def judge_page(self, xml_compressed_tree):
        # 判断是否包含 "Pair new device"
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Pair new device")
        if len(outs) == 0:
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "my AVD")
        if len(outs) == 0:
            return {"judge_page": True, "1": False, "complete": False}
        else:
            return {"judge_page": True, "1": True, "complete": True}


class SingleTask_Setting_5(SingleTask):

    def judge_page(self, xml_compressed_tree):
        # 判断是否包含 "Battery percentage"
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Battery percentage")
        if len(outs) == 0:
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Battery percentage")
        for out in outs:
            for key, value in out.items():
                for judge_key, _ in value.items():
                    if "unchecked" in judge_key:
                        return {"judge_page": True, "1": False, "complete": False}
        return {"judge_page": True, "1": True, "complete": True}


class SingleTask_Setting_6(SingleTask):

    def judge_page(self, xml_compressed_tree):
        # 判断是否包含 "Apps"
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Apps")
        if len(outs) == 0:
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Apps")
        for out in outs:
            for key, value in out.items():
                for storage, _ in value.items():
                    if "MB" in storage or "GB" in storage:
                        if ";" in storage:
                            storage = storage.split(";")[-1]
                        return {"judge_page": True, "1": storage}
        return {"judge_page": False}


class SingleTask_Setting_7(SingleTask):

    def judge_page(self, xml_compressed_tree):
        # 判断是否包含 "Display "
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Display ")
        if len(outs) == 0:
            return False
        return True

    def setting_ch(self, xml_compressed_tree):
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Dark theme ")
        found = False
        finish = False
        for out in outs:
            out = out.values()
            for single_out in out:
                for key, value in single_out.items():
                    if "RecyclerView" in key:
                        found = True
                        item = find_subtrees_of_parents_with_key(xml_compressed_tree, "Use Dark theme ")
                        for it in item:
                            it = it.values()
                            for single_it_ in it:
                                for key_, value_ in single_it_.items():
                                    if not "unchecked" in key_:
                                        if "checked" in key_:
                                            finish = True
                                            break
                        break
        if found:
            return {"judge_page": True, "1": finish, "complete": finish}
        else:
            return {"judge_page": False}

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Display ")
        found = False
        finish = False
        for out in outs:
            out = out.values()
            for single_out in out:
                for key, value in single_out.items():
                    if "RecyclerView" in key:
                        found = True
                        item = find_subtrees_of_parents_with_key(xml_compressed_tree, "Dark theme ")
                        for it in item:
                            it = it.values()
                            for single_it_ in it:
                                for key_, value_ in single_it_.items():
                                    if not "unchecked" in key_:
                                        if "checked" in key_ and "Dark theme" in key_:
                                            finish = True
                                            break
                        break
        if found:
            return {"judge_page": True, "1": finish, "complete": finish}
        else:
            return self.setting_ch(xml_compressed_tree)


class SingleTask_Setting_8(SingleTask):

    def judge_page(self, xml_compressed_tree):
        # 判断是否包含 "Brightness level "
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Brightness level ")
        if len(outs) == 0:
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Brightness level ")
        finish = False
        for out in outs:
            out = out.values()
            for single_out in out:
                for key, value in single_out.items():
                    if "%" in key:
                        key = key.split(";")[-1].rstrip()
                        break
        if key == "0%":
            return {"judge_page": True, "1": True, "complete": True}
        else:
            return {"judge_page": True, "1": False, "complete": False}


class SingleTask_Setting_9(SingleTask):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        if "command" not in line:
            return {"judge_page": False}
        command = line["command"]
        if "0" in command["adb shell settings list system | grep volume_ring_speaker"]:
            return {"judge_page": True, "1": True, "complete": True}
        else:
            return {"judge_page": True, "1": False, "complete": False}


class SingleTask_Setting_10(SingleTask):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        if "command" not in line:
            return {"judge_page": False}
        command = line["command"]
        if "7" in command["adb shell settings list system | grep volume_alarm_speaker"]:
            return {"judge_page": True, "1": True, "complete": True}
        else:
            return {"judge_page": True, "1": False, "complete": False}


class SingleTask_Setting_11(SingleTask):

    def judge_page(self, xml_compressed_tree):
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "Text-to-speech output"):
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Chinese")
        if len(outs) > 0:
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_Setting_12(SingleTask):

    def judge_page(self, xml_compressed_tree):
        if not find_subtrees_of_parents_with_key(xml_compressed_tree, "Set time automatically"):
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "May 1, 2024")
        if len(outs) > 0:
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_Setting_13(SingleTask):

    def judge_page(self, xml_compressed_tree):
        # 判断是否包含 "Ring vibration "
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Ring vibration ")
        if len(outs) == 0:
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        finish = {"judge_page": True, "1": False, "complete": False}
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Ring vibration ")
        for out in outs:
            out = out.values()
            for single_out in out:
                for key, value in single_out.items():
                    if "unchecked" in key:
                        finish = {"judge_page": True, "1": True, "complete": True}
                        break
        return finish


class SingleTask_Setting_14(SingleTask):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        if "command" not in line:
            return {"judge_page": False}
        command = line["command"]
        timezone = command["adb shell 'getprop persist.sys.timezone'"]
        if line["parsed_action"]["action"] != "finish":
            return {"judge_page": False}
        try:
            self.final_ground_truth = timezone
            if self.check_answer(line):
                return {"judge_page": True, "1": True, "complete": True}
            else:
                return {"judge_page": True, "1": False, "complete": False}
        except:
            return {"judge_page": True, "1": False, "complete": False}


class SingleTask_Setting_15(SingleTask):

    def judge_page(self, xml_compressed_tree):
        # 判断是否包含 "Add a language"
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Add a language")
        if len(outs) == 0:
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Español (Estados Unidos)")
        if len(outs) == 0:
            return {"judge_page": True, "1": False, "complete": False}
        for out in outs:
            for key, value in out.items():
                for idx, judge_key in enumerate(value.keys()):
                    if "Español (Estados Unidos)" in judge_key:
                        if "2" in list(value.keys())[idx + 1]:
                            return {"judge_page": True, "1": True, "2": True, "complete": True}
                        else:
                            return {"judge_page": True, "1": True, "2": False, "complete": False}


class SingleTask_Setting_16(SingleTask):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        if line["parsed_action"]["action"] != "finish":
            return {"judge_page": False}
        try:
            self.final_ground_truth = "English (United States)"
            if self.check_answer(line):
                return {"judge_page": True, "1": True, "complete": True}
            else:
                return {"judge_page": True, "1": False, "complete": False}
        except:
            return {"judge_page": True, "1": False, "complete": False}


class SingleTask_Setting_17(SingleTask):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        if "command" not in line:
            return {"judge_page": False}
        command = line["command"]
        answer = command["adb shell getprop ro.build.version.release"]
        if line["parsed_action"]["action"] != "finish":
            return {"judge_page": False}
        try:
            self.final_ground_truth = answer
            if self.check_answer(line):
                return {"judge_page": True, "1": True, "complete": True}
            else:
                return {"judge_page": True, "1": False, "complete": False}
        except:
            return {"judge_page": True, "1": False, "complete": False}


class SingleTask_Setting_18(SingleTask):

    def judge_page(self, xml_compressed_tree):
        # 判断是否包含 "Allowed"
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Allowed")
        if len(outs) == 0:
            return False
        return True

    def setting_18_ch(self, xml_compressed_tree):
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Allow notification access")
        found = 0
        finish = False
        for out in outs:
            out = out.values()
            for single_out in out:
                for key, value in single_out.items():
                    if found == 1:
                        if not ("unchecked" in key):
                            if "checked" in key:
                                finish = True
                                break
                    if found >= 1:
                        found += 1
                    if "Allow notification access" in key:
                        found += 1
        if found >= 1:
            if finish:
                return {"judge_page": True, "1": False, "complete": False}
            else:
                return {"judge_page": True, "1": True, "complete": True}
        else:
            return {"judge_page": False}

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return self.setting_18_ch(xml_compressed_tree)
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Allowed")
        found_item = False
        found = False
        finish = False
        for out in outs:
            out = out.values()
            for single_out in out:
                for key, value in single_out.items():
                    if found_item:
                        try:
                            for _key in value.keys():
                                if "Contacts" in _key:
                                    finish = True
                                    break
                        except AttributeError:
                            pass
                    if "Allowed" in key:
                        found_item = True
                    if "Not allowed" in key:
                        found_item = False
        if finish:
            return {"judge_page": True, "1": False, "complete": False}
        else:
            return {"judge_page": True, "1": True, "complete": True}


class SingleTask_Setting_19(SingleTask):

    def judge_page(self, xml_compressed_tree):
        # 判断是否包含 "Default browser app" 和 "Firefox"
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Default browser app")
        if len(outs) == 0:
            return False
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Firefox")
        if len(outs) == 0:
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Default browser app")
        for out in outs:
            for key, value in out.items():
                for judge_key, _ in value.items():
                    if "unchecked" in judge_key:
                        return {"judge_page": True, "1": False, "complete": False}
        return {"judge_page": True, "1": True, "complete": True}


class SingleTask_Setting_20(SingleTask):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        if "command" not in line:
            return {"judge_page": False}
        command = line["command"]
        if "booking" in command["adb shell pm list packages | grep 'com.booking'"]:
            return {"judge_page": True, "1": False, "complete": False}
        else:
            return {"judge_page": True, "1": True, "complete": True}


class SingleTask_Setting_21(SingleTask):

    def judge_page(self, xml_compressed_tree):
        # 判断是否包含 "Settings " 和 "Search settings"
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Settings ")
        outs1 = find_subtrees_of_parents_with_key(xml_compressed_tree, "Search settings")
        if len(outs) == 0 or len(outs1) == 0:
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        return {"judge_page": True, "1": True, "complete": True}


class SingleTask_Setting_22(SingleTask):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        if "command" not in line:
            return {"judge_page": False}
        command = line["command"]
        answer = command["adb shell settings get global airplane_mode_on"]
        if answer == "1":
            answer = "open"
        else:
            answer = "not open"
        if line["parsed_action"]["action"] != "finish":
            return {"judge_page": False}
        try:
            self.final_ground_truth = answer
            if self.check_answer(line):
                return {"judge_page": True, "1": True, "complete": True}
            else:
                return {"judge_page": True, "1": False, "complete": False}
        except:
            return {"judge_page": True, "1": False, "complete": False}

class SingleTask_Setting_LLM_0(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is the airplane mode turned on/activated?
Look for airplane mode icon in the status bar or settings.
Respond in JSON format with keys: {"airplane_mode_on": bool}"""

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
                    "1": llm_result["airplane_mode_on"],
                    "complete": llm_result["airplane_mode_on"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
            
        return {"judge_page": True, "1": False, "complete": False}

class SingleTask_Setting_LLM_5(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is the battery percentage indicator enabled in the status bar?
Respond in JSON format with keys: {"battery_percentage_enabled": bool}"""

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
                    "1": llm_result["battery_percentage_enabled"],
                    "complete": llm_result["battery_percentage_enabled"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Battery percentage")
        for out in outs:
            for key, value in out.items():
                for judge_key, _ in value.items():
                    if "unchecked" in judge_key:
                        return {"judge_page": True, "1": False, "complete": False}
        return {"judge_page": True, "1": True, "complete": True}

class SingleTask_Setting_LLM_7(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is the Dark theme enabled/turned on?
Respond in JSON format with keys: {"dark_theme_enabled": bool}"""

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
                    "1": llm_result["dark_theme_enabled"],
                    "complete": llm_result["dark_theme_enabled"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Dark theme ")
        found = False
        finish = False
        for out in outs:
            out = out.values()
            for single_out in out:
                for key, value in single_out.items():
                    if "RecyclerView" in key:
                        found = True
                        item = find_subtrees_of_parents_with_key(xml_compressed_tree, "Use Dark theme ")
                        for it in item:
                            it = it.values()
                            for single_it_ in it:
                                for key_, value_ in single_it_.items():
                                    if not "unchecked" in key_:
                                        if "checked" in key_:
                                            finish = True
                                            break
                        break
        if found:
            return {"judge_page": True, "1": finish, "complete": finish}
        else:
            return {"judge_page": False}

class SingleTask_Setting_LLM_14(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text output and verify:
1. Does the text correctly identify the timezone?
Respond in JSON format with keys: {"timezone_identified": bool}"""

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
                "1": llm_result["timezone_identified"],
                "complete": llm_result["timezone_identified"]
            }
            return result
        except Exception as e:
            print(f"LLM analysis failed: {e}")
            return {"judge_page": True, "1": False, "complete": False}

class SingleTask_Setting_LLM_18(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Are the Contacts app notifications disabled/not allowed?
Respond in JSON format with keys: {"contacts_notifications_disabled": bool}"""

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
                    "1": llm_result["contacts_notifications_disabled"],
                    "complete": llm_result["contacts_notifications_disabled"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Allowed")
        found_item = False
        found = False
        finish = False
        for out in outs:
            out = out.values()
            for single_out in out:
                for key, value in single_out.items():
                    if found_item:
                        try:
                            for _key in value.keys():
                                if "Contacts" in _key:
                                    finish = True
                                    break
                        except AttributeError:
                            pass
                    if "Allowed" in key:
                        found_item = True
                    if "Not allowed" in key:
                        found_item = False
        if finish:
            return {"judge_page": True, "1": False, "complete": False}
        else:
            return {"judge_page": True, "1": True, "complete": True}

class SingleTask_Setting_LLM_1(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is the "Turn on Wi‑Fi automatically" option disabled/unchecked?
Respond in JSON format with keys: {"wifi_auto_disabled": bool}"""

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
                    "1": llm_result["wifi_auto_disabled"],
                    "complete": llm_result["wifi_auto_disabled"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Turn on Wi‑Fi automatically")
        for out in outs:
            for key, value in out.items():
                for judge_key, _ in value.items():
                    if "unchecked" in judge_key:
                        return {"judge_page": True, "1": True, "complete": True}
        return {"judge_page": True, "1": False, "complete": False}

class SingleTask_Setting_LLM_2(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is the Private DNS provider hostname set to "dns.google"?
Respond in JSON format with keys: {"dns_google_set": bool}"""

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
                    "1": llm_result["dns_google_set"],
                    "complete": llm_result["dns_google_set"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "dns.google")
        if len(outs) == 0:
            return {"judge_page": True, "1": False, "complete": False}
        else:
            return {"judge_page": True, "1": True, "complete": True}

class SingleTask_Setting_LLM_3(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is Bluetooth turned off/disabled?
Look for Bluetooth settings or status indicators showing it's off.
Respond in JSON format with keys: {"bluetooth_off": bool}"""

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
                    "1": llm_result["bluetooth_off"],
                    "complete": llm_result["bluetooth_off"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        if "command" not in line:
            return {"judge_page": True, "1": False, "complete": False}
        command = line["command"]
        if command["adb shell settings get global bluetooth_on"] == "1":
            return {"judge_page": True, "1": False, "complete": False}
        else:
            return {"judge_page": True, "1": True, "complete": True}

class SingleTask_Setting_LLM_4(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is the Bluetooth device name set to "my AVD"?
Respond in JSON format with keys: {"device_name_set": bool}"""

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
                    "1": llm_result["device_name_set"],
                    "complete": llm_result["device_name_set"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "my AVD")
        if len(outs) == 0:
            return {"judge_page": True, "1": False, "complete": False}
        else:
            return {"judge_page": True, "1": True, "complete": True}

class SingleTask_Setting_LLM_6(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is the storage usage for Apps displayed and visible?
Respond in JSON format with keys: {"storage_info_visible": bool}"""

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
                    "1": llm_result["storage_info_visible"],
                    "complete": llm_result["storage_info_visible"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Apps")
        for out in outs:
            for key, value in out.items():
                for storage, _ in value.items():
                    if "MB" in storage or "GB" in storage:
                        if ";" in storage:
                            storage = storage.split(";")[-1]
                        return {"judge_page": True, "1": storage}
        return {"judge_page": False}

class SingleTask_Setting_LLM_8(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is the brightness level set to 0%?
Respond in JSON format with keys: {"brightness_zero": bool}"""

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
                    "1": llm_result["brightness_zero"],
                    "complete": llm_result["brightness_zero"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Brightness level ")
        for out in outs:
            out = out.values()
            for single_out in out:
                for key, value in single_out.items():
                    if "%" in key:
                        key = key.split(";")[-1].rstrip()
                        break
        if key == "0%":
            return {"judge_page": True, "1": True, "complete": True}
        else:
            return {"judge_page": True, "1": False, "complete": False}

class SingleTask_Setting_LLM_9(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text output and verify:
1. Is the Ring & notification volume set to 0?
Respond in JSON format with keys: {"ring_volume_zero": bool}"""

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
                "1": llm_result["ring_volume_zero"],
                "complete": llm_result["ring_volume_zero"]
            }
            return result
        except Exception as e:
            print(f"LLM analysis failed: {e}")
            return {"judge_page": True, "1": False, "complete": False}

class SingleTask_Setting_LLM_10(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text output and verify:
1. Is the alarm volume set to maximum (7)?
Respond in JSON format with keys: {"alarm_volume_max": bool}"""

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
                "1": llm_result["alarm_volume_max"],
                "complete": llm_result["alarm_volume_max"]
            }
            return result
        except Exception as e:
            print(f"LLM analysis failed: {e}")
            return {"judge_page": True, "1": False, "complete": False}

class SingleTask_Setting_LLM_11(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is Chinese selected as the text-to-speech language?
Respond in JSON format with keys: {"chinese_tts_selected": bool}"""

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
                    "1": llm_result["chinese_tts_selected"],
                    "complete": llm_result["chinese_tts_selected"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Chinese")
        if len(outs) > 0:
            return {"judge_page": True, "1": True, "complete": True}
        else:
            return {"judge_page": True, "1": False, "complete": False}

class SingleTask_Setting_LLM_12(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is the date set to May 1, 2024?
Respond in JSON format with keys: {"date_set_correctly": bool}"""

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
                    "1": llm_result["date_set_correctly"],
                    "complete": llm_result["date_set_correctly"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "May 1, 2024")
        if len(outs) > 0:
            return {"judge_page": True, "1": True, "complete": True}
        else:
            return {"judge_page": True, "1": False, "complete": False}

class SingleTask_Setting_LLM_13(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is Ring vibration turned off/disabled?
Respond in JSON format with keys: {"ring_vibration_off": bool}"""

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
                    "1": llm_result["ring_vibration_off"],
                    "complete": llm_result["ring_vibration_off"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        finish = {"judge_page": True, "1": False, "complete": False}
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Ring vibration ")
        for out in outs:
            out = out.values()
            for single_out in out:
                for key, value in single_out.items():
                    if "unchecked" in key:
                        finish = {"judge_page": True, "1": True, "complete": True}
                        break
        return finish

class SingleTask_Setting_LLM_15(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is "Español (Estados Unidos)" added to the language list?
2. Is it set as the second favorite language?
Respond in JSON format with keys: {"spanish_added": bool, "spanish_second": bool}"""

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
                    "1": llm_result["spanish_added"],
                    "2": llm_result["spanish_second"],
                    "complete": llm_result["spanish_added"] and llm_result["spanish_second"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Español (Estados Unidos)")
        if len(outs) == 0:
            return {"judge_page": True, "1": False, "complete": False}
        for out in outs:
            for key, value in out.items():
                for idx, judge_key in enumerate(value.keys()):
                    if "Español (Estados Unidos)" in judge_key:
                        if "2" in list(value.keys())[idx + 1]:
                            return {"judge_page": True, "1": True, "2": True, "complete": True}
                        else:
                            return {"judge_page": True, "1": True, "2": False, "complete": False}

class SingleTask_Setting_LLM_16(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text output and verify:
1. Is "English (United States)" identified as the primary language?
Respond in JSON format with keys: {"english_us_primary": bool}"""

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
                "1": llm_result["english_us_primary"],
                "complete": llm_result["english_us_primary"]
            }
            return result
        except Exception as e:
            print(f"LLM analysis failed: {e}")
            return {"judge_page": True, "1": False, "complete": False}

class SingleTask_Setting_LLM_17(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text output and verify:
1. Is the Android version correctly identified?
Respond in JSON format with keys: {"version_identified": bool}"""

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
                "1": llm_result["version_identified"],
                "complete": llm_result["version_identified"]
            }
            return result
        except Exception as e:
            print(f"LLM analysis failed: {e}")
            return {"judge_page": True, "1": False, "complete": False}

class SingleTask_Setting_LLM_19(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is Firefox set as the default browser app?
Respond in JSON format with keys: {"firefox_default": bool}"""

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
                    "1": llm_result["firefox_default"],
                    "complete": llm_result["firefox_default"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Default browser app")
        for out in outs:
            for key, value in out.items():
                for judge_key, _ in value.items():
                    if "unchecked" in judge_key:
                        return {"judge_page": True, "1": False, "complete": False}
        return {"judge_page": True, "1": True, "complete": True}

class SingleTask_Setting_LLM_20(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text output and verify:
1. Is the booking app uninstalled (not present in package list)?
Respond in JSON format with keys: {"booking_uninstalled": bool}"""

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
                "1": llm_result["booking_uninstalled"],
                "complete": llm_result["booking_uninstalled"]
            }
            return result
        except Exception as e:
            print(f"LLM analysis failed: {e}")
            return {"judge_page": True, "1": False, "complete": False}

class SingleTask_Setting_LLM_21(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is the Settings app open and visible?
2. Is the search settings option available?
Respond in JSON format with keys: {"settings_open": bool, "search_available": bool}"""

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
                    "1": llm_result["settings_open"] and llm_result["search_available"],
                    "complete": llm_result["settings_open"] and llm_result["search_available"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Settings ")
        outs1 = find_subtrees_of_parents_with_key(xml_compressed_tree, "Search settings")
        if len(outs) == 0 or len(outs1) == 0:
            return {"judge_page": False}
        return {"judge_page": True, "1": True, "complete": True}

class SingleTask_Setting_LLM_22(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text output and verify:
1. Is the airplane mode status correctly identified (open=1, not open=0)?
Respond in JSON format with keys: {"status_identified": bool}"""

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
                "1": llm_result["status_identified"],
                "complete": llm_result["status_identified"]
            }
            return result
        except Exception as e:
            print(f"LLM analysis failed: {e}")
            return {"judge_page": True, "1": False, "complete": False}
