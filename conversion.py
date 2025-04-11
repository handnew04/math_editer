# conversion.py
import json
import os
import re

MAPPING_FILE = "mapping.json"

def load_mappings():
    if os.path.exists(MAPPING_FILE):
        with open(MAPPING_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            fixed = data.get("fixed", {})
            custom = data.get("custom", {})
            merged = {}
            merged.update(fixed)
            merged.update(custom)
            return data, merged
    else:
        # 파일이 없으면, 빈 고정 매핑과 사용자 매핑으로 구성된 구조를 생성
        default_data = {
            "fixed": {},   # 기본 고정 매핑은 비워두고 외부 파일로 관리
            "custom": {}
        }
        with open(MAPPING_FILE, "w", encoding="utf-8") as f:
            json.dump(default_data, f, ensure_ascii=False, indent=4)
        return default_data, {}

def save_mappings(data):
    with open(MAPPING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 전역 매핑 데이터
mapping_data, merged_mappings = load_mappings()

def add_custom_mapping(key, value):
    global mapping_data, merged_mappings
    # 사용자 매핑에 추가
    mapping_data.setdefault("custom", {})[key] = value
    new_merged = {}
    new_merged.update(mapping_data.get("fixed", {}))
    new_merged.update(mapping_data.get("custom", {}))
    merged_mappings = new_merged
    save_mappings(mapping_data)

def convert_math_shorthand(text):
    global merged_mappings
    # JSON 파일에서 불러온 매핑(고정 + 사용자)을 먼저 적용
    for key, value in merged_mappings.items():
        text = text.replace(key, value)
    
    # ";;-문자" 패턴에 대해 처리
    def replace_special(match):
        s = match.group(1)
        if s.isdigit():
            # 숫자인 경우: 각 숫자에 결합 윗선을 붙여 전체에 루트 효과 적용
            return "√" + "".join(digit + "\u0305" for digit in s)
        else:
            # 알파벳(또는 혼합)인 경우: 소문자도 대문자로 변환 후 각 문자에 결합 윗선 추가
            return "".join(letter.upper() + "\u0305" for letter in s)
    
    text = re.sub(r";;-(\w+)", replace_special, text)
    return text