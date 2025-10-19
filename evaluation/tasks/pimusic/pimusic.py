import re
from typing import Dict, List

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

def extract_songs(xml_compressed_tree) -> List[Dict]:
    songs_data = find_matching_subtrees(xml_compressed_tree, "TextView ;; ;;")
    song_data = [list(sd.keys())[0].split(";; ;;")[-1].strip() for sd in songs_data]
    duration_pattern = re.compile(r'^(\d+:)?[0-5]?\d:[0-5]?\d$')
    start_index = 0
    for i in range(4):
        if i + 2 < len(song_data):
            if duration_pattern.match(song_data[i + 2]):
                start_index = i
                break
    result = []
    for i in range(start_index, len(song_data), 3):
        if i + 2 < len(song_data):
            song = song_data[i]
            artist = song_data[i + 1]
            duration = song_data[i + 2]
            if duration_pattern.match(duration):
                song_info = {
                    'song': song,
                    'artist': artist,
                    'duration': duration
                }
                result.append(song_info)
            else:
                break
    return result


def parse_duration(duration):
    parts = list(map(int, duration.split(':')))
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    elif len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    else:
        raise ValueError("Invalid duration format")


def extract_info(xml_compressed_tree):
    songs_data = find_matching_subtrees(xml_compressed_tree, "TextView")
    songs_set = set()
    for song_data in songs_data:
        song_data = list(song_data.keys())[0]
        song_data = song_data.split(";; ;;")[-1].strip()
        songs_set.add(song_data)
    return songs_set


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


class SingleTask_pimusic_1(SingleTask):

    def judge_page(self, line):
        if line["parsed_action"]["action"] != "finish":
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(line):
            return {"judge_page": False}

        answer = "13 songs"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_pimusic_2(SingleTask):

    def judge_page(self, line):
        if line["parsed_action"]["action"] != "finish":
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(line):
            return {"judge_page": False}

        answer = "4 songs"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_pimusic_3(SingleTask):

    def judge_page(self, line):
        if line["parsed_action"]["action"] != "finish":
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(line):
            return {"judge_page": False}

        answer = "Pulse Live"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_pimusic_4(SingleTask):

    def judge_page(self, line):
        if line["parsed_action"]["action"] != "finish":
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(line):
            return {"judge_page": False}

        answer = "13 minutes and 25 seconds"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_pimusic_5(SingleTask):

    def judge_page(self, line):
        if line["parsed_action"]["action"] != "finish":
            return False
        return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(line):
            return {"judge_page": False}

        answer = "The second song is 'Dark Side Of The Moon' and the fourth song is 'Future sounds'"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_pimusic_6(SingleTask):

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(line):
            return {"judge_page": False}

        answer = "11 minutes and 42 seconds"
        self.save_answer(answer)
        if self.check_answer(line):
            outcome = {"judge_page": True, "1": True, "complete": True}
        else:
            outcome = {"judge_page": True, "1": False, "complete": False}
        return outcome


class SingleTask_pimusic_7(SingleTask):
    judge_list = False
    judge_favo = False

    def judge_page(self, xml_compressed_tree):
        page_info = extract_info(xml_compressed_tree)
        for info in page_info:
            if "Now Playing list" in info and "Equalizer" in info:
                return True
        return False

    def judge(self, xml_compressed_tree, line):
        if not self.judge_list:
            if check_selected(xml_compressed_tree, "PLAYLISTS"):
                self.judge_list = True

        if not self.judge_favo:
            get_pf = find_matching_subtrees(xml_compressed_tree, "] ;; ;;Favorite")
            if len(get_pf) == 1:
                self.judge_favo = True

        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        if self.judge_favo:
            judge_play = False
            play_info = extract_info(xml_compressed_tree)
            if "PINK BLOOD" in play_info:
                judge_play = True

        return {
            "judge_page": True,
            "1": self.judge_list,
            "2": self.judge_favo,
            "3": judge_play,
            "complete": self.judge_list & self.judge_favo & judge_play
        }


class SingleTask_pimusic_8(SingleTask):
    judge_arti = False
    judge_sort_step = False

    def judge_page(self, xml_compressed_tree):
        get_pf = find_matching_subtrees(xml_compressed_tree, "] ;; ;;Pink Floyd")
        if len(get_pf) != 1:
            return False
        else:
            return True

    def judge(self, xml_compressed_tree, line):
        if not self.judge_arti:
            if check_selected(xml_compressed_tree, "ARTISTS"):
                self.judge_arti = True

        if not self.judge_sort_step:
            sort_info = extract_info(xml_compressed_tree)
            if "Sort By" in sort_info:
                self.judge_sort_step = True

        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        judge_pf = judge_sort_final = False
        get_pf = find_matching_subtrees(xml_compressed_tree, "] ;; ;;Pink Floyd")
        if len(get_pf) == 1:
            judge_pf = True

        if self.judge_sort_step:
            song_data = extract_songs(xml_compressed_tree)
            def dur2sec(duration):
                return parse_duration(duration)
            dur2sec_list = [dur2sec(song['duration']) for song in song_data]
            judge_sort_final = all(dur2sec_list[i] >= dur2sec_list[i + 1] for i in range(len(dur2sec_list) - 1))

        return {
            "judge_page": True,
            "1": self.judge_arti,
            "2": judge_pf,
            "3": self.judge_sort_step,
            "4": judge_sort_final,
            "complete": self.judge_arti & judge_pf & self.judge_sort_step & judge_sort_final
        }


class SingleTask_pimusic_9(SingleTask):

    def judge_page(self, xml_compressed_tree):
        return check_selected(xml_compressed_tree, "PLAYLISTS")

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        judge_list = judge_cree = False

        if check_selected(xml_compressed_tree, "PLAYLISTS"):
            judge_list = True

        list_info = extract_info(xml_compressed_tree)
        if "Creepy" in list_info:
            judge_cree = True

        return {
            "judge_page": True,
            "1": judge_list,
            "2": judge_cree,
            "complete": judge_list & judge_cree
        }


class SingleTask_pimusic_10(SingleTask):

    def judge_page(self, xml_compressed_tree):
        page_info = extract_info(xml_compressed_tree)
        for info in page_info:
            if "Now Playing list" in info and "Equalizer" in info:
                return True
        return False

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        judge_time = False
        play_info = extract_info(xml_compressed_tree)
        if "1:27" in play_info:
            judge_time = True

        return {
            "judge_page": True,
            "1": judge_time,
            "complete": judge_time
        }


class SingleTask_pimusic_11(SingleTask):

    def judge_page(self, xml_compressed_tree):
        page_info = extract_info(xml_compressed_tree)
        for info in page_info:
            if "Now Playing list" in info and "Equalizer" in info:
                return True
        return False

    def judge(self, xml_compressed_tree, line):
        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        judge_play = False
        play_info = extract_info(xml_compressed_tree)
        if "Lightship" in play_info:
            judge_play = True

        return {
            "judge_page": True,
            "1": judge_play,
            "complete": judge_play
        }


class SingleTask_pimusic_12(SingleTask):
    judge_sort_step = False

    def judge_page(self, xml_compressed_tree):
        return check_selected(xml_compressed_tree, "TRACKS")

    def judge(self, xml_compressed_tree, line):
        if not self.judge_sort_step:
            sort_info = extract_info(xml_compressed_tree)
            if "Sort By" in sort_info:
                self.judge_sort_step = True

        if not self.judge_page(xml_compressed_tree):
            return {"judge_page": False}

        judge_sort_final = False

        song_data = extract_songs(xml_compressed_tree)
        def dur2sec(duration):
            return parse_duration(duration)
        dur2sec_list = [dur2sec(song['duration']) for song in song_data]
        judge_sort_final = all(dur2sec_list[i] <= dur2sec_list[i + 1] for i in range(len(dur2sec_list) - 1))

        return {
            "judge_page": True,
            "1": self.judge_sort_step,
            "2": judge_sort_final,
            "complete": self.judge_sort_step & judge_sort_final
        }


class SingleTask_pimusic_LLM_1(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text output and verify:
1. Does the text indicate the total number of songs the user has?
2. Is the answer "13 songs"?
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


class SingleTask_pimusic_LLM_2(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text output and verify:
1. Does the text indicate the number of Pink Floyd's songs the user has?
2. Is the answer "4 songs"?
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


class SingleTask_pimusic_LLM_3(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text output and verify:
1. Does the text indicate the album name of the song "Wish You Were Here"?
2. Is the answer "Pulse Live"?
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


class SingleTask_pimusic_LLM_4(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text output and verify:
1. Does the text indicate the duration time of the longest song by Pink Floyd?
2. Is the answer "13 minutes and 24 seconds"?
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


class SingleTask_pimusic_LLM_5(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text output and verify:
1. Does the text indicate the second and fourth songs after sorting by title in ascending order?
2. Is the answer "The second song is 'Dark Side Of The Moon' and the fourth song is 'Future sounds'"?
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


class SingleTask_pimusic_LLM_6(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this text output and verify:
1. Does the text indicate the total duration time of all of Eason Chan's songs?
2. Is the answer "11 minutes and 40 seconds"?
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


class SingleTask_pimusic_LLM_7(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is the song "PINK BLOOD" currently playing?
Respond in JSON format with keys: {"pink_blood_playing": bool}"""

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
                    "1": llm_result["pink_blood_playing"],
                    "complete": llm_result["pink_blood_playing"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        judge_play = False
        play_info = extract_info(xml_compressed_tree)
        if "PINK BLOOD" in play_info:
            judge_play = True

        return {
            "judge_page": True,
            "1": judge_play,
            "complete": judge_play
        }


class SingleTask_pimusic_LLM_8(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Are Pink Floyd's songs sorted by duration time in descending order (longest to shortest)?
Respond in JSON format with keys: {"songs_sorted_descending": bool}"""

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
                    "1": llm_result["songs_sorted_descending"],
                    "complete": llm_result["songs_sorted_descending"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        song_data = extract_songs(xml_compressed_tree)
        judge_sort_final = False
        
        if song_data:
            def dur2sec(duration):
                return parse_duration(duration)
            dur2sec_list = [dur2sec(song['duration']) for song in song_data]
            judge_sort_final = all(dur2sec_list[i] >= dur2sec_list[i + 1] for i in range(len(dur2sec_list) - 1))

        return {
            "judge_page": True,
            "1": judge_sort_final,
            "complete": judge_sort_final
        }


class SingleTask_pimusic_LLM_9(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is the "PLAYLISTS" section selected/active?
2. Is a playlist named "Creepy" visible in the playlist list?
Respond in JSON format with keys: {"playlists_selected": bool, "creepy_playlist_created": bool}"""

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
                    "1": llm_result["playlists_selected"],
                    "2": llm_result["creepy_playlist_created"],
                    "complete": llm_result["playlists_selected"] and llm_result["creepy_playlist_created"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        judge_list = judge_cree = False

        if check_selected(xml_compressed_tree, "PLAYLISTS"):
            judge_list = True

        list_info = extract_info(xml_compressed_tree)
        if "Creepy" in list_info:
            judge_cree = True

        return {
            "judge_page": True,
            "1": judge_list,
            "2": judge_cree,
            "complete": judge_list & judge_cree
        }


class SingleTask_pimusic_LLM_10(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is the currently playing song paused?
2. Is the seek bar positioned at 1 minute and 27 seconds (1:27)?
Respond in JSON format with keys: {"song_paused": bool, "seek_position_correct": bool}"""

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
                    "1": llm_result["song_paused"] and llm_result["seek_position_correct"],
                    "complete": llm_result["song_paused"] and llm_result["seek_position_correct"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        judge_time = False
        play_info = extract_info(xml_compressed_tree)
        if "1:27" in play_info:
            judge_time = True

        return {
            "judge_page": True,
            "1": judge_time,
            "complete": judge_time
        }


class SingleTask_pimusic_LLM_11(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Is the song "Lightship" currently playing?
Respond in JSON format with keys: {"lightship_playing": bool}"""

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
                    "1": llm_result["lightship_playing"],
                    "complete": llm_result["lightship_playing"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        judge_play = False
        play_info = extract_info(xml_compressed_tree)
        if "Lightship" in play_info:
            judge_play = True

        return {
            "judge_page": True,
            "1": judge_play,
            "complete": judge_play
        }


class SingleTask_pimusic_LLM_12(SingleTask):
    def __init__(self, args):
        super().__init__(args)
        self.llm_evaluator = LLMEvaluator()
        self.task_prompt = """Please analyze this screenshot and verify:
1. Are the songs sorted by duration time in ascending order (shortest to longest)?
Respond in JSON format with keys: {"songs_sorted_ascending": bool}"""

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
                    "1": llm_result["songs_sorted_ascending"],
                    "complete": llm_result["songs_sorted_ascending"]
                }
                return result
            except Exception as e:
                print(f"LLM analysis failed: {e}, falling back to traditional check")
                
        # Fallback to traditional check
        song_data = extract_songs(xml_compressed_tree)
        judge_sort_final = False
        
        if song_data:
            def dur2sec(duration):
                return parse_duration(duration)
            dur2sec_list = [dur2sec(song['duration']) for song in song_data]
            judge_sort_final = all(dur2sec_list[i] <= dur2sec_list[i + 1] for i in range(len(dur2sec_list) - 1))

        return {
            "judge_page": True,
            "1": judge_sort_final,
            "complete": judge_sort_final
        }
