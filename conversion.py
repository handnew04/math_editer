import json
import os
import re
from PyQt5.QtWidgets import QHBoxLayout, QListWidget, QListWidgetItem

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
        default_data = {
            "fixed": {},
            "custom": {}
        }
        with open(MAPPING_FILE, "w", encoding="utf-8") as f:
            json.dump(default_data, f, ensure_ascii=False, indent=4)
        return default_data, {}

def save_mappings(data):
    with open(MAPPING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

mapping_data, merged_mappings = load_mappings()

def add_custom_mapping(key, value):
    global mapping_data, merged_mappings
    mapping_data.setdefault("custom", {})[key] = value
    new_merged = {}
    new_merged.update(mapping_data.get("fixed", {}))
    new_merged.update(mapping_data.get("custom", {}))
    merged_mappings = new_merged
    save_mappings(mapping_data)

def remove_custom_mapping(key):
    global mapping_data, merged_mappings
    if key in mapping_data.get("custom", {}):
        del mapping_data["custom"][key]
        new_merged = {}
        new_merged.update(mapping_data.get("fixed", {}))
        new_merged.update(mapping_data.get("custom", {}))
        merged_mappings = new_merged
        save_mappings(mapping_data)

def convert_math_shorthand(text):
    global merged_mappings
    for key, value in merged_mappings.items():
        text = text.replace(key, value)
    
    def replace_special(match):
        s = match.group(1)
        if s.isdigit():
            return "√" + "".join(digit + "\u0305" for digit in s)
        else:
            return "".join(letter.upper() + "\u0305" for letter in s)
    
    text = re.sub(r";;-(\w+)", replace_special, text)
    return text

def populate_mapping_list(self):
    self.mapping_list.clear()
    for key, value in mapping_data.get("fixed", {}).items():
        self.mapping_list.addItem(f"{key} → {value}")
    for key, value in mapping_data.get("custom", {}).items():
        self.mapping_list.addItem(f"{key} → {value}")

def setup_ui(self):
    main_layout = QHBoxLayout()
    left_layout = QVBoxLayout()
    right_layout = QVBoxLayout()

    input_label = QLabel("문제 입력 (단축키 사용 가능):")
    self.input_edit = CustomTextEdit(self)
    self.input_edit.setFont(QFont("Consolas", 12))

    self.convert_button = QPushButton("변환 실행")
    self.convert_button.clicked.connect(self.convert_text)

    log_label = QLabel("출력 로그:")
    self.log_list = QListWidget()
    self.log_list.setFont(QFont("Consolas", 12))

    self.copy_button = QPushButton("선택 항목 복사")
    self.copy_button.clicked.connect(self.copy_selected)

    self.add_mapping_button = QPushButton("새 단축키 매핑 추가")
    self.add_mapping_button.clicked.connect(self.add_mapping)

    left_layout.addWidget(input_label)
    left_layout.addWidget(self.input_edit)
    left_layout.addWidget(self.convert_button)
    left_layout.addWidget(log_label)
    left_layout.addWidget(self.log_list)
    left_layout.addWidget(self.copy_button)
    left_layout.addWidget(self.add_mapping_button)

    self.mapping_list = QListWidget()
    self.mapping_list.setFont(QFont("Consolas", 11))
    right_layout.addWidget(QLabel("현재 단축키 매핑 목록:"))
    right_layout.addWidget(self.mapping_list)

    main_layout.addLayout(left_layout)
    main_layout.addLayout(right_layout)
    self.setLayout(main_layout)

    self.resize(800, 600)
    self.populate_mapping_list()