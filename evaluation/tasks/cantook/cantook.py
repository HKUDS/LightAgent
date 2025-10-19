from evaluation.task import SingleTask
from evaluation.utils import find_matching_subtrees
from evaluation.tasks.llm_evaluator import LLMEvaluator

import re
from typing import Dict
import base64
import requests
import os
from typing import Dict, Any, List
import json
import traceback

def extract_books_info(xml_compressed_tree):
    books_data = find_matching_subtrees(xml_compressed_tree, "TextView")
    books_set = set()
    for book_data in books_data:
        book_data = list(book_data.keys())[0]
        book_data = book_data.split(";; ;;")[-1].strip()
        books_set.add(book_data)
    return books_set


def check_selected(xml_compressed_tree, key_filter):
    def helper(data):
        if isinstance(data, dict):
            for key, value in data.items():
                if key_filter in key:
                    return True
                if helper(value):
                    return True
        elif isinstance(data, list):
            for item in data:
                if helper(item):
                    return True
        return False

    selected_data = find_matching_subtrees(xml_compressed_tree, "selected, ;")
    return helper(selected_data)


class SingleTask_cantook_1(SingleTask):

    def judge_page(self, line):
        if line["parsed_action"]["action"] != "finish":
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(line):
            return {"judge_page": False}

        answer = "No"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_cantook_2(SingleTask):

    def judge_page(self, line):
        if line["parsed_action"]["action"] != "finish":
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(line):
            return {"judge_page": False}

        answer = "The Scarlet Letter"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_cantook_3(SingleTask):

    def judge_page(self, line):
        if line["parsed_action"]["action"] != "finish":
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(line):
            return {"judge_page": False}

        answer = "William Shakespeare"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_cantook_4(SingleTask):

    def judge_page(self, line):
        if line["parsed_action"]["action"] != "finish":
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(line):
            return {"judge_page": False}

        answer = "Two"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_cantook_5(SingleTask):

    def judge_page(self, line):
        if line["parsed_action"]["action"] != "finish":
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(line):
            return {"judge_page": False}

        answer = "100.0%"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_cantook_6(SingleTask):

    def judge_page(self, xml_compressed_tree):
        book_info = extract_books_info(xml_compressed_tree)
        for info in book_info:
            if ".epub" in info or "Help" in info:
                return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        judge_book = False

        book_info = extract_books_info(xml_compressed_tree)

        if "Alice's Adventures in Wonderland" in book_info:
            judge_book = True

        return {
            "judge_page": True,
            "1": judge_book,
            "complete": judge_book
        }


class SingleTask_cantook_7(SingleTask):

    def judge_page(self, xml_compressed_tree):
        outs = find_matching_subtrees(xml_compressed_tree, "My Books")
        for out in outs:
            select = find_matching_subtrees(out, "selected")
            if len(select) > 0:
                return True
        return False

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        judge_book = False

        book_info = extract_books_info(xml_compressed_tree)

        if "Don Quixote" not in book_info:
            judge_book = True

        return {
            "judge_page": True,
            "1": judge_book,
            "complete": judge_book
        }


class SingleTask_cantook_8(SingleTask):

    def judge_page(self, xml_compressed_tree):
        book_info = extract_books_info(xml_compressed_tree)
        for info in book_info:
            if "Info" not in info and "Read" not in info:
                return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        judge_book = judge_read = False

        book_info = extract_books_info(xml_compressed_tree)

        if "Hamlet" in book_info:
            judge_book = True

        if "Mark as unread" in book_info and "100.0%" in book_info:
            judge_read = True

        return {
            "judge_page": True,
            "1": judge_book,
            "2": judge_read,
            "complete": judge_book & judge_read
        }


class SingleTask_cantook_9(SingleTask):

    def judge_page(self, xml_compressed_tree):
        book_info = extract_books_info(xml_compressed_tree)
        for info in book_info:
            if "Info" not in info and "Read" not in info:
                return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        judge_book = judge_read = False

        book_info = extract_books_info(xml_compressed_tree)

        if "Oliver Twist" in book_info:
            judge_book = True

        if "Mark as read" in book_info:
            judge_read = True

        return {
            "judge_page": True,
            "1": judge_book,
            "2": judge_read,
            "complete": judge_book & judge_read
        }


class SingleTask_cantook_10(SingleTask):

    def judge_page(self, xml_compressed_tree):
        book_info = extract_books_info(xml_compressed_tree)
        for info in book_info:
            if ".epub" in info or "Help" in info:
                return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        judge_book = False

        book_info = extract_books_info(xml_compressed_tree)

        # if "Mer. Thou desir'st me to stop in my tale against the haire" in book_info:
        #     judge_book = True

        if "Romeo and Juliet" in book_info:
            judge_book = True

        return {
            "judge_page": True,
            "1": judge_book,
            "complete": judge_book
        }


class SingleTask_cantook_11(SingleTask):
    judge_cate = False

    def judge_page(self, xml_compressed_tree):
        book_info = extract_books_info(xml_compressed_tree)
        if "Tragedies" in book_info:
            return True
        else:
            return False

    def judge(self, xml_compressed_tree, line):
        if check_selected(xml_compressed_tree, "Categories"):
            self.judge_cate = True

        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        judge_trag = judge_book = False

        book_info = extract_books_info(xml_compressed_tree)

        if "Tragedies" in book_info:
            judge_trag = True

        if "Hamlet" in book_info and "Romeo and Juliet" in book_info:
            judge_book = True

        return {
            "judge_page": True,
            "1": self.judge_cate,
            "2": judge_trag,
            "3": judge_book,
            "complete": self.judge_cate & judge_trag & judge_book
        }


class SingleTask_cantook_12(SingleTask):

    def judge_page(self, xml_compressed_tree):
        return check_selected(xml_compressed_tree, "Collections")

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        judge_coll = judge_favo = False

        if check_selected(xml_compressed_tree, "Collections"):
            judge_coll = True

        book_info = extract_books_info(xml_compressed_tree)

        if "Favorite" in book_info:
            judge_favo = True

        return {
            "judge_page": True,
            "1": judge_coll,
            "2": judge_favo,
            "complete": judge_coll & judge_favo
        }


class SingleTask_cantook_LLM_1(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text output and verify:
1. Does the text indicate that Pride and Prejudice is NOT in the bookshelf?
Respond in JSON format with keys: {"has_correct_answer": bool}"""

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
                "1": llm_result["has_correct_answer"],
                "complete": llm_result["has_correct_answer"]
            }
            return result
        except Exception as e:
            print(f"LLM analysis failed: {e}")
            return {"judge_page": True, "1": False, "complete": False}


class SingleTask_cantook_LLM_2(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text output and verify:
1. Does the text indicate The Scarlet Letter ?
Respond in JSON format with keys: {"has_correct_answer": bool}"""

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
                "1": llm_result["has_correct_answer"],
                "complete": llm_result["has_correct_answer"]
            }
            return result
        except Exception as e:
            print(f"LLM analysis failed: {e}")
            return {"judge_page": True, "1": False, "complete": False}


class SingleTask_cantook_LLM_3(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text output and verify:
1. Does the text indicate that William Shakespeare is the author of the second recently added book?
Respond in JSON format with keys: {"has_correct_answer": bool}"""

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
                "1": llm_result["has_correct_answer"],
                "complete": llm_result["has_correct_answer"]
            }
            return result
        except Exception as e:
            print(f"LLM analysis failed: {e}")
            return {"judge_page": True, "1": False, "complete": False}


class SingleTask_cantook_LLM_4(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text output and verify:
1. Does the text indicate that there are exactly two Charles Dickens books?
Respond in JSON format with keys: {"has_correct_answer": bool}"""

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
                "1": llm_result["has_correct_answer"],
                "complete": llm_result["has_correct_answer"]
            }
            return result
        except Exception as e:
            print(f"LLM analysis failed: {e}")
            return {"judge_page": True, "1": False, "complete": False}


class SingleTask_cantook_LLM_5(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text output and verify:
1. Does the text indicate that Romeo and Juliet has a reading progress of 100.0%?
Respond in JSON format with keys: {"has_correct_answer": bool}"""

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
                "1": llm_result["has_correct_answer"],
                "complete": llm_result["has_correct_answer"]
            }
            return result
        except Exception as e:
            print(f"LLM analysis failed: {e}")
            return {"judge_page": True, "1": False, "complete": False}


class SingleTask_cantook_LLM_6(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is "Alice's Adventures in Wonderland" visible in the book list?
Respond in JSON format with keys: {"book_imported": bool}"""

    # def judge_page(self, xml_compressed_tree):
    #     # Removed XML tree check
    #     return True

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
        #     return {"judge_page": False}

        if not self.judge_page(line):
            return {"judge_page": False}
        
        screenshot_path = self._get_screenshot_path(line)
        
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                llm_result = self.llm_evaluator.analyze_screenshot(screenshot_path, self.task_prompt)
                
                result = {
                    "judge_page": True,
                    "1": llm_result["book_imported"],
                    "complete": llm_result["book_imported"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        judge_book = False
        book_info = extract_books_info(xml_compressed_tree)
        
        if "Alice's Adventures in Wonderland" in book_info:
            judge_book = True

        return {
            "judge_page": True,
            "1": judge_book,
            "complete": judge_book
        }


class SingleTask_cantook_LLM_7(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is "Don Quixote" absent from the book list?
Respond in JSON format with keys: {"book_deleted": bool}"""

    # def judge_page(self, xml_compressed_tree):
    #     # Removed XML tree check
    #     return True

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
        #     return {"judge_page": False}

        if not self.judge_page(line):
            return {"judge_page": False}
        
        screenshot_path = self._get_screenshot_path(line)
        
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                llm_result = self.llm_evaluator.analyze_screenshot(screenshot_path, self.task_prompt)
                
                result = {
                    "judge_page": True,
                    "1": llm_result["book_deleted"],
                    "complete": llm_result["book_deleted"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        judge_book = False
        book_info = extract_books_info(xml_compressed_tree)
        
        if "Don Quixote" not in book_info:
            judge_book = True

        return {
            "judge_page": True,
            "1": judge_book,
            "complete": judge_book
        }


class SingleTask_cantook_LLM_8(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is "Hamlet" visible in the book list?
2. Does it show a reading progress of 100.0% and an option to "Mark as unread"?
Respond in JSON format with keys: {"book_present": bool, "marked_as_read": bool}"""

    # def judge_page(self, xml_compressed_tree):
    #     # Removed XML tree check
    #     return True
    
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
        #     return {"judge_page": False}

        if not self.judge_page(line):
            return {"judge_page": False}
        
        screenshot_path = self._get_screenshot_path(line)
        
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                llm_result = self.llm_evaluator.analyze_screenshot(screenshot_path, self.task_prompt)
                
                result = {
                    "judge_page": True,
                    "1": llm_result["book_present"],
                    "2": llm_result["marked_as_read"],
                    "complete": llm_result["book_present"] and llm_result["marked_as_read"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        judge_book = judge_read = False
        book_info = extract_books_info(xml_compressed_tree)
        
        if "Hamlet" in book_info:
            judge_book = True

        if "Mark as unread" in book_info and "100.0%" in book_info:
            judge_read = True

        return {
            "judge_page": True,
            "1": judge_book,
            "2": judge_read,
            "complete": judge_book & judge_read
        }


class SingleTask_cantook_LLM_9(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is "Oliver Twist" visible in the book list?
2. Is there an option to "Mark as read" (indicating it's currently unread)?
Respond in JSON format with keys: {"book_present": bool, "marked_as_unread": bool}"""

    # def judge_page(self, xml_compressed_tree):
    #     # Removed XML tree check
    #     return True
    
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
        #     return {"judge_page": False}

        if not self.judge_page(line):
            return {"judge_page": False}
        
        screenshot_path = self._get_screenshot_path(line)
        
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                llm_result = self.llm_evaluator.analyze_screenshot(screenshot_path, self.task_prompt)
                
                result = {
                    "judge_page": True,
                    "1": llm_result["book_present"],
                    "2": llm_result["marked_as_unread"],
                    "complete": llm_result["book_present"] and llm_result["marked_as_unread"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        judge_book = judge_read = False
        book_info = extract_books_info(xml_compressed_tree)
        
        if "Oliver Twist" in book_info:
            judge_book = True

        if "Mark as read" in book_info:
            judge_read = True

        return {
            "judge_page": True,
            "1": judge_book,
            "2": judge_read,
            "complete": judge_book & judge_read
        }


class SingleTask_cantook_LLM_10(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is "Romeo and Juliet" visible and opened in the book viewer?
Respond in JSON format with keys: {"book_opened": bool}"""

    # def judge_page(self, xml_compressed_tree):
    #     # Removed XML tree check
    #     return True
    
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
        #     return {"judge_page": False}

        if not self.judge_page(line):
            return {"judge_page": False}
        
        screenshot_path = self._get_screenshot_path(line)
        
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                llm_result = self.llm_evaluator.analyze_screenshot(screenshot_path, self.task_prompt)
                
                result = {
                    "judge_page": True,
                    "1": llm_result["book_opened"],
                    "complete": llm_result["book_opened"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        judge_book = False
        book_info = extract_books_info(xml_compressed_tree)
        
        if "Romeo and Juliet" in book_info:
            judge_book = True

        return {
            "judge_page": True,
            "1": judge_book,
            "complete": judge_book
        }


class SingleTask_cantook_LLM_11(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is the "Categories" section selected/active?
2. Is the "Tragedies" category visible?
3. Are both "Hamlet" and "Romeo and Juliet" visible in the book list?
Respond in JSON format with keys: {"categories_selected": bool, "tragedies_visible": bool, "books_visible": bool}"""
        self.judge_cate = False

    # def judge_page(self, xml_compressed_tree):
    #     # Removed XML tree check
    #     return True
    
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
        if check_selected(xml_compressed_tree, "Categories"):
            self.judge_cate = True

        # if not self.judge_page(xml_compressed_tree):
        #     return {"judge_page": False}

        if not self.judge_page(line):
            return {"judge_page": False}
        
        screenshot_path = self._get_screenshot_path(line)
        
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                llm_result = self.llm_evaluator.analyze_screenshot(screenshot_path, self.task_prompt)
                
                result = {
                    "judge_page": True,
                    "1": llm_result["categories_selected"],
                    "2": llm_result["tragedies_visible"],
                    "3": llm_result["books_visible"],
                    "complete": (llm_result["categories_selected"] and llm_result["tragedies_visible"] and 
                               llm_result["books_visible"])
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        judge_trag = judge_book = False
        book_info = extract_books_info(xml_compressed_tree)
        
        if "Tragedies" in book_info:
            judge_trag = True

        if "Hamlet" in book_info and "Romeo and Juliet" in book_info:
            judge_book = True

        return {
            "judge_page": True,
            "1": self.judge_cate,
            "2": judge_trag,
            "3": judge_book,
            "complete": self.judge_cate & judge_trag & judge_book
        }


class SingleTask_cantook_LLM_12(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is the "Collections" section selected/active?
2. Is a collection named "Favorite" visible in the list?
Respond in JSON format with keys: {"collections_selected": bool, "favorite_collection_created": bool}"""

    # def judge_page(self, xml_compressed_tree):
    #     # Removed XML tree check
    #     return True
    
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
        #     return {"judge_page": False}

        if not self.judge_page(line):
            return {"judge_page": False}
        
        screenshot_path = self._get_screenshot_path(line)
        
        if screenshot_path and os.path.exists(screenshot_path):
            try:
                llm_result = self.llm_evaluator.analyze_screenshot(screenshot_path, self.task_prompt)
                
                result = {
                    "judge_page": True,
                    "1": llm_result["collections_selected"],
                    "2": llm_result["favorite_collection_created"],
                    "complete": llm_result["collections_selected"] and llm_result["favorite_collection_created"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        judge_coll = judge_favo = False
        
        if check_selected(xml_compressed_tree, "Collections"):
            judge_coll = True

        book_info = extract_books_info(xml_compressed_tree)
        
        if "Favorite" in book_info:
            judge_favo = True

        return {
            "judge_page": True,
            "1": judge_coll,
            "2": judge_favo,
            "complete": judge_coll & judge_favo
        }
