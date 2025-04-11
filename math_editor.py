# math_editor.py
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTextEdit, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QDialog, QLineEdit, QDialogButtonBox, QHBoxLayout
)
from PyQt5.QtGui import QFont, QGuiApplication
from conversion import convert_math_shorthand, add_custom_mapping, mapping_data, remove_custom_mapping

# CustomTextEdit: Shift+Enter 시 부모의 convert_and_copy() 호출
class CustomTextEdit(QTextEdit):
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and event.modifiers() & Qt.ShiftModifier:
            if hasattr(self.parent(), "convert_and_copy"):
                self.parent().convert_and_copy()
            return  # 기본 개행 동작 차단
        super().keyPressEvent(event)

class MappingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("새 단축키 매핑 추가")
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        self.shortcut_edit = QLineEdit()
        self.shortcut_edit.setPlaceholderText("단축키 (예: ;;스타)")
        self.replacement_edit = QLineEdit()
        self.replacement_edit.setPlaceholderText("대체 문자 (예: ★)")
        layout.addWidget(QLabel("단축키:"))
        layout.addWidget(self.shortcut_edit)
        layout.addWidget(QLabel("대체 문자:"))
        layout.addWidget(self.replacement_edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)
    
    def get_mapping(self):
        return self.shortcut_edit.text(), self.replacement_edit.text()

class MathEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("수학 문제 타이핑 도우미")
        self.setup_ui()
        
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

        # 오른쪽 매핑 리스트
        self.mapping_list = QListWidget()
        self.mapping_list.setFont(QFont("Consolas", 11))
        right_layout.addWidget(QLabel("현재 단축키 매핑 목록:"))
        right_layout.addWidget(self.mapping_list)

        self.remove_mapping_button = QPushButton("선택된 매핑 삭제")
        self.remove_mapping_button.clicked.connect(self.remove_selected_mapping)
        right_layout.addWidget(self.remove_mapping_button)

        main_layout.addLayout(left_layout, 3)
        main_layout.addLayout(right_layout, 1)

        self.setLayout(main_layout)
        self.resize(800, 600)

        self.populate_mapping_list()

    def populate_mapping_list(self):
        self.mapping_list.clear()
        self.mapping_list.addItem("🔒 고정 매핑")
        for key, value in mapping_data.get("fixed", {}).items():
            self.mapping_list.addItem(f"{key} → {value}")
        
        # 특수 패턴 매핑도 명시적으로 추가
        self.mapping_list.addItem(";;-AB → 선분 표시 (A̅B̅)")
        self.mapping_list.addItem(";;-12 → 숫자 루트 (√1̅2̅)")

        self.mapping_list.addItem(" ")

        self.mapping_list.addItem("👤 사용자 매핑")
        for key, value in mapping_data.get("custom", {}).items():
            self.mapping_list.addItem(f"{key} → {value}")

    def convert_text(self):
        original_text = self.input_edit.toPlainText()
        converted_text = convert_math_shorthand(original_text)
        self.log_list.addItem(QListWidgetItem(converted_text))
    
    def convert_and_copy(self):
        original_text = self.input_edit.toPlainText()
        converted_text = convert_math_shorthand(original_text)
        self.log_list.addItem(QListWidgetItem(converted_text))
        QGuiApplication.clipboard().setText(converted_text)
    
    def copy_selected(self):
        selected_items = self.log_list.selectedItems()
        if selected_items:
            QGuiApplication.clipboard().setText(selected_items[0].text())
    
    def add_mapping(self):
        dialog = MappingDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            shortcut, replacement = dialog.get_mapping()
            if shortcut and replacement:
                add_custom_mapping(shortcut, replacement)
                self.log_list.addItem(QListWidgetItem(f"추가된 매핑: {shortcut} -> {replacement}"))
                self.populate_mapping_list()

    def remove_selected_mapping(self):
        selected_items = self.mapping_list.selectedItems()
        if not selected_items:
            return

        for item in selected_items:
            text = item.text()
            # 사용자 매핑 섹션만 처리하도록 필터링
            if "→" not in text or "고정" in text or "특수" in text or "사용자 매핑" in text:
              continue
            shortcut = text.split("→")[0].strip()

        # 실제 사용자 매핑인지 확인 후 삭제
        if shortcut in mapping_data.get("custom", {}):
            remove_custom_mapping(shortcut)
            self.populate_mapping_list()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = MathEditor()
    editor.show()
    sys.exit(app.exec_())