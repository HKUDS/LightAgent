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

def extract_alarms(data):
    def clock_end(key, Collapse=False):
        if not Collapse:
            if "Switch" in key and "checked" in key:
                return True
            return False
        else:
            if "Delete" in key or "Add alarm" in key:
                return True
            return False

    def extract_text_from_key(key):
        # 分割字符串，获取最后的实际文本内容
        parts = key.split(';;')
        if len(parts) > 1:
            return parts[-1].strip()
        return key

    def process_elements(elements):
        alarms = []
        alarm = {}
        alarm["days"] = []
        Collapse = False
        
        for key, element in elements.items():
            if isinstance(element, str):
                continue
                
            # 如果是CardView且包含闹钟信息，递归处理其子元素
            if "CardView" in key and "PM" in key or "AM" in key:
                sub_alarm = process_elements(element)
                if sub_alarm:
                    alarms.extend(sub_alarm)
                continue
                
            text = extract_text_from_key(key)
            
            if "Collapse" in key:
                Collapse = True
                alarm["Expand"] = True
                
            if clock_end(key, Collapse):
                if "unchecked" in key:
                    alarm["status"] = "unchecked"
                else:
                    alarm["status"] = "checked"
                if alarm:  # 只有当alarm不为空时才添加
                    alarms.append(alarm.copy())
                alarm = {"days": []}
                Collapse = False
                
            if "AM" in text or "PM" in text:
                # 提取时间，保留AM/PM信息
                words = text.split()
                if len(words) >= 2:
                    time = words[0]
                    meridiem = "AM" if "AM" in text else "PM"
                    alarm["time"] = f"{time}\u200a{meridiem}"  # 使用与原始格式相同的Unicode空格
                else:
                    alarm["time"] = text  # 如果格式不符合预期，保留原始文本
                
            if "Label" in key:
                label_text = extract_text_from_key(key)
                if "Label" in label_text:
                    label_text = label_text.split("Label")[-1].strip()
                alarm["label"] = label_text
                
            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun", "Not scheduled", "Today", "Tomorrow", "Every day"]
            for day in days:
                if day in text and "TextView" in key:
                    alarm["days"].append(day)
                    
            if "Ringtone" in key:
                alarm["ringtone"] = extract_text_from_key(key)
                
            if "Vibrate" in key:
                if "unchecked" in key:
                    alarm["vibrate"] = "unchecked"
                else:
                    alarm["vibrate"] = "checked"
        
        # 如果最后一个alarm没有被添加（没有遇到结束标记），且包含有效信息，则添加它
        if alarm and ("time" in alarm or "label" in alarm):
            alarms.append(alarm)
            
        return alarms

    # 获取根元素下的所有元素
    root_elements = list(data.values())[0]
    return process_elements(root_elements)


class SingleTask_Clock_General(SingleTask):
    def split_string(self, str, splitter):
        str = str.split(";")
        for substr in str:
            if splitter in substr:
                return substr.split(splitter)[0].rstrip()


class SingleTask_Clock_1(SingleTask_Clock_General):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        # print("sdsdsdsdsdsds")
        # print(xml_compressed_tree)
        # print("sdsdsdsdsdsds-----")

        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Alarm")
        outcome = {"judge_page": True, "1": False, "2": False, "3": False, "complete": False}

        # print(xml_compressed_tree)
        # print(outs)
        # print("--------------------------------")
        # print(outs)

        for out in outs:
            alarms_data = extract_alarms(out)
            # print(alarms_data)
            for alarm in alarms_data:
                try:
                    if '3:00\u200aPM' in alarm['time']:
                        outcome["1"] = True
                        try:
                            # 直接比较label值，因为extract_alarms已经处理好了
                            if alarm['label'] == 'meeting':
                                outcome["2"] = True
                        except KeyError:
                            pass
                        try:
                            if alarm['status'] == 'checked':
                                outcome["3"] = True
                        except KeyError:
                            pass
                        try:
                            if alarm['status'] == 'checked' and alarm['label'] == 'meeting' and '3:00\u200aPM' in \
                                    alarm['time']:
                                outcome["complete"] = True
                        except KeyError:
                            pass
                except KeyError:
                    pass
        return outcome


class SingleTask_Clock_2(SingleTask_Clock_General):

    def judge_page(self, xml_compressed_tree):
        # 可以根据需要在这里实现特定的页面判断逻辑
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Alarm")
        outcome = {"judge_page": True, "1": False, "2": False, "3": False, "4": False, "complete": False}

        for out in outs:
            alarms_data = extract_alarms(out)
            # print(alarms_data)
            for alarm in alarms_data:
                try:
                    if '6:45\u200aAM' in alarm['time']:
                        outcome["1"] = True
                        try:
                            if alarm['vibrate'] == 'unchecked':
                                outcome["2"] = True
                        except KeyError:
                            pass
                        try:
                            # if self.split_string(alarm["ringtone"], "Ringtone") == 'Argon':
                            if alarm["ringtone"] == 'Argon':
                                outcome["3"] = True
                        except KeyError:
                            pass
                        try:
                            if alarm['status'] == 'checked':
                                outcome["4"] = True
                        except KeyError:
                            pass
                        try:
                            # if alarm['status'] == 'checked' and self.split_string(alarm["ringtone"],
                            #                                                       "Ringtone") == 'Argon' and \
                            if alarm['status'] == 'checked' and alarm["ringtone"] == 'Argon' and \
                                    alarm['vibrate'] == 'unchecked' and '6:45\u200aAM' in alarm['time']:
                                outcome["complete"] = True
                        except KeyError:
                            pass
                except KeyError:
                    pass

        return outcome


class SingleTask_Clock_3(SingleTask_Clock_General):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Alarm")
        outcome = {"judge_page": True, "1": False, "2": False, "3": False, "complete": False}

        for out in outs:
            alarms_data = extract_alarms(out)
            # print(alarms_data)
            for alarm in alarms_data:
                try:
                    if '7:00\u200aAM' in alarm['time']:
                        outcome["1"] = True
                        try:
                            if alarm['days'] == ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']:
                                outcome["2"] = True
                        except KeyError:
                            pass
                        try:
                            if alarm['status'] == 'checked':
                                outcome["3"] = True
                        except KeyError:
                            pass
                        try:
                            if alarm['status'] == 'checked' and alarm['days'] == ['Mon', 'Tue', 'Wed', 'Thu',
                                                                                  'Fri'] and '7:00\u200aAM' in alarm[
                                'time']:
                                outcome["complete"] = True
                        except KeyError:
                            pass
                except KeyError:
                    pass

        return outcome


class SingleTask_Clock_4(SingleTask_Clock_General):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Alarm")
        outcome = {"judge_page": True, "1": False, "2": False, "3": False, "complete": False}

        for out in outs:
            alarms_data = extract_alarms(out)
            # print(alarms_data)
            for alarm in alarms_data:
                try:
                    if '9:00\u200aAM' in alarm['time']:
                        outcome["1"] = True
                        try:
                            if alarm['days'] == ['Every day']:
                                outcome["2"] = True
                        except KeyError:
                            pass
                        try:
                            if alarm['status'] == 'checked':
                                outcome["3"] = True
                        except KeyError:
                            pass
                        try:
                            if '9:00\u200aAM' in alarm['time'] and alarm['days'] == ['Every day'] and alarm[
                                'status'] == 'checked':
                                outcome["complete"] = True
                        except KeyError:
                            pass
                except KeyError:
                    pass

        return outcome


class SingleTask_Clock_5(SingleTask_Clock_General):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Alarm")
        outcome = {"judge_page": True, "1": False, "2": False, "3": False, "complete": False}

        for out in outs:
            alarms_data = extract_alarms(out)
            # print(alarms_data)
            for alarm in alarms_data:
                try:
                    if '10:30\u200aAM' in alarm['time']:
                        outcome["1"] = True
                        try:
                            if alarm['days'] == ['Tomorrow']:
                                outcome["2"] = True
                        except KeyError:
                            pass
                        try:
                            if alarm['status'] == 'checked':
                                outcome["3"] = True
                        except KeyError:
                            pass
                        try:
                            if '10:30\u200aAM' in alarm['time'] and alarm['days'] == ['Tomorrow'] and alarm[
                                'status'] == 'checked':
                                outcome["complete"] = True
                        except KeyError:
                            pass
                except KeyError:
                    pass

        return outcome


class SingleTask_Clock_6(SingleTask_Clock_General):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Alarm")
        outcome = {"judge_page": True, "1": False, "2": False, "3": False, "4": False, "complete": False}

        for out in outs:
            alarms_data = extract_alarms(out)
            # print(alarms_data)
            for alarm in alarms_data:
                try:
                    if '10:30\u200aPM' in alarm['time']:
                        outcome["1"] = True
                        try:
                            if alarm['days'] == ['Sat', 'Sun']:
                                outcome["2"] = True
                        except KeyError:
                            pass
                        try:
                            # if self.split_string(alarm['label'], 'Label') == 'Watch Football Games':
                            if alarm['label'] == 'Watch Football Games':
                                outcome["3"] = True
                        except KeyError:
                            pass
                        try:
                            if alarm['status'] == 'checked':
                                outcome["4"] = True
                        except KeyError:
                            pass
                        try:
                            # if alarm['status'] == 'checked' and self.split_string(alarm['label'],
                            #                                                       'Label') == 'Watch Football Games' and \
                            if alarm['status'] == 'checked' and alarm['label'] == 'Watch Football Games' and \
                                    alarm['days'] == ['Sat', 'Sun'] and '10:30\u200aPM' in alarm['time']:
                                outcome["complete"] = True
                        except KeyError:
                            pass
                except KeyError:
                    pass

        return outcome


class SingleTask_Clock_7(SingleTask_Clock_General):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        outs = find_matching_subtrees(xml_compressed_tree, "Alarm")
        outcome = {"judge_page": True, "1": False, "complete": False}
        if len(outs) == 0 or (len(outs) == 1 and "click ; ;;Alarm" in next(iter(outs[0]))):
            return outcome

        for out in outs:
            alarms_data = extract_alarms(out)
            # print(alarms_data)
            for alarm in alarms_data:
                try:
                    if alarm['status'] != 'unchecked':
                        return outcome
                except KeyError:
                    break

        outcome["1"] = True
        outcome["complete"] = True

        return outcome


class SingleTask_Clock_8(SingleTask_Clock_General):

    def get_time(self, str):
        strs = str.split(";")
        for substr in strs:
            if "PM" in substr:
                time = substr.split("\u200a")[0]
                hour = int(time.split(":")[0])
                minute = int(time.split(":")[1])
                return hour, minute

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        outs = find_matching_subtrees(xml_compressed_tree, "Alarm")
        outcome = {"judge_page": True, "1": False, "complete": False}
        if len(outs) == 0 or (len(outs) == 1 and "click ; ;;Alarm" in next(iter(outs[0]))):
            return outcome

        for out in outs:
            alarms_data = extract_alarms(out)
            # print(alarms_data)
            for alarm in alarms_data:
                try:
                    if "PM" in alarm["time"] and (self.get_time(alarm["time"])[0] > 2 or (
                            self.get_time(alarm["time"])[0] == 2 and self.get_time(alarm["time"])[1] > 0)):
                        return outcome
                except KeyError:
                    pass

        outcome["1"] = True
        outcome["complete"] = True

        return outcome


class SingleTask_Clock_9(SingleTask_Clock_General):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        outs = find_matching_subtrees(xml_compressed_tree, "Alarm")
        outcome = {"judge_page": True, "1": False, "complete": False}
        if len(outs) == 0 or (len(outs) == 1 and "click ; ;;Alarm" in next(iter(outs[0]))):
            return outcome

        for out in outs:
            alarms_data = extract_alarms(out)
            # print(alarms_data)
            for alarm in alarms_data:
                try:
                    if "4:00\u200aPM" in alarm["time"]:
                        if alarm['status'] == 'unchecked':
                            outcome["1"] = True
                            outcome["complete"] = True
                            break
                except KeyError:
                    pass

        return outcome


class SingleTask_Clock_10(SingleTask_Clock_General):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        answer = "7:30AM"
        self.save_answer(answer)
        # print(line)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_Clock_11(SingleTask_Clock_General):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        answer = "No"
        self.save_answer(answer)
        # print(line)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_Clock_12(SingleTask_Clock_General):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        answer = "Yes"
        self.save_answer(answer)
        # print(line)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_Clock_13(SingleTask_Clock_General):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        answer = "Two alarms"
        self.save_answer(answer)
        # print(line)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_Clock_14(SingleTask_Clock_General):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        answer = "No"
        self.save_answer(answer)
        # print(line)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_Clock_15(SingleTask_Clock_General):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        outcome = {"judge_page": True, "1": False, "2": False, "complete": False}
        outs_london = find_subtrees_of_parents_with_key(xml_compressed_tree, "London")
        outs_barcelona = find_subtrees_of_parents_with_key(xml_compressed_tree, "Barcelona")

        if len(outs_london) > 0:
            outcome["1"] = True
        if len(outs_barcelona) > 0:
            outcome["2"] = True

        outcome["complete"] = outcome["1"] and outcome["2"]
        return outcome


class SingleTask_Clock_16(SingleTask_Clock_General):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        answer = "6 hours behind"
        self.save_answer(answer)
        # print("???????", line)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_Clock_17(SingleTask_Clock_General):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        outcome = {"judge_page": True, "1": False, "complete": False}
        outs_barcelona = find_subtrees_of_parents_with_key(xml_compressed_tree, "Barcelona")
        try:
            selected_dict = find_matching_subtrees(xml_compressed_tree, "focusable ; selected ; selected")[0]
            selected = next(iter(selected_dict))
            if "Clock" not in selected:
                return outcome
        except:
            return {"judge_page": False}

        if len(outs_barcelona) == 0:
            outcome["1"] = True
            outcome["complete"] = True

        return outcome


class SingleTask_Clock_18(SingleTask_Clock_General):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        outs = find_matching_subtrees(xml_compressed_tree, "TextView")
        outcome = {"judge_page": True, "1": False, "2": False, "3": False, "complete": False}

        for out in outs:
            for key, value in out.items():
                if "hour" in key and "minute" in key and "second" in key:
                    hour = key.split("hour")[0].rstrip().split(" ")[-1]
                    minute = key.split("minute")[0].rstrip().split(" ")[-1]
                    second = key.split("second")[0].rstrip().split(" ")[-1]
                    if hour == "1":
                        outcome["1"] = True
                    if minute == "15":
                        outcome["2"] = True
                    if second == "0":
                        outcome["3"] = True

        outcome["complete"] = outcome["1"] and outcome["2"] and outcome["3"]
        return outcome


class SingleTask_Clock_19(SingleTask_Clock_General):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        outcome = {"judge_page": True, "1": False, "2": False, "complete": False}
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "BEDTIME")

        for out in outs:
            out = out.values()
            for single_out in out:
                for key, value in single_out.items():
                    if "Bedtime" in key:
                        bed_time = key.split("Bedtime")[-1].split()
                        b_time, m_or_n = bed_time[0], bed_time[1]
                        b_time_split = b_time.split(":")
                        if len(b_time_split) != 2:
                            outcome["1"] = False
                            continue

                        b_hour, b_min = b_time_split[0], b_time_split[1]
                        if m_or_n == 'PM':
                            outcome["1"] = (b_hour == "10" and b_min == "00")
                        else:
                            outcome["1"] = False
                    if "Wake-up" in key:
                        wake_time = key.split("Wake-up")[-1].split()
                        w_time, m_or_n = wake_time[0], wake_time[1]
                        w_hour, w_min = w_time.split(":")
                        if m_or_n == 'AM':
                            outcome["2"] = (w_hour == "7" and w_min == "00")
                        else:
                            outcome["2"] = False

        outcome["complete"] = outcome["1"] and outcome["2"]
        return outcome


class SingleTask_Clock_20(SingleTask_Clock_General):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        outcome = {"judge_page": True, "1": False, "complete": False}
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Alarm")

        for out in outs:
            out = out.values()
            for single_out in out:
                for key, value in single_out.items():
                    if "sleep sound" in key:
                        str = key.split("sleep sound ")[-1].rstrip()
                        if str == "Deep space":
                            outcome["1"] = True
                            outcome["complete"] = True
                            break

        return outcome


class SingleTask_Clock_21(SingleTask_Clock_General):

    def judge_page(self, xml_compressed_tree):
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "AM Wake-up 7:00")
        if len(outs) > 0:
            return True
        else:
            return False

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        outcome = {"judge_page": True, "1": False, "complete": False}
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "AM Wake-up 7:00")

        for out in outs:
            out = out.values()
            for single_out in out:
                for key, value in single_out.items():
                    if "click check ; checked" in key:
                        outcome["1"] = True
                        outcome["complete"] = True
                        break

        return outcome


class SingleTask_Clock_22(SingleTask_Clock_General):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        outcome = {"judge_page": True, "1": True, "complete": True}
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Analog")

        if len(outs) == 0:
            outcome["1"] = False
            outcome["complete"] = False

        return outcome


class SingleTask_Clock_23(SingleTask_Clock_General):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        outcome = {"judge_page": True, "1": False, "complete": False}
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Home time zone ")

        for out in outs:
            out = out.values()
            for single_out in out:
                for key, value in single_out.items():
                    if "Tokyo" in key:
                        outcome["1"] = True
                        outcome["complete"] = True
                        break

        return outcome


class SingleTask_Clock_24(SingleTask_Clock_General):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        outcome = {"judge_page": True, "1": False, "complete": False}
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Silence after ")

        for out in outs:
            out = out.values()
            for single_out in out:
                for key, value in single_out.items():
                    key = key.split(";")[-1]
                    if key == "5 minutes ":
                        outcome["1"] = True
                        outcome["complete"] = True
                        break

        return outcome


class SingleTask_Clock_25(SingleTask_Clock_General):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        outcome = {"judge_page": True, "1": False, "complete": False}
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Alarm")
        outs_2 = find_subtrees_of_parents_with_key(xml_compressed_tree, "Clock")
        outs_3 = find_subtrees_of_parents_with_key(xml_compressed_tree, "Timer")
        outs_4 = find_subtrees_of_parents_with_key(xml_compressed_tree, "Stopwatch")

        if len(outs) > 0 and len(outs_2) > 0 and len(outs_3) > 0 and len(outs_4) > 0:
            outcome["1"] = True
            outcome["complete"] = True

        return outcome


class SingleTask_Clock_26(SingleTask_Clock_General):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        outcome = {"judge_page": True, "1": False, "complete": False}
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Alarm")

        for out in outs:
            alarms_data = extract_alarms(out)
            for alarm in alarms_data:
                try:
                    if '7:30' in alarm['time'] and "AM" in alarm["time"]:
                        if alarm['status'] == 'unchecked':
                            outcome["1"] = True
                            outcome["complete"] = True
                            break
                except KeyError:
                    pass

        return outcome


class SingleTask_Clock_27(SingleTask_Clock_General):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        outcome = {"judge_page": True, "1": False, "complete": False}
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Alarm")

        for out in outs:
            alarms_data = extract_alarms(out)
            for alarm in alarms_data:
                try:
                    if '3:00' in alarm["time"] and "PM" in alarm["time"]:
                        if alarm['status'] == 'checked':
                            outcome["1"] = True
                            outcome["complete"] = True
                except KeyError:
                    pass

        return outcome


class SingleTask_Clock_LLM_1(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is there an alarm set for 3:00 PM?
2. Does this alarm have the label "meeting"?
3. Is this alarm turned on (checked)?
Respond in JSON format with keys: {"has_correct_time": bool, "has_correct_label": bool, "is_enabled": bool}"""

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
                    "1": llm_result["has_correct_time"],
                    "2": llm_result["has_correct_label"],
                    "3": llm_result["is_enabled"],
                    "complete": (llm_result["has_correct_time"] and 
                               llm_result["has_correct_label"] and 
                               llm_result["is_enabled"])
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        outcome = {"judge_page": True, "1": False, "2": False, "3": False, "complete": False}
        
        for out in find_subtrees_of_parents_with_key(xml_compressed_tree, "Alarm"):
            alarms_data = extract_alarms(out)
            for alarm in alarms_data:
                try:
                    if '3:00\u200aPM' in alarm['time']:
                        outcome["1"] = True
                        try:
                            if alarm['label'] == 'meeting':
                                outcome["2"] = True
                        except KeyError:
                            pass
                        try:
                            if alarm['status'] == 'checked':
                                outcome["3"] = True
                        except KeyError:
                            pass
                        try:
                            if alarm['status'] == 'checked' and alarm['label'] == 'meeting' and '3:00\u200aPM' in alarm['time']:
                                outcome["complete"] = True
                        except KeyError:
                            pass
                except KeyError:
                    pass
        return outcome


class SingleTask_Clock_LLM_2(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is there an alarm set for 6:45 AM?
2. Is vibrate disabled (unchecked) for this alarm?
3. Is the ringtone set to "Argon"?
4. Is this alarm turned on (checked)?
Respond in JSON format with keys: {"has_correct_time": bool, "vibrate_disabled": bool, "has_correct_ringtone": bool, "is_enabled": bool}"""

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
                    "1": llm_result["has_correct_time"],
                    "2": llm_result["vibrate_disabled"],
                    "3": llm_result["has_correct_ringtone"],
                    "4": llm_result["is_enabled"],
                    "complete": (llm_result["has_correct_time"] and 
                               llm_result["vibrate_disabled"] and 
                               llm_result["has_correct_ringtone"] and
                               llm_result["is_enabled"])
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        outcome = {"judge_page": True, "1": False, "2": False, "3": False, "4": False, "complete": False}
        
        for out in find_subtrees_of_parents_with_key(xml_compressed_tree, "Alarm"):
            alarms_data = extract_alarms(out)
            for alarm in alarms_data:
                try:
                    if '6:45\u200aAM' in alarm['time']:
                        outcome["1"] = True
                        try:
                            if alarm['vibrate'] == 'unchecked':
                                outcome["2"] = True
                        except KeyError:
                            pass
                        try:
                            if alarm["ringtone"] == 'Argon':
                                outcome["3"] = True
                        except KeyError:
                            pass
                        try:
                            if alarm['status'] == 'checked':
                                outcome["4"] = True
                        except KeyError:
                            pass
                        try:
                            if (alarm['status'] == 'checked' and 
                                alarm["ringtone"] == 'Argon' and
                                alarm['vibrate'] == 'unchecked' and 
                                '6:45\u200aAM' in alarm['time']):
                                outcome["complete"] = True
                        except KeyError:
                            pass
                except KeyError:
                    pass
        return outcome


class SingleTask_Clock_LLM_3(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is there an alarm set for 7:00 AM?
2. Is this alarm set to repeat on Monday through Friday only?
3. Is this alarm turned on (checked)?
Respond in JSON format with keys: {"has_correct_time": bool, "has_correct_days": bool, "is_enabled": bool}"""

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
                    "1": llm_result["has_correct_time"],
                    "2": llm_result["has_correct_days"],
                    "3": llm_result["is_enabled"],
                    "complete": (llm_result["has_correct_time"] and 
                               llm_result["has_correct_days"] and 
                               llm_result["is_enabled"])
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        outcome = {"judge_page": True, "1": False, "2": False, "3": False, "complete": False}
        
        for out in find_subtrees_of_parents_with_key(xml_compressed_tree, "Alarm"):
            alarms_data = extract_alarms(out)
            for alarm in alarms_data:
                try:
                    if '7:00\u200aAM' in alarm['time']:
                        outcome["1"] = True
                        try:
                            if alarm['days'] == ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']:
                                outcome["2"] = True
                        except KeyError:
                            pass
                        try:
                            if alarm['status'] == 'checked':
                                outcome["3"] = True
                        except KeyError:
                            pass
                        try:
                            if (alarm['status'] == 'checked' and 
                                alarm['days'] == ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'] and 
                                '7:00\u200aAM' in alarm['time']):
                                outcome["complete"] = True
                        except KeyError:
                            pass
                except KeyError:
                    pass
        return outcome


class SingleTask_Clock_LLM_4(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is there an alarm set for 9:00 AM?
2. Is this alarm set to repeat every day?
3. Is this alarm turned on (checked)?
Respond in JSON format with keys: {"has_correct_time": bool, "repeats_daily": bool, "is_enabled": bool}"""

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
                    "1": llm_result["has_correct_time"],
                    "2": llm_result["repeats_daily"],
                    "3": llm_result["is_enabled"],
                    "complete": (llm_result["has_correct_time"] and 
                               llm_result["repeats_daily"] and 
                               llm_result["is_enabled"])
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        outcome = {"judge_page": True, "1": False, "2": False, "3": False, "complete": False}
        
        for out in find_subtrees_of_parents_with_key(xml_compressed_tree, "Alarm"):
            alarms_data = extract_alarms(out)
            for alarm in alarms_data:
                try:
                    if '9:00\u200aAM' in alarm['time']:
                        outcome["1"] = True
                        try:
                            if alarm['days'] == ['Every day']:
                                outcome["2"] = True
                        except KeyError:
                            pass
                        try:
                            if alarm['status'] == 'checked':
                                outcome["3"] = True
                        except KeyError:
                            pass
                        try:
                            if (alarm['status'] == 'checked' and 
                                alarm['days'] == ['Every day'] and 
                                '9:00\u200aAM' in alarm['time']):
                                outcome["complete"] = True
                        except KeyError:
                            pass
                except KeyError:
                    pass
        return outcome


class SingleTask_Clock_LLM_5(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is there an alarm set for 10:30 AM?
2. Is this alarm set for tomorrow only?
3. Is this alarm turned on (checked)?
Respond in JSON format with keys: {"has_correct_time": bool, "set_for_tomorrow": bool, "is_enabled": bool}"""

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
                    "1": llm_result["has_correct_time"],
                    "2": llm_result["set_for_tomorrow"],
                    "3": llm_result["is_enabled"],
                    "complete": (llm_result["has_correct_time"] and 
                               llm_result["set_for_tomorrow"] and 
                               llm_result["is_enabled"])
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        outcome = {"judge_page": True, "1": False, "2": False, "3": False, "complete": False}
        
        for out in find_subtrees_of_parents_with_key(xml_compressed_tree, "Alarm"):
            alarms_data = extract_alarms(out)
            for alarm in alarms_data:
                try:
                    if '10:30\u200aAM' in alarm['time']:
                        outcome["1"] = True
                        try:
                            if alarm['days'] == ['Tomorrow']:
                                outcome["2"] = True
                        except KeyError:
                            pass
                        try:
                            if alarm['status'] == 'checked':
                                outcome["3"] = True
                        except KeyError:
                            pass
                        try:
                            if (alarm['status'] == 'checked' and 
                                alarm['days'] == ['Tomorrow'] and 
                                '10:30\u200aAM' in alarm['time']):
                                outcome["complete"] = True
                        except KeyError:
                            pass
                except KeyError:
                    pass
        return outcome


class SingleTask_Clock_LLM_6(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is there an alarm set for 10:30 PM?
2. Is this alarm set to repeat on Saturday and Sunday only?
3. Does this alarm have the label "Watch Football Games"?
4. Is this alarm turned on (checked)?
Respond in JSON format with keys: {"has_correct_time": bool, "repeats_weekends": bool, "has_correct_label": bool, "is_enabled": bool}"""

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
                    "1": llm_result["has_correct_time"],
                    "2": llm_result["repeats_weekends"],
                    "3": llm_result["has_correct_label"],
                    "4": llm_result["is_enabled"],
                    "complete": (llm_result["has_correct_time"] and 
                               llm_result["repeats_weekends"] and 
                               llm_result["has_correct_label"] and
                               llm_result["is_enabled"])
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        outcome = {"judge_page": True, "1": False, "2": False, "3": False, "4": False, "complete": False}
        
        for out in find_subtrees_of_parents_with_key(xml_compressed_tree, "Alarm"):
            alarms_data = extract_alarms(out)
            for alarm in alarms_data:
                try:
                    if '10:30\u200aPM' in alarm['time']:
                        outcome["1"] = True
                        try:
                            if alarm['days'] == ['Sat', 'Sun']:
                                outcome["2"] = True
                        except KeyError:
                            pass
                        try:
                            if alarm['label'] == 'Watch Football Games':
                                outcome["3"] = True
                        except KeyError:
                            pass
                        try:
                            if alarm['status'] == 'checked':
                                outcome["4"] = True
                        except KeyError:
                            pass
                        try:
                            if (alarm['status'] == 'checked' and 
                                alarm['label'] == 'Watch Football Games' and
                                alarm['days'] == ['Sat', 'Sun'] and 
                                '10:30\u200aPM' in alarm['time']):
                                outcome["complete"] = True
                        except KeyError:
                            pass
                except KeyError:
                    pass
        return outcome


class SingleTask_Clock_LLM_7(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Are all alarms turned off (unchecked)?
Respond in JSON format with keys: {"all_alarms_disabled": bool}"""

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
                    "1": llm_result["all_alarms_disabled"],
                    "complete": llm_result["all_alarms_disabled"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        outcome = {"judge_page": True, "1": False, "complete": False}
        
        outs = find_matching_subtrees(xml_compressed_tree, "Alarm")
        if len(outs) == 0 or (len(outs) == 1 and "click ; ;;Alarm" in next(iter(outs[0]))):
            return outcome

        for out in outs:
            alarms_data = extract_alarms(out)
            for alarm in alarms_data:
                try:
                    if alarm['status'] != 'unchecked':
                        return outcome
                except KeyError:
                    break

        outcome["1"] = True
        outcome["complete"] = True
        return outcome


class SingleTask_Clock_LLM_8(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Are there any alarms set for after 2:00 PM?
Respond in JSON format with keys: {"has_afternoon_alarms": bool}"""

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
                    "1": not llm_result["has_afternoon_alarms"],  # Inverted because we want to verify no afternoon alarms
                    "complete": not llm_result["has_afternoon_alarms"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        outcome = {"judge_page": True, "1": False, "complete": False}
        
        outs = find_matching_subtrees(xml_compressed_tree, "Alarm")
        if len(outs) == 0 or (len(outs) == 1 and "click ; ;;Alarm" in next(iter(outs[0]))):
            return outcome

        for out in outs:
            alarms_data = extract_alarms(out)
            for alarm in alarms_data:
                try:
                    if "PM" in alarm["time"]:
                        hour, minute = self.get_time(alarm["time"])
                        if hour > 2 or (hour == 2 and minute > 0):
                            return outcome
                except KeyError:
                    pass

        outcome["1"] = True
        outcome["complete"] = True
        return outcome

    def get_time(self, str):
        strs = str.split(";")
        for substr in strs:
            if "PM" in substr:
                time = substr.split("\u200a")[0]
                hour = int(time.split(":")[0])
                minute = int(time.split(":")[1])
                return hour, minute
        return 0, 0


class SingleTask_Clock_LLM_9(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is there an alarm set for 4:00 PM and is it turned off (unchecked)?
Respond in JSON format with keys: {"alarm_disabled": bool}"""

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
                    "1": llm_result["alarm_disabled"],
                    "complete": llm_result["alarm_disabled"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        outcome = {"judge_page": True, "1": False, "complete": False}
        
        outs = find_matching_subtrees(xml_compressed_tree, "Alarm")
        if len(outs) == 0 or (len(outs) == 1 and "click ; ;;Alarm" in next(iter(outs[0]))):
            return outcome

        for out in outs:
            alarms_data = extract_alarms(out)
            for alarm in alarms_data:
                try:
                    if "4:00\u200aPM" in alarm["time"]:
                        if alarm['status'] == 'unchecked':
                            outcome["1"] = True
                            outcome["complete"] = True
                            break
                except KeyError:
                    pass

        return outcome


class SingleTask_Clock_LLM_10(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text output and verify:
1. What is the earliest enabled (checked) alarm time?
Respond in JSON format with keys: {"earliest_alarm": string}"""

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
                "1": llm_result.get("earliest_alarm") == "7:30AM",
                "complete": llm_result.get("earliest_alarm") == "7:30AM"
            }
            return result
        except Exception as e:
            print(f"LLM analysis failed: {e}")
            return {"judge_page": True, "1": False, "complete": False}


class SingleTask_Clock_LLM_11(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text output and verify:
1. Is there an alarm set for 4:00 PM that repeats every day?
Respond in JSON format with keys: {"has_daily_4pm_alarm": bool}"""

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
                "1": not llm_result.get("has_daily_4pm_alarm", True),  # Inverted because we expect "No"
                "complete": not llm_result.get("has_daily_4pm_alarm", True)
            }
            return result
        except Exception as e:
            print(f"LLM analysis failed: {e}")
            return {"judge_page": True, "1": False, "complete": False}


class SingleTask_Clock_LLM_12(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text output and verify:
1. Does the alarm at 4:00 PM have vibrate enabled (checked)?
Respond in JSON format with keys: {"vibrate_enabled": bool}"""

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
                "1": llm_result.get("vibrate_enabled", False),
                "complete": llm_result.get("vibrate_enabled", False)
            }
            return result
        except Exception as e:
            print(f"LLM analysis failed: {e}")
            return {"judge_page": True, "1": False, "complete": False}


class SingleTask_Clock_LLM_13(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text output and verify:
1. How many alarms are currently enabled (checked)?
Respond in JSON format with keys: {"enabled_alarm_count": string}"""

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
                "1": llm_result.get("enabled_alarm_count") == "Two alarms",
                "complete": llm_result.get("enabled_alarm_count") == "Two alarms"
            }
            return result
        except Exception as e:
            print(f"LLM analysis failed: {e}")
            return {"judge_page": True, "1": False, "complete": False}


class SingleTask_Clock_LLM_14(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text output and verify:
1. Is the alarm at 9:00 AM enabled (checked)?
Respond in JSON format with keys: {"alarm_enabled": bool}"""

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
                "1": not llm_result.get("alarm_enabled", True),  # Inverted because we expect "No"
                "complete": not llm_result.get("alarm_enabled", True)
            }
            return result
        except Exception as e:
            print(f"LLM analysis failed: {e}")
            return {"judge_page": True, "1": False, "complete": False}


class SingleTask_Clock_LLM_15(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is London time zone added to the world clock list?
2. Is Barcelona time zone added to the world clock list?
Respond in JSON format with keys: {"london_added": bool, "barcelona_added": bool}"""

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
                    "1": llm_result["london_added"],
                    "2": llm_result["barcelona_added"],
                    "complete": llm_result["london_added"] and llm_result["barcelona_added"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        outcome = {"judge_page": True, "1": False, "2": False, "complete": False}
        
        outs_london = find_subtrees_of_parents_with_key(xml_compressed_tree, "London")
        outs_barcelona = find_subtrees_of_parents_with_key(xml_compressed_tree, "Barcelona")

        if len(outs_london) > 0:
            outcome["1"] = True
        if len(outs_barcelona) > 0:
            outcome["2"] = True

        outcome["complete"] = outcome["1"] and outcome["2"]
        return outcome


class SingleTask_Clock_LLM_16(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text output and verify:
1. Is the time difference between Barcelona and the local time 6 hours behind?
Respond in JSON format with keys: {"6_hours_behind": bool}"""

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
                "1": llm_result.get("6_hours_behind", True),
                "complete": llm_result.get("6_hours_behind", True)
            }
            return result
        except Exception as e:
            print(f"LLM analysis failed: {e}")
            return {"judge_page": True, "1": False, "complete": False}


class SingleTask_Clock_LLM_17(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is Barcelona time zone removed from the world clock list?
Respond in JSON format with keys: {"barcelona_removed": bool}"""

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
                    "1": llm_result["barcelona_removed"],
                    "complete": llm_result["barcelona_removed"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        outcome = {"judge_page": True, "1": False, "complete": False}
        
        try:
            selected_dict = find_matching_subtrees(xml_compressed_tree, "focusable ; selected ; selected")[0]
            selected = next(iter(selected_dict))
            if "Clock" not in selected:
                return outcome
        except:
            return {"judge_page": False}

        outs_barcelona = find_subtrees_of_parents_with_key(xml_compressed_tree, "Barcelona")
        if len(outs_barcelona) == 0:
            outcome["1"] = True
            outcome["complete"] = True

        return outcome


class SingleTask_Clock_LLM_18(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is the timer set to 1 hour?
2. Is the timer set to 15 minutes?
3. Is the timer set to 0 seconds?
Respond in JSON format with keys: {"hour_correct": bool, "minute_correct": bool, "second_correct": bool}"""

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
                    "1": llm_result["hour_correct"],
                    "2": llm_result["minute_correct"],
                    "3": llm_result["second_correct"],
                    "complete": (llm_result["hour_correct"] and 
                               llm_result["minute_correct"] and 
                               llm_result["second_correct"])
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        outcome = {"judge_page": True, "1": False, "2": False, "3": False, "complete": False}
        
        outs = find_matching_subtrees(xml_compressed_tree, "TextView")
        for out in outs:
            for key, value in out.items():
                if "hour" in key and "minute" in key and "second" in key:
                    hour = key.split("hour")[0].rstrip().split(" ")[-1]
                    minute = key.split("minute")[0].rstrip().split(" ")[-1]
                    second = key.split("second")[0].rstrip().split(" ")[-1]
                    if hour == "1":
                        outcome["1"] = True
                    if minute == "15":
                        outcome["2"] = True
                    if second == "0":
                        outcome["3"] = True

        outcome["complete"] = outcome["1"] and outcome["2"] and outcome["3"]
        return outcome


class SingleTask_Clock_LLM_19(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is bedtime set to 10:00 PM?
2. Is wake-up time set to 7:00 AM?
Respond in JSON format with keys: {"bedtime_correct": bool, "wakeup_correct": bool}"""

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
                    "1": llm_result["bedtime_correct"],
                    "2": llm_result["wakeup_correct"],
                    "complete": llm_result["bedtime_correct"] and llm_result["wakeup_correct"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        outcome = {"judge_page": True, "1": False, "2": False, "complete": False}
        
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "BEDTIME")
        for out in outs:
            out = out.values()
            for single_out in out:
                for key, value in single_out.items():
                    if "Bedtime" in key:
                        bed_time = key.split("Bedtime")[-1].split()
                        b_time, m_or_n = bed_time[0], bed_time[1]
                        b_time_split = b_time.split(":")
                        if len(b_time_split) != 2:
                            outcome["1"] = False
                            continue

                        b_hour, b_min = b_time_split[0], b_time_split[1]
                        if m_or_n == 'PM':
                            outcome["1"] = (b_hour == "10" and b_min == "00")
                        else:
                            outcome["1"] = False
                    if "Wake-up" in key:
                        wake_time = key.split("Wake-up")[-1].split()
                        w_time, m_or_n = wake_time[0], wake_time[1]
                        w_hour, w_min = w_time.split(":")
                        if m_or_n == 'AM':
                            outcome["2"] = (w_hour == "7" and w_min == "00")
                        else:
                            outcome["2"] = False

        outcome["complete"] = outcome["1"] and outcome["2"]
        return outcome


class SingleTask_Clock_LLM_20(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is the sleep sound set to "Deep space"?
Respond in JSON format with keys: {"correct_sound": bool}"""

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
                    "1": llm_result["correct_sound"],
                    "complete": llm_result["correct_sound"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        outcome = {"judge_page": True, "1": False, "complete": False}
        
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Alarm")
        for out in outs:
            out = out.values()
            for single_out in out:
                for key, value in single_out.items():
                    if "sleep sound" in key:
                        str = key.split("sleep sound ")[-1].rstrip()
                        if str == "Deep space":
                            outcome["1"] = True
                            outcome["complete"] = True
                            break

        return outcome


class SingleTask_Clock_LLM_21(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is the wake-up alarm at 7:00 AM enabled (checked)?
Respond in JSON format with keys: {"alarm_enabled": bool}"""

    def judge_page(self, xml_compressed_tree):
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "AM Wake-up 7:00")
        if len(outs) > 0:
            return True
        else:
            return False

    def _get_screenshot_path(self, line):
        if not line:
            return None
        base_screenshot = line.get("image")
        if not base_screenshot:
            return None
        return base_screenshot

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}
        
        screenshot_path = self._get_screenshot_path(line)
        
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                llm_result = self.llm_evaluator.analyze_screenshot(screenshot_path, self.task_prompt)
                
                result = {
                    "judge_page": True,
                    "1": llm_result["alarm_enabled"],
                    "complete": llm_result["alarm_enabled"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        outcome = {"judge_page": True, "1": False, "complete": False}
        
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "AM Wake-up 7:00")
        for out in outs:
            out = out.values()
            for single_out in out:
                for key, value in single_out.items():
                    if "click check ; checked" in key:
                        outcome["1"] = True
                        outcome["complete"] = True
                        break

        return outcome


class SingleTask_Clock_LLM_22(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is the clock style set to Analog?
Respond in JSON format with keys: {"analog_style": bool}"""

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
                    "1": llm_result["analog_style"],
                    "complete": llm_result["analog_style"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        outcome = {"judge_page": True, "1": True, "complete": True}
        
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Analog")
        if len(outs) == 0:
            outcome["1"] = False
            outcome["complete"] = False

        return outcome


class SingleTask_Clock_LLM_23(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is the home time zone set to Tokyo?
Respond in JSON format with keys: {"tokyo_timezone": bool}"""

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
                    "1": llm_result["tokyo_timezone"],
                    "complete": llm_result["tokyo_timezone"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        outcome = {"judge_page": True, "1": False, "complete": False}
        
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Home time zone ")
        for out in outs:
            out = out.values()
            for single_out in out:
                for key, value in single_out.items():
                    if "Tokyo" in key:
                        outcome["1"] = True
                        outcome["complete"] = True
                        break

        return outcome


class SingleTask_Clock_LLM_24(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is the silence after duration set to 5 minutes?
Respond in JSON format with keys: {"correct_duration": bool}"""

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
                    "1": llm_result["correct_duration"],
                    "complete": llm_result["correct_duration"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        outcome = {"judge_page": True, "1": False, "complete": False}
        
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Silence after ")
        for out in outs:
            out = out.values()
            for single_out in out:
                for key, value in single_out.items():
                    key = key.split(";")[-1]
                    if key == "5 minutes ":
                        outcome["1"] = True
                        outcome["complete"] = True
                        break

        return outcome


class SingleTask_Clock_LLM_25(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Are all four main tabs visible: Alarm, Clock, Timer, and Stopwatch?
Respond in JSON format with keys: {"all_tabs_visible": bool}"""

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
                    "1": llm_result["all_tabs_visible"],
                    "complete": llm_result["all_tabs_visible"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        outcome = {"judge_page": True, "1": False, "complete": False}
        
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Alarm")
        outs_2 = find_subtrees_of_parents_with_key(xml_compressed_tree, "Clock")
        outs_3 = find_subtrees_of_parents_with_key(xml_compressed_tree, "Timer")
        outs_4 = find_subtrees_of_parents_with_key(xml_compressed_tree, "Stopwatch")

        if len(outs) > 0 and len(outs_2) > 0 and len(outs_3) > 0 and len(outs_4) > 0:
            outcome["1"] = True
            outcome["complete"] = True

        return outcome


class SingleTask_Clock_LLM_26(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is the alarm at 7:30 AM turned off (unchecked)?
Respond in JSON format with keys: {"alarm_disabled": bool}"""

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
                    "1": llm_result["alarm_disabled"],
                    "complete": llm_result["alarm_disabled"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        outcome = {"judge_page": True, "1": False, "complete": False}
        
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Alarm")
        for out in outs:
            alarms_data = extract_alarms(out)
            for alarm in alarms_data:
                try:
                    if '7:30' in alarm['time'] and "AM" in alarm["time"]:
                        if alarm['status'] == 'unchecked':
                            outcome["1"] = True
                            outcome["complete"] = True
                            break
                except KeyError:
                    pass

        return outcome


class SingleTask_Clock_LLM_27(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is there an alarm set for 3:00 PM and is it turned on (checked)?
Respond in JSON format with keys: {"alarm_enabled": bool}"""

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
                    "1": llm_result["alarm_enabled"],
                    "complete": llm_result["alarm_enabled"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        outcome = {"judge_page": True, "1": False, "complete": False}
        
        outs = find_subtrees_of_parents_with_key(xml_compressed_tree, "Alarm")
        for out in outs:
            alarms_data = extract_alarms(out)
            for alarm in alarms_data:
                try:
                    if '3:00' in alarm["time"] and "PM" in alarm["time"]:
                        if alarm['status'] == 'checked':
                            outcome["1"] = True
                            outcome["complete"] = True
                except KeyError:
                    pass

        return outcome
