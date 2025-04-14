# math_editor.py
import sys
from matplotlib import pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from io import BytesIO
from PyQt5.QtGui import QPixmap
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

    def latex_to_pixmap(self, latex_code):
        try:
            fig = plt.figure(figsize=(0.8, 0.4), dpi=100)
            fig.patch.set_visible(False)
            ax = fig.add_subplot(111)
            ax.axis("off")
            ax.text(0.5, 0.5, f"${latex_code}$", fontsize=14, ha='center', va='center')

            buf = BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight', transparent=True)
            buf.seek(0)

            pixmap = QPixmap()
            pixmap.loadFromData(buf.read())
            plt.close(fig)
            return pixmap
        except Exception as e:
            print(f"렌더링 실패: {latex_code} → {e}")
            return QPixmap()

    def setup_ui(self):
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        input_label = QLabel("입력, Shift + Enter = 바로 복사:")
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

        self.import_button = QPushButton("매핑 JSON 불러오기")
        self.import_button.clicked.connect(self.import_mapping_file)
        right_layout.addWidget(self.import_button)

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
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("단축키 또는 수식 내용으로 검색")
        self.search_bar.textChanged.connect(self.populate_mapping_list)
        right_layout.addWidget(self.search_bar)
        right_layout.addWidget(QLabel("현재 단축키 매핑 목록:"))
        right_layout.addWidget(self.mapping_list)

        self.mapping_list.itemClicked.connect(self.insert_mapping_to_input)

        self.remove_mapping_button = QPushButton("선택된 매핑 삭제")
        self.remove_mapping_button.clicked.connect(self.remove_selected_mapping)
        right_layout.addWidget(self.remove_mapping_button)

        main_layout.addLayout(left_layout, 3)
        main_layout.addLayout(right_layout, 1)

        self.setLayout(main_layout)
        self.resize(800, 600)

        self.populate_mapping_list()

    def import_mapping_file(self):
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        import shutil

        file_name, _ = QFileDialog.getOpenFileName(self, "매핑 JSON 파일 선택", "", "JSON Files (*.json)")
        if file_name:
            try:
                shutil.copy(file_name, "mapping.json")
                QMessageBox.information(self, "성공", "새 매핑 파일을 불러왔습니다.\n프로그램을 재시작해주세요.")
            except Exception as e:
                QMessageBox.critical(self, "오류", f"매핑 파일 불러오기 실패:\n{e}")

    def populate_mapping_list(self):
        self.mapping_list.clear()
        all_mappings = {}
        all_mappings.update(mapping_data.get("fixed", {}))
        all_mappings.update(mapping_data.get("custom", {}))

        # Include dynamic mappings as examples
        dynamic_examples = {
            ";1/2": "\\frac{1}{2}",
            ";루트123": "\\sqrt{123}",
            ";벡터AB": "\\vec{AB}",
            ";선분AB": "\\overline{AB}",
            "4^2(지수)": "4^2"
        }
        all_mappings.update(dynamic_examples)

        filter_text = self.search_bar.text().lower()

        for key, value in all_mappings.items():
            if filter_text and filter_text not in key.lower() and filter_text not in value.lower():
                continue

            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(2, 2, 2, 2)
            item_layout.addWidget(QLabel(key))

            preview_label = QLabel()
            preview_label.setPixmap(self.latex_to_pixmap(value))
            item_layout.addWidget(preview_label)

            item = QListWidgetItem()
            item.setSizeHint(item_widget.sizeHint())
            self.mapping_list.addItem(item)
            self.mapping_list.setItemWidget(item, item_widget)

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

        for i in selected_items:
            index = self.mapping_list.row(i)
            item_widget = self.mapping_list.itemWidget(i)
            if item_widget:
                shortcut_label = item_widget.layout().itemAt(0).widget()
                shortcut = shortcut_label.text().strip()

                # Try removing from custom first
                if shortcut in mapping_data.get("custom", {}):
                    remove_custom_mapping(shortcut)
                elif shortcut in mapping_data.get("fixed", {}):
                    del mapping_data["fixed"][shortcut]

        self.populate_mapping_list()

    def insert_mapping_to_input(self, item):
        item_widget = self.mapping_list.itemWidget(item)
        if item_widget:
            shortcut_label = item_widget.layout().itemAt(0).widget()
            shortcut = shortcut_label.text().strip()
            cursor = self.input_edit.textCursor()
            cursor.insertText(shortcut)
            self.input_edit.setFocus()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = MathEditor()
    editor.show()
    sys.exit(app.exec_())