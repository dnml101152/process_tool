import uuid

from PyQt5.QtWidgets import (
    QApplication, QWidget, QListWidget, QPushButton,
    QComboBox, QTextEdit, QHBoxLayout, QVBoxLayout, QShortcut, QListWidgetItem, QLineEdit, QMessageBox,QLabel
)
from PyQt5.QtGui import QKeySequence
from rule_widget import process_input_string, reconstruct_expression, create_valid_fields_dict, tooltip_html
from trades import trade_valid_fields
from PyQt5.QtCore import Qt
import json
from models import SecurityModel, PositionModel




class MappingTool(QWidget):
    def __init__(self, mapping_dict,valid_fields,data_path,tool_tip_data = None):
        super().__init__()

        if tool_tip_data:
            self.tt_data = tool_tip_data

        self.data = {}
        self.data_path = data_path
        previous_data = self.load_data()

        if previous_data:
            self.data = previous_data

        print(999,self.data)

        self.mapping_dict = mapping_dict
        self.valid_fields = valid_fields
        # Left column: QListWidget
        self.list_widget = QListWidget()
        self.list_widget.addItems(['Item 1', 'Item 2', 'Item 3'])

        # Middle column: thin vertical box with multiple buttons
        self.button_box = QVBoxLayout()
        self.button_container = QWidget()
        self.button_container.setFixedWidth(80)  # make thin column

        button_labels = ["Up", "Add", "Down", "Delete"]
        self.button_box = QVBoxLayout()
        self.button_container = QWidget()
        self.button_container.setFixedWidth(80)

        for label in button_labels:
            btn = QPushButton(label)
            self.button_box.addWidget(btn)
            if label == "Add":
                btn.clicked.connect(self.on_new_clicked)
            elif label == "Delete":
                btn.clicked.connect(self.on_delete_clicked)
            elif label == "Up":
                btn.clicked.connect(self.on_up_clicked)
            elif label == "Down":
                btn.clicked.connect(self.on_down_clicked)

        self.button_box.addStretch()
        self.button_container.setLayout(self.button_box)

        # Right column: vertical box with dropdown and multi-line text input
        self.right_box = QVBoxLayout()
        self.dropdown = QComboBox()
        self.text_input = QTextEdit()  # multi-line input field

        self.right_box.addWidget(self.dropdown)
        self.right_box.addWidget(self.text_input)
        self.right_box.addStretch()

        # Add options to dropdown: display option text, store UUID as user data
        for key, value in self.mapping_dict.items():
            self.dropdown.addItem(value, key)

        right_container = QWidget()
        right_container.setLayout(self.right_box)

        # Main horizontal layout
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.list_widget)
        main_layout.addWidget(self.button_container)
        main_layout.addWidget(right_container)

        self.submit_button = QPushButton("Submit")

        # Connect submit button clicked signal
        self.submit_button.clicked.connect(self.on_submit_clicked)
        self.right_box.addWidget(self.submit_button)
        shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        shortcut.activated.connect(self.submit_button.click)

        # NEW: title input field
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter rule title here...")
        self.right_box.insertWidget(0,self.title_input)

        self.setLayout(main_layout)
        self.setWindowTitle("Three Column Widget with Multi-line Input (PyQt5)")

        self.list_widget.currentItemChanged.connect(self.on_item_selected)

        self.error_label = QLabel("")
        self.right_box.addWidget(self.error_label)

        self.populate_list_widget()

        field_types_str = f"<h3>Available Fields</h3><pre>{json.dumps(self.valid_fields, indent=2)}</pre>"

        self.text_input.setToolTip("Press Shift+F1 for help")
        self.text_input.setWhatsThis(tooltip_html + field_types_str)

    def on_submit_clicked(self):
        try:
            text = self.text_input.toPlainText()
            lines = text.splitlines()
            rule_update = []

            for line in lines:
                if line.strip():  # skip empty lines
                    rule = process_input_string(line, self.valid_fields)
                    rule_update.append(rule)

            item = self.list_widget.currentItem()
            if item:
                rule_id = item.data(Qt.UserRole)
                if rule_id in self.data:
                    self.data[rule_id]["rule_dicts"] = rule_update
                    self.data[rule_id]["temp"] = False
                    self.data[rule_id]["label"] = self.title_input.text().strip()
                    if not self.data[rule_id]["label"]:
                        self.data[rule_id]["label"] = self.dropdown.currentText()

                    self.data[rule_id]["mapping_label"] = self.dropdown.currentText()
                    self.data[rule_id]["mapping_id"] = self.dropdown.currentData()

                    # Refresh label in list widget
                    item.setText(self.data[rule_id]["label"])




                else:
                    print(f"[Error] Rule ID {rule_id} not found in self.data")

            else:
                # No item selected → create a new rule entry
                new_id = str(uuid.uuid4())
                title = self.title_input.text().strip()
                if not title:
                    title = self.dropdown.currentText()

                self.data[new_id] = {
                    "key": new_id,
                    "temp": False,
                    "label": title,
                    "mapping_id": self.dropdown.currentData(),
                    "rule_dicts": rule_update,
                }

            self.populate_list_widget()
            self.save_data()

        except Exception as err:
            self.error_label.setText(f"[Submit Error] {str(err)}")







        except Exception as err:
            print (err)

    def on_new_clicked(self):
        try:
            rule_id = str(uuid.uuid4())
            # Determine the new position as last index
            new_position = len(self.data)

            self.data[rule_id] = {
                "label": "New Rule",
                "temp": True,
                "rule_dicts": [],
                "position": new_position,  # <-- important for ordering
            }
            self.populate_list_widget()
            self.title_input.clear()
            self.text_input.clear()
            self.error_label.setText("")

            # Optionally, select the newly added item:
            last_row = self.list_widget.count() - 1
            if last_row >= 0:
                self.list_widget.setCurrentRow(last_row)

        except Exception as err:
            print(str(err))

    def populate_list_widget(self):
        self.list_widget.clear()
        # Sort items by position to guarantee order
        ordered = sorted(self.data.items(), key=lambda x: x[1].get("position", 0))
        for rule_id, rule_data in ordered:
            label = rule_data.get('label', 'No Label')
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, rule_id)
            if rule_data.get("temp", False):
                font = item.font()
                font.setItalic(True)
                item.setFont(font)
            self.list_widget.addItem(item)

    def on_delete_clicked(self):
        item = self.list_widget.currentItem()
        if not item:
            print("No item selected to delete.")
            return

        rule_id = item.data(Qt.UserRole)
        rule_label = self.data.get(rule_id, {}).get("label", "Unnamed Rule")

        confirm = QMessageBox.question(
            self,
            "Delete Rule",
            f"Are you sure you want to delete '{rule_label}'?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if confirm == QMessageBox.Yes and rule_id in self.data:
            del self.data[rule_id]
            print(f"Deleted rule {rule_id}")

            self.populate_list_widget()
            self.title_input.clear()
            self.text_input.clear()
            self.dropdown.setCurrentIndex(0)
            self.save_data()

    def save_data(self):
        try:
            self.update_positions_from_list_widget()  # ✅ ensure position is accurate
            filtered_data = {rule_id: data for rule_id, data in self.data.items() if not data.get("temp", True)}

            with open(self.data_path, "w", encoding="utf-8") as f:
                json.dump(filtered_data, f, indent=4)
            self.error_label.setText("Update Saved")
        except Exception as e:
            print(f"[Save Error] {e}")
    def load_data(self):
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                load_data = json.load(f)
                print(888,load_data)
                load_data = dict(
                    sorted(load_data.items(), key=lambda x: x[1].get("position", 0)))
                print(9919,load_data)
                return load_data
            print(f"Loaded rules from {filename}")
        except FileNotFoundError:
            print("No previous data found, starting fresh.")
            return None
        except Exception as e:
            print(f"[Load Error] {e}")
            return None

    def update_positions_from_list_widget(self):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            rule_id = item.data(Qt.UserRole)
            if rule_id in self.data:
                self.data[rule_id]["position"] = i

    def swap_items_in_list(self, index1, index2):
        if index1 < 0 or index2 < 0:
            return

        item1 = self.list_widget.item(index1)
        item2 = self.list_widget.item(index2)

        # Swap the text and user data
        text1, data1 = item1.text(), item1.data(Qt.UserRole)
        text2, data2 = item2.text(), item2.data(Qt.UserRole)

        item1.setText(text2)
        item1.setData(Qt.UserRole, data2)

        item2.setText(text1)
        item2.setData(Qt.UserRole, data1)

        self.list_widget.setCurrentRow(index2)  # update selection
        self.save_data()

    def on_up_clicked(self):
        current_row = self.list_widget.currentRow()
        if current_row > 0:
            keys = list(self.data.keys())
            # Swap keys
            keys[current_row], keys[current_row - 1] = keys[current_row - 1], keys[current_row]

            # Rebuild self.data in new order & update positions
            new_data = {}
            for pos, key in enumerate(keys):
                entry = self.data[key]
                entry["position"] = pos
                new_data[key] = entry

            self.data = new_data
            self.populate_list_widget()
            self.list_widget.setCurrentRow(current_row - 1)
            self.save_data()

    def on_down_clicked(self):
        current_row = self.list_widget.currentRow()
        if current_row < self.list_widget.count() - 1:
            keys = list(self.data.keys())
            keys[current_row], keys[current_row + 1] = keys[current_row + 1], keys[current_row]

            new_data = {}
            for pos, key in enumerate(keys):
                entry = self.data[key]
                entry["position"] = pos
                new_data[key] = entry

            self.data = new_data
            self.populate_list_widget()
            self.list_widget.setCurrentRow(current_row + 1)
            self.save_data()
    def on_item_selected(self):
        try:

            rule_id = self.list_widget.currentItem().data(Qt.UserRole)

            #set title input line
            self.title_input.setText(self.data.get(rule_id).get("label"))

            #set input field
            string_value = ""
            for text in self.data.get(rule_id).get("rule_dicts"):
                string_value = string_value + reconstruct_expression(text)+"\n"
            self.text_input.setPlainText(string_value)

            #set dropdown
            mapping_id = self.data.get(rule_id).get("mapping_id")
            index = self.dropdown.findData(mapping_id)  # returns -1 if not found
            if index != -1:
                self.dropdown.setCurrentIndex(index)
            else:
                print("Mapping ID not in dropdown!")


            print(rule_id)
        except Exception as err:
            print(err)



if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    mappings_path = r"C:\Users\dnml1\Downloads\types.json"
    with open(mappings_path, "r", encoding="utf-8") as f:
        mappings_list = json.load(f)
    mappings= {}
    for mapping in mappings_list:
        mappings[mapping.get("uid")] = mapping.get("title")
    print(mappings_list)
    valid_fields = {}
    valid_fields = create_valid_fields_dict(SecurityModel,name="sec")|create_valid_fields_dict(PositionModel,name="pos")
    print(valid_fields)

    window = MappingTool(mappings,valid_fields,"test.json",tool_tip_data=tooltip_html)
    window.resize(600, 300)
    window.show()
    sys.exit(app.exec_())

# $AND(?trade.broker=="SI"?,?trade.datetime > (*,*,*,8,50,0)?,?trade.datetime < (*,*,*,9,0,0)?,?trade.isin<>"DE"?)