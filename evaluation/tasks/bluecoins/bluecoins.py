import re
from typing import Dict
import base64
import requests
import os
from typing import Dict, Any, List
import json
import traceback


from evaluation.task import SingleTask
from evaluation.utils import find_matching_subtrees, find_subtrees_of_parents_with_key

from evaluation.tasks.llm_evaluator import LLMEvaluator

def extract_bills_NewEditBK(xml_compressed_tree) -> Dict:
    """
    {type, date, cash, note}
    type: TextView ;; ;; -> str
    date: TextView ;; ;; -> str()
    cash: EditText ;click long-click ; ;; -> int
    note: EditText ;click long-click ; ;; -> str
    """
    type = date = cash = note = ""
    results = {
        "type": type,
        "date": date,
        "cash": cash,
        "note": note
    }

    try:
        type_date_datas = find_matching_subtrees(xml_compressed_tree, "TextView ;; ;;")
        keys = [key for d in type_date_datas for key in d.keys()]
        type_key = keys[0]
        type_key = type_key.split(";; ;;")[-1].strip()
        type = type_key.split()[-1].strip()
        for key in keys:
            if re.search(r"January|February|March|April|May|June|July|August|September|October|November|December", key):
                date = key.split(";; ;;")[-1].strip()
                break
        results["type"] = type
        results["date"] = date
    except IndexError:
        pass

    try:
        cash_datas = find_subtrees_of_parents_with_key(xml_compressed_tree, "click ; ;;CNY")  # 若不存在则返回[]
        cash_datas = list(cash_datas[0].values())[0]  # 此时出错，（抛出异常）
        for key in cash_datas.keys():
            if "EditText" in key and "long-click" in key:
                cash = key.split(";;")[-1].strip()
                results["cash"] = cash
    except IndexError:
        pass

    try:
        note_datas = find_matching_subtrees(xml_compressed_tree, "EditText")[-1]
        note = list(note_datas.keys())[0].split(";;")[-1].strip()
        results["note"] = "None" if note in ("Notes", "Payee or item purchased", "Name of income") else note
    except IndexError:
        pass

    return results


class SingleTask_bluecoins_1(SingleTask):

    def judge_page(self, line):
        if line["parsed_action"]["action"] != "finish":
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(line):
            return {"judge_page": False}

        answer = "11,400.00 CNY"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_bluecoins_LLM_1(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text output and verify:
1. Does the text indicate an amount of approximately 11,400.00 CNY? (Allow for minor variations in format)
Respond in JSON format with keys: {"has_correct_amount": bool}"""

    def judge_page(self, line):
        if line["parsed_action"]["action"] != "finish":
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(line):
            return {"judge_page": False}
        
        try:
            # Get the text output from line
            text_output = json.dumps(line["parsed_action"])
            if not text_output:
                return {"judge_page": True, "1": False, "complete": False}
            
            # Use LLM to analyze the text output
            llm_result = self.llm_evaluator.analyze_text(text_output, self.task_prompt)
            
            result = {
                "judge_page": True,
                "1": llm_result["has_correct_amount"],
                "complete": llm_result["has_correct_amount"]
            }
            return result
        except Exception as e:
            print(f"LLM analysis failed: {e}")
            return {"judge_page": True, "1": False, "complete": False}


class SingleTask_bluecoins_2(SingleTask):

    def judge_page(self, line):
        if line["parsed_action"]["action"] != "finish":
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(line):
            return {"judge_page": False}

        answer = "Buying cake"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_bluecoins_LLM_2(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text output and verify:
1. Does the text mention "Buying cake" or something related to buying/purchasing cake?
Respond in JSON format with keys: {"has_cake_purchase": bool}"""

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
                "1": llm_result["has_cake_purchase"],
                "complete": llm_result["has_cake_purchase"]
            }
            return result
        except Exception as e:
            print(f"LLM analysis failed: {e}")
            return {"judge_page": True, "1": False, "complete": False}


class SingleTask_bluecoins_3(SingleTask):

    def judge_page(self, line):
        if line["parsed_action"]["action"] != "finish":
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(line):
            return {"judge_page": False}

        answer = "69.51 CNY"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_bluecoins_LLM_3(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text output and verify:
1. Does the text indicate a total amount of approximately 69.51 CNY? (Allow for minor variations in format)
Respond in JSON format with keys: {"has_correct_amount": bool}"""

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
                "1": llm_result["has_correct_amount"],
                "complete": llm_result["has_correct_amount"]
            }
            return result
        except Exception as e:
            print(f"LLM analysis failed: {e}")
            return {"judge_page": True, "1": False, "complete": False}


class SingleTask_bluecoins_4(SingleTask):

    def judge_page(self, line):
        if line["parsed_action"]["action"] != "finish":
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(line):
            return {"judge_page": False}

        answer = "Three transactions"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_bluecoins_LLM_4(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text output and verify:
1. Does the text indicate exactly three transactions?
Respond in JSON format with keys: {"has_three_transactions": bool}"""

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
                "1": llm_result["has_three_transactions"],
                "complete": llm_result["has_three_transactions"]
            }
            return result
        except Exception as e:
            print(f"LLM analysis failed: {e}")
            return {"judge_page": True, "1": False, "complete": False}


class SingleTask_bluecoins_5(SingleTask):

    def judge_page(self, line):
        if line["parsed_action"]["action"] != "finish":
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(line):
            return {"judge_page": False}

        answer = "60.12 CNY"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_bluecoins_LLM_5(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text output and verify:
1. Does the text indicate a total amount spent on taxis of approximately 60.12 CNY? (Allow for minor variations in format)
Respond in JSON format with keys: {"has_correct_amount": bool}"""

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
                "1": llm_result["has_correct_amount"],
                "complete": llm_result["has_correct_amount"]
            }
            return result
        except Exception as e:
            print(f"LLM analysis failed: {e}")
            return {"judge_page": True, "1": False, "complete": False}


class SingleTask_bluecoins_6(SingleTask):

    def judge_page(self, xml_compressed_tree):
        bill = extract_bills_NewEditBK(xml_compressed_tree)
        if bill.get("cash") == bill.get("note") == "":
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        judge_type = judge_cash = False

        bill = extract_bills_NewEditBK(xml_compressed_tree)
        if bill.get("type") == "Expense":
            judge_type = True

        if bill.get("cash") in ("512", "512.00"):
            judge_cash = True

        return {
            "judge_page": True,
            "1": judge_type,
            "2": judge_cash,
            "complete": judge_type & judge_cash
        }


class SingleTask_bluecoins_LLM_6(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this Bluecoins app screenshot and verify:
1. Is this an expense transaction?
2. Is the amount shown approximately 512 CNY? (Allow for minor variations in format like 512.00)
Respond in JSON format with keys: {"is_expense": bool, "has_correct_amount": bool}"""

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
        # if not self.judge_page(xml_compressed_tree):
        if not self.judge_page(line):
            return {"judge_page": False}
        
        screenshot_path = self._get_screenshot_path(line)
        
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                llm_result = self.llm_evaluator.analyze_screenshot(screenshot_path, self.task_prompt)
                
                result = {
                    "judge_page": True,
                    "1": llm_result["is_expense"],
                    "2": llm_result["has_correct_amount"],
                    "complete": llm_result["is_expense"] and llm_result["has_correct_amount"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        judge_type = judge_cash = False
        bill = extract_bills_NewEditBK(xml_compressed_tree)
        
        if bill.get("type") == "Expense":
            judge_type = True

        if bill.get("cash") in ("512", "512.00"):
            judge_cash = True

        return {
            "judge_page": True,
            "1": judge_type,
            "2": judge_cash,
            "complete": judge_type & judge_cash
        }


class SingleTask_bluecoins_7(SingleTask):

    def judge_page(self, xml_compressed_tree):
        bill = extract_bills_NewEditBK(xml_compressed_tree)
        if bill.get("cash") == bill.get("note") == "":
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        judge_type = judge_cash = judge_note = False

        bill = extract_bills_NewEditBK(xml_compressed_tree)
        if bill.get("type") == "Income":
            judge_type = True

        if bill.get("cash") in ("8000", "8000.00"):
            judge_cash = True

        if bill.get("note").lower() == "salary":
            judge_note = True

        return {
            "judge_page": True,
            "1": judge_type,
            "2": judge_cash,
            "3": judge_note,
            "complete": judge_type & judge_cash & judge_note
        }


class SingleTask_bluecoins_LLM_7(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this Bluecoins app screenshot and verify:
1. Is this an income transaction?
2. Is the amount shown approximately 8000 CNY? (Allow for minor variations in format like 8000.00)
3. Is the note or description "salary" or related to salary payment?
Respond in JSON format with keys: {"is_income": bool, "has_correct_amount": bool, "is_salary": bool}"""

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
        # if not self.judge_page(xml_compressed_tree):
        if not self.judge_page(line):
            return {"judge_page": False}
        
        screenshot_path = self._get_screenshot_path(line)
        
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                llm_result = self.llm_evaluator.analyze_screenshot(screenshot_path, self.task_prompt)
                
                result = {
                    "judge_page": True,
                    "1": llm_result["is_income"],
                    "2": llm_result["has_correct_amount"],
                    "3": llm_result["is_salary"],
                    "complete": llm_result["is_income"] and llm_result["has_correct_amount"] and llm_result["is_salary"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        judge_type = judge_cash = judge_note = False
        bill = extract_bills_NewEditBK(xml_compressed_tree)
        
        if bill.get("type") == "Income":
            judge_type = True

        if bill.get("cash") in ("8000", "8000.00"):
            judge_cash = True

        if bill.get("note").lower() == "salary":
            judge_note = True

        return {
            "judge_page": True,
            "1": judge_type,
            "2": judge_cash,
            "3": judge_note,
            "complete": judge_type & judge_cash & judge_note
        }


class SingleTask_bluecoins_8(SingleTask):

    def judge_page(self, xml_compressed_tree):
        bill = extract_bills_NewEditBK(xml_compressed_tree)
        if bill.get("cash") == bill.get("note") == "":
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        judge_type = judge_date = judge_cash = False

        bill = extract_bills_NewEditBK(xml_compressed_tree)
        if bill.get("type") == "Expense":
            judge_type = True

        if bill.get("date") == "May 11, 2025":
            judge_date = True

        if bill.get("cash") in ("768", "768.00"):
            judge_cash = True

        return {
            "judge_page": True,
            "1": judge_type,
            "2": judge_date,
            "3": judge_cash,
            "complete": judge_type & judge_date & judge_cash
        }


class SingleTask_bluecoins_LLM_8(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this Bluecoins app screenshot and verify:
1. Is this an expense transaction?
2. Is the date shown "May 11, 2025"?
3. Is the amount shown approximately 768 CNY? (Allow for minor variations in format like 768.00)
Respond in JSON format with keys: {"is_expense": bool, "has_correct_date": bool, "has_correct_amount": bool}"""

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
        # if not self.judge_page(xml_compressed_tree):
        if not self.judge_page(line):
            return {"judge_page": False}
        
        screenshot_path = self._get_screenshot_path(line)
        
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                llm_result = self.llm_evaluator.analyze_screenshot(screenshot_path, self.task_prompt)
                
                result = {
                    "judge_page": True,
                    "1": llm_result["is_expense"],
                    "2": llm_result["has_correct_date"],
                    "3": llm_result["has_correct_amount"],
                    "complete": llm_result["is_expense"] and llm_result["has_correct_date"] and llm_result["has_correct_amount"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        judge_type = judge_date = judge_cash = False
        bill = extract_bills_NewEditBK(xml_compressed_tree)
        
        if bill.get("type") == "Expense":
            judge_type = True

        if bill.get("date") == "May 11, 2025":
            judge_date = True

        if bill.get("cash") in ("768", "768.00"):
            judge_cash = True

        return {
            "judge_page": True,
            "1": judge_type,
            "2": judge_date,
            "3": judge_cash,
            "complete": judge_type & judge_date & judge_cash
        }


class SingleTask_bluecoins_9(SingleTask):

    def judge_page(self, xml_compressed_tree):
        bill = extract_bills_NewEditBK(xml_compressed_tree)
        if bill.get("cash") == bill.get("note") == "":
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        judge_type = judge_date = judge_cash = judge_note = False

        bill = extract_bills_NewEditBK(xml_compressed_tree)
        if bill.get("type") == "Income":
            judge_type = True

        if bill.get("date") == "March 8, 2025":
            judge_date = True

        if bill.get("cash") == "3.14":
            judge_cash = True

        if bill.get("note").lower() == "weixin red packet":
            judge_note = True

        return {
            "judge_page": True,
            "1": judge_type,
            "2": judge_date,
            "3": judge_cash,
            "4": judge_note,
            "complete": judge_type & judge_date & judge_cash & judge_note
        }


class SingleTask_bluecoins_LLM_9(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this Bluecoins app screenshot and verify:
1. Is this an income transaction?
2. Is the date shown "March 8, 2025"?
3. Is the amount shown 3.14 CNY?
4. Is the note or description "weixin red packet" or related to WeChat/Weixin red packet?
Respond in JSON format with keys: {"is_income": bool, "has_correct_date": bool, "has_correct_amount": bool, "is_red_packet": bool}"""

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
        # if not self.judge_page(xml_compressed_tree):
        if not self.judge_page(line):
            return {"judge_page": False}
        
        screenshot_path = self._get_screenshot_path(line)
        
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                llm_result = self.llm_evaluator.analyze_screenshot(screenshot_path, self.task_prompt)
                
                result = {
                    "judge_page": True,
                    "1": llm_result["is_income"],
                    "2": llm_result["has_correct_date"],
                    "3": llm_result["has_correct_amount"],
                    "4": llm_result["is_red_packet"],
                    "complete": (llm_result["is_income"] and llm_result["has_correct_date"] and 
                               llm_result["has_correct_amount"] and llm_result["is_red_packet"])
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        judge_type = judge_date = judge_cash = judge_note = False
        bill = extract_bills_NewEditBK(xml_compressed_tree)
        
        if bill.get("type") == "Income":
            judge_type = True

        if bill.get("date") == "March 8, 2025":
            judge_date = True

        if bill.get("cash") == "3.14":
            judge_cash = True

        if bill.get("note").lower() == "weixin red packet":
            judge_note = True

        return {
            "judge_page": True,
            "1": judge_type,
            "2": judge_date,
            "3": judge_cash,
            "4": judge_note,
            "complete": judge_type & judge_date & judge_cash & judge_note
        }


class SingleTask_bluecoins_10(SingleTask):

    def judge_page(self, xml_compressed_tree):
        bill = extract_bills_NewEditBK(xml_compressed_tree)
        if bill.get("cash") == bill.get("note") == "":
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        judge_type = judge_date = judge_cash = judge_note = False
        bill = extract_bills_NewEditBK(xml_compressed_tree)

        if bill.get("type") == "Expense":
            judge_type = True

        if bill.get("date") == "May 14, 2025":
            judge_date = True

        if bill.get("cash") in ("256", "256.00"):
            judge_cash = True

        if bill.get("note").lower() == "eating":
            judge_note = True

        return {
            "judge_page": True,
            "1": judge_type,
            "2": judge_date,
            "3": judge_cash,
            "4": judge_note,
            "complete": judge_type & judge_date & judge_cash & judge_note
        }


class SingleTask_bluecoins_LLM_10(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this Bluecoins app screenshot and verify:
1. Is this an expense transaction?
2. Is the date shown "May 14, 2025"?
3. Is the amount shown approximately 256 CNY? (Allow for minor variations in format like 256.00)
4. Is the note or description "eating" or related to food/dining?
Respond in JSON format with keys: {"is_expense": bool, "has_correct_date": bool, "has_correct_amount": bool, "is_eating": bool}"""

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
        # if not self.judge_page(xml_compressed_tree):
        if not self.judge_page(line):
            return {"judge_page": False}
        
        screenshot_path = self._get_screenshot_path(line)
        
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                llm_result = self.llm_evaluator.analyze_screenshot(screenshot_path, self.task_prompt)
                
                result = {
                    "judge_page": True,
                    "1": llm_result["is_expense"],
                    "2": llm_result["has_correct_date"],
                    "3": llm_result["has_correct_amount"],
                    "4": llm_result["is_eating"],
                    "complete": (llm_result["is_expense"] and llm_result["has_correct_date"] and 
                               llm_result["has_correct_amount"] and llm_result["is_eating"])
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        judge_type = judge_date = judge_cash = judge_note = False
        bill = extract_bills_NewEditBK(xml_compressed_tree)
        
        if bill.get("type") == "Expense":
            judge_type = True

        if bill.get("date") == "May 14, 2025":
            judge_date = True

        if bill.get("cash") in ("256", "256.00"):
            judge_cash = True

        if bill.get("note").lower() == "eating":
            judge_note = True

        return {
            "judge_page": True,
            "1": judge_type,
            "2": judge_date,
            "3": judge_cash,
            "4": judge_note,
            "complete": judge_type & judge_date & judge_cash & judge_note
        }


class SingleTask_bluecoins_11(SingleTask):
    origin_bill = False

    def judge_page(self, xml_compressed_tree):
        bill = extract_bills_NewEditBK(xml_compressed_tree)
        if bill.get("cash") == bill.get("note") == "":
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        bill = extract_bills_NewEditBK(xml_compressed_tree)

        if self.origin_bill is not True:
            if bill.get("date") == "May 15, 2025" and bill.get("cash") == "400.00":
                self.origin_bill = True
        else:
            judge_date = judge_cash = False

            if bill.get("date") == "May 15, 2025":
                judge_date = True

            if bill.get("cash") in ("500", "500.00"):
                judge_cash = True

            return {
                "judge_page": True,
                "1": judge_date,
                "2": judge_cash,
                "complete": judge_date & judge_cash
            }

        return {"judge_page": False}


class SingleTask_bluecoins_LLM_11(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this Bluecoins app screenshot and verify if this is the MODIFIED transaction (not the original one):
Original transaction: Amount 400.00 CNY on May 15, 2025
Expected modification: Amount should be changed to 500.00 CNY, date remains the same

Please verify:
1. Is the date still May 15, 2025?
2. Has the amount been modified to approximately 500 CNY? (Allow for minor variations in format like 500.00)
Respond in JSON format with keys: {"has_correct_date": bool, "has_correct_amount": bool}"""
        self.origin_bill = False

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
        # if not self.judge_page(xml_compressed_tree):
        if not self.judge_page(line):
            return {"judge_page": False}
        
        bill = extract_bills_NewEditBK(xml_compressed_tree)
        
        if self.origin_bill is not True:
            if bill.get("date") == "May 15, 2025" and bill.get("cash") == "400.00":
                self.origin_bill = True
                return {"judge_page": False}
        
        screenshot_path = self._get_screenshot_path(line)
        
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                llm_result = self.llm_evaluator.analyze_screenshot(screenshot_path, self.task_prompt)
                
                result = {
                    "judge_page": True,
                    "1": llm_result["has_correct_date"],
                    "2": llm_result["has_correct_amount"],
                    "complete": llm_result["has_correct_date"] and llm_result["has_correct_amount"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        judge_date = judge_cash = False

        if bill.get("date") == "May 15, 2025":
            judge_date = True

        if bill.get("cash") in ("500", "500.00"):
            judge_cash = True

        return {
            "judge_page": True,
            "1": judge_date,
            "2": judge_cash,
            "complete": judge_date & judge_cash
        }


class SingleTask_bluecoins_12(SingleTask):
    origin_bill = False

    def judge_page(self, xml_compressed_tree):
        bill = extract_bills_NewEditBK(xml_compressed_tree)
        if bill.get("cash") == bill.get("note") == "":
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        bill = extract_bills_NewEditBK(xml_compressed_tree)

        if self.origin_bill is not True:
            if bill.get("date") == "May 12, 2025" and bill.get("cash") == "18000.00":
                self.origin_bill = True
        else:
            judge_date = judge_cash = False

            if bill.get("date") == "May 10, 2025":
                judge_date = True

            if bill.get("cash") in ("18250", "18250.00"):
                judge_cash = True

            return {
                "judge_page": True,
                "1": judge_date,
                "2": judge_cash,
                "complete": judge_date & judge_cash
            }

        return {"judge_page": False}


class SingleTask_bluecoins_LLM_12(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this Bluecoins app screenshot and verify if this is the MODIFIED transaction (not the original one):
Original transaction: Amount 18000.00 CNY on May 12, 2025
Expected modification: Amount should be changed to 18250.00 CNY and date to May 10, 2025

Please verify:
1. Has the date been changed to May 10, 2025?
2. Has the amount been modified to approximately 18250 CNY? (Allow for minor variations in format like 18250.00)
Respond in JSON format with keys: {"has_correct_date": bool, "has_correct_amount": bool}"""
        self.origin_bill = False

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
        # if not self.judge_page(xml_compressed_tree):
        if not self.judge_page(line):
            return {"judge_page": False}
        
        bill = extract_bills_NewEditBK(xml_compressed_tree)
        
        if self.origin_bill is not True:
            if bill.get("date") == "May 12, 2025" and bill.get("cash") == "18000.00":
                self.origin_bill = True
                return {"judge_page": False}
        
        screenshot_path = self._get_screenshot_path(line)
        
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                llm_result = self.llm_evaluator.analyze_screenshot(screenshot_path, self.task_prompt)
                
                result = {
                    "judge_page": True,
                    "1": llm_result["has_correct_date"],
                    "2": llm_result["has_correct_amount"],
                    "complete": llm_result["has_correct_date"] and llm_result["has_correct_amount"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        judge_date = judge_cash = False

        if bill.get("date") == "May 10, 2025":
            judge_date = True

        if bill.get("cash") in ("18250", "18250.00"):
            judge_cash = True

        return {
            "judge_page": True,
            "1": judge_date,
            "2": judge_cash,
            "complete": judge_date & judge_cash
        }


class SingleTask_bluecoins_13(SingleTask):
    origin_bill = False

    def judge_page(self, xml_compressed_tree):
        bill = extract_bills_NewEditBK(xml_compressed_tree)
        if bill.get("cash") == bill.get("note") == "":
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        bill = extract_bills_NewEditBK(xml_compressed_tree)

        if self.origin_bill is not True:
            if bill.get("date") == "May 13, 2025" and bill.get("type") == "Expense":
                self.origin_bill = True
        else:
            judge_type = judge_sign = judge_date = judge_note = False
            if bill.get("type") == "Income":
                judge_type = True

            if bill.get("date") == "May 13, 2025":
                judge_date = True

            if bill.get("note").lower() == "gift":
                judge_note = True

            tvc_datas = find_matching_subtrees(xml_compressed_tree, "TextView ;click")
            keys = [key for d in tvc_datas for key in d.keys()]
            for key in keys:
                key = key.split("; ;;")[-1].strip()
                if key in ("+", "-"):
                    sign = key
                    break

            if sign == "+":
                judge_sign = True

            return {
                "judge_page": True,
                "1": judge_type,
                "2": judge_sign,
                "3": judge_date,
                "4": judge_note,
                "complete": judge_type & judge_sign & judge_date & judge_note
            }

        return {"judge_page": False}


class SingleTask_bluecoins_LLM_13(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this Bluecoins app screenshot and verify if this is the MODIFIED transaction (not the original one):
Original transaction: An expense transaction on May 13, 2025
Expected modification: Should be changed to an income transaction with note "gift" on the same date

Please verify:
1. Has the transaction type been changed to income (should see a '+' sign)?
2. Is there a '+' sign visible indicating income?
3. Is the date still May 13, 2025?
4. Has the note been changed to "gift"?
Respond in JSON format with keys: {"is_income": bool, "has_plus_sign": bool, "has_correct_date": bool, "is_gift": bool}"""
        self.origin_bill = False

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
        # if not self.judge_page(xml_compressed_tree):
        if not self.judge_page(line):
            return {"judge_page": False}
        
        bill = extract_bills_NewEditBK(xml_compressed_tree)
        
        if self.origin_bill is not True:
            if bill.get("date") == "May 13, 2025" and bill.get("type") == "Expense":
                self.origin_bill = True
                return {"judge_page": False}
        
        screenshot_path = self._get_screenshot_path(line)
        
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                llm_result = self.llm_evaluator.analyze_screenshot(screenshot_path, self.task_prompt)
                
                result = {
                    "judge_page": True,
                    "1": llm_result["is_income"],
                    "2": llm_result["has_plus_sign"],
                    "3": llm_result["has_correct_date"],
                    "4": llm_result["is_gift"],
                    "complete": (llm_result["is_income"] and llm_result["has_plus_sign"] and 
                               llm_result["has_correct_date"] and llm_result["is_gift"])
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        judge_type = judge_sign = judge_date = judge_note = False
        
        if bill.get("type") == "Income":
            judge_type = True

        if bill.get("date") == "May 13, 2025":
            judge_date = True

        if bill.get("note").lower() == "gift":
            judge_note = True

        tvc_datas = find_matching_subtrees(xml_compressed_tree, "TextView ;click")
        keys = [key for d in tvc_datas for key in d.keys()]
        for key in keys:
            key = key.split("; ;;")[-1].strip()
            if key in ("+", "-"):
                sign = key
                break

        if sign == "+":
            judge_sign = True

        return {
            "judge_page": True,
            "1": judge_type,
            "2": judge_sign,
            "3": judge_date,
            "4": judge_note,
            "complete": judge_type & judge_sign & judge_date & judge_note
        }


class SingleTask_bluecoins_14(SingleTask):
    origin_bill = False

    def judge_page(self, xml_compressed_tree):
        bill = extract_bills_NewEditBK(xml_compressed_tree)
        if bill.get("cash") == bill.get("note") == "":
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        bill = extract_bills_NewEditBK(xml_compressed_tree)

        if self.origin_bill is not True:
            if bill.get("date") == "May 2, 2025" and bill.get("type") == "Income":
                self.origin_bill = True
        else:
            judge_type = judge_sign = judge_date = judge_cash = judge_note = False

            if bill.get("type") == "Expense":
                judge_type = True

            if bill.get("date") == "May 2, 2025":
                judge_date = True

            if bill.get("cash") in ("520", "520.00"):
                judge_cash = True

            if bill.get("note").lower() == "wrong operation":
                judge_note = True
            sign = ""
            tvc_datas = find_matching_subtrees(xml_compressed_tree, "TextView ;click")
            keys = [key for d in tvc_datas for key in d.keys()]
            for key in keys:
                key = key.split("; ;;")[-1].strip()
                if key in ("+", "-"):
                    sign = key
                    break

            if sign == "-":
                judge_sign = True

            return {
                "judge_page": True,
                "1": judge_type,
                "2": judge_sign,
                "3": judge_date,
                "4": judge_cash,
                "5": judge_note,
                "complete": judge_type & judge_sign & judge_date & judge_cash & judge_note
            }

        return {"judge_page": False}


class SingleTask_bluecoins_LLM_14(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this Bluecoins app screenshot and verify if this is the MODIFIED transaction (not the original one):
Original transaction: An income transaction on May 2, 2025
Expected modification: Should be changed to an expense transaction with amount 520.00 CNY and note "wrong operation"

Please verify:
1. Has the transaction type been changed to expense?
2. Is there a '-' sign visible indicating expense?
3. Is the date still May 2, 2025?
4. Has the amount been set to approximately 520 CNY? (Allow for minor variations in format like 520.00)
5. Has the note been changed to "wrong operation"?
Respond in JSON format with keys: {"is_expense": bool, "has_minus_sign": bool, "has_correct_date": bool, "has_correct_amount": bool, "is_wrong_operation": bool}"""
        self.origin_bill = False

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
        # if not self.judge_page(xml_compressed_tree):
        if not self.judge_page(line):
            return {"judge_page": False}
        
        bill = extract_bills_NewEditBK(xml_compressed_tree)
        
        if self.origin_bill is not True:
            if bill.get("date") == "May 2, 2025" and bill.get("type") == "Income":
                self.origin_bill = True
                return {"judge_page": False}
        
        screenshot_path = self._get_screenshot_path(line)
        
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                llm_result = self.llm_evaluator.analyze_screenshot(screenshot_path, self.task_prompt)
                
                result = {
                    "judge_page": True,
                    "1": llm_result["is_expense"],
                    "2": llm_result["has_minus_sign"],
                    "3": llm_result["has_correct_date"],
                    "4": llm_result["has_correct_amount"],
                    "5": llm_result["is_wrong_operation"],
                    "complete": (llm_result["is_expense"] and llm_result["has_minus_sign"] and 
                               llm_result["has_correct_date"] and llm_result["has_correct_amount"] and
                               llm_result["is_wrong_operation"])
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        judge_type = judge_sign = judge_date = judge_cash = judge_note = False
        
        if bill.get("type") == "Expense":
            judge_type = True

        if bill.get("date") == "May 2, 2025":
            judge_date = True

        if bill.get("cash") in ("520", "520.00"):
            judge_cash = True

        if bill.get("note").lower() == "wrong operation":
            judge_note = True

        tvc_datas = find_matching_subtrees(xml_compressed_tree, "TextView ;click")
        keys = [key for d in tvc_datas for key in d.keys()]
        for key in keys:
            key = key.split("; ;;")[-1].strip()
            if key in ("+", "-"):
                sign = key
                break

        if sign == "-":
            judge_sign = True

        return {
            "judge_page": True,
            "1": judge_type,
            "2": judge_sign,
            "3": judge_date,
            "4": judge_cash,
            "5": judge_note,
            "complete": judge_type & judge_sign & judge_date & judge_cash & judge_note
        }


class SingleTask_bluecoins_15(SingleTask):
    origin_bill = False

    def judge_page(self, xml_compressed_tree):
        bill = extract_bills_NewEditBK(xml_compressed_tree)
        if bill.get("cash") == bill.get("note") == "":
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        bill = extract_bills_NewEditBK(xml_compressed_tree)

        if self.origin_bill is not True:
            if bill.get("date") == "May 12, 2025" and bill.get("cash") == "794.20":
                self.origin_bill = True
        else:
            judge_date = judge_cash = judge_note = False

            if bill.get("date") == "May 13, 2025":
                judge_date = True

            if bill.get("cash") == "936.02":
                judge_cash = True

            if bill.get("note").lower() == "grocery shopping":
                judge_note = True

            return {
                "judge_page": True,
                "1": judge_date,
                "2": judge_cash,
                "3": judge_note,
                "complete": judge_date & judge_cash & judge_note
            }

        return {"judge_page": False}


class SingleTask_bluecoins_LLM_15(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this Bluecoins app screenshot and verify if this is the MODIFIED transaction (not the original one):
Original transaction: Amount 794.20 CNY on May 12, 2025
Expected modification: Amount should be changed to 936.02 CNY, date to May 13, 2025, and note to "grocery shopping"

Please verify:
1. Has the date been changed to May 13, 2025?
2. Has the amount been modified to exactly 936.02 CNY?
3. Has the note been changed to "grocery shopping"?
Respond in JSON format with keys: {"has_correct_date": bool, "has_correct_amount": bool, "is_grocery_shopping": bool}"""
        self.origin_bill = False

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
        # if not self.judge_page(xml_compressed_tree):
        if not self.judge_page(line):
            return {"judge_page": False}
        
        bill = extract_bills_NewEditBK(xml_compressed_tree)
        
        if self.origin_bill is not True:
            if bill.get("date") == "May 12, 2025" and bill.get("cash") == "794.20":
                self.origin_bill = True
                return {"judge_page": False}
        
        screenshot_path = self._get_screenshot_path(line)
        
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                llm_result = self.llm_evaluator.analyze_screenshot(screenshot_path, self.task_prompt)
                
                result = {
                    "judge_page": True,
                    "1": llm_result["has_correct_date"],
                    "2": llm_result["has_correct_amount"],
                    "3": llm_result["is_grocery_shopping"],
                    "complete": (llm_result["has_correct_date"] and llm_result["has_correct_amount"] and 
                               llm_result["is_grocery_shopping"])
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        judge_date = judge_cash = judge_note = False

        if bill.get("date") == "May 13, 2025":
            judge_date = True

        if bill.get("cash") == "936.02":
            judge_cash = True

        if bill.get("note").lower() == "grocery shopping":
            judge_note = True

        return {
            "judge_page": True,
            "1": judge_date,
            "2": judge_cash,
            "3": judge_note,
            "complete": judge_date & judge_cash & judge_note
        }
