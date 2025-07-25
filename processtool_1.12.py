import sys
import uuid

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QStackedWidget, QGridLayout, QShortcut, QMessageBox
)
from PyQt5.QtGui import QFont, QMouseEvent, QKeySequence
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import (
    QWidget, QLabel, QListWidget, QPushButton,
    QVBoxLayout, QHBoxLayout, QListWidgetItem, QLineEdit, QDialog, QComboBox, QCheckBox, QScrollArea, QMenu, QAction, QColorDialog
)


from pymongo import MongoClient
from datetime import datetime
import ast

class SelectionDialog(QDialog):
    def __init__(self, items, parent=None, title="Select an Option", label="Choose one:"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.selected_item = None


        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(label))

        self.combo_box = QComboBox()
        # Populate combo with title as display, full dict as user data
        for key, value in items.items():
            self.combo_box.addItem(value.get("title", str(key)), value)

        layout.addWidget(self.combo_box)

        # Buttons
        button_layout = QHBoxLayout()
        confirm_button = QPushButton("Confirm")
        cancel_button = QPushButton("Cancel")
        button_layout.addWidget(confirm_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        confirm_button.clicked.connect(self.confirm)
        cancel_button.clicked.connect(self.reject)

    def confirm(self):
        self.selected_item = self.combo_box.currentData()
        self.accept()

    def get_selection(self):
        return self.selected_item


class RightClickableButton(QPushButton):
    def __init__(self,main,button_pos,load_color = None,load_id = None, text="", parent=None):
        super().__init__(text, parent)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.main = main
        self.color = None
        self.button_pos = button_pos
        if load_id:
            self.id = load_id
            self.update_button()
        else:
            self.id = None
        if load_color:
            self.color = load_color
            self.update_button()
        self.prior_id = None


    def show_context_menu(self, pos: QPoint):
        global_pos = self.mapToGlobal(pos)

        menu = QMenu(self)

        action_1 = QAction("Set Quicklink", self)
        action_1.triggered.connect(self.set_quicklink)

        action_2 = QAction("Custom Action 2", self)
        action_2.triggered.connect(self.get_color)

        menu.addAction(action_1)
        menu.addAction(action_2)

        menu.exec_(global_pos)

    def set_quicklink(self):
        try:
            if self.id:
                self.prior_id = self.id
            dialog = SelectionDialog(self.main.process_data,self.main, title="Pick Quicklink for button")
            if dialog.exec_() == QDialog.Accepted:
                self.id = dialog.get_selection()["process_id"]
                self.main.process_data[self.id]["button_position"] = self.button_pos
                self.color = None
                self.main.process_collection.update_one(
                    {"idkey": self.id},
                    {"$set": self.main.process_data[self.id]},
                    upsert=True
                )
                if self.prior_id:
                    del self.main.process_data[self.prior_id]["button_position"]
                    del self.main.process_data[self.prior_id]["button_color"]
                    self.main.process_collection.update_many(
                        {"idkey": self.prior_id},
                        {"$unset": {"button_position": "", "button_color": ""}}
                    )
                self.update_button()


            else:
                print("Cancelled")
        except Exception as err:
            print(err)

    def get_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.color = color.name()
            self.update_button()
            self.main.process_data[self.id]["button_color"] = self.color
            self.main.process_collection.update_one(
                {"idkey": self.id},
                {"$set": self.main.process_data[self.id]},
                upsert=True
            )
            return None  # Returns color as hex string, e.g. "#ff0000"
        return None

    def update_button(self):
        self.setText(self.main.process_data[self.id]["title"])
        self.setStyleSheet(f"background-color: {self.color}")
        try:
            self.clicked.disconnect()
        except TypeError:
            # no connections were present
            pass
        self.clicked.connect(lambda: self.main.run_process(self.id))


        #self.layout()


# --- Sub-check widget with simple QCheckBox ---
class Subcheck(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QVBoxLayout(self)

        # Horizontal layout: checkbox + label
        top_row = QHBoxLayout()
        self.check_box = QCheckBox()
        self.check_box.setFixedSize(20, 20)
        self.check_box.stateChanged.connect(self.notify_parent)
        top_row.addWidget(self.check_box)

        self.check_label = QLabel("Check item:")
        self.check_label.setStyleSheet("font-size: 14pt;")
        self.check_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        top_row.addWidget(self.check_label)

        top_row.addStretch()
        main_layout.addLayout(top_row)

        # Optional comment input
        self.comment_input = QLineEdit()
        self.comment_input.setPlaceholderText("Optional comment")
        main_layout.addWidget(self.comment_input)



    def notify_parent(self):
        if self.parent() and hasattr(self.parent(), "evaluate_progress"):
            self.parent().evaluate_progress()

    def get_data(self):
        return {
            "text": self.check_label.text(),
            "checked": self.check_box.isChecked(),
            "comment": self.comment_input.text().strip()
        }

    def is_valid(self):
        return self.check_box.isChecked()

    def set_check_text(self, text):
        self.check_label.setText(text)
        self.check_box.setChecked(False)
        self.comment_input.clear()

# --- Checklist Manager Widget ---
class ChecklistManagerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Checklist Manager")
        self.setMinimumSize(400, 500)
        self.checks = []

        self.layout = QVBoxLayout(self)

        self.check_label = QLabel("Check item:")
        self.check_label.setAlignment(Qt.AlignCenter)
        self.check_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        self.layout.addWidget(self.check_label)

        # Input to add new check
        add_layout = QHBoxLayout()
        self.check_input = QLineEdit()
        self.check_input.setPlaceholderText("Enter new check...")
        self.add_button = QPushButton("Add Check")
        self.add_button.clicked.connect(self.add_check)
        add_layout.addWidget(self.check_input)
        add_layout.addWidget(self.add_button)
        self.layout.addLayout(add_layout)

        # Scroll area for added checks
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.checks_container = QWidget()
        self.checks_layout = QVBoxLayout(self.checks_container)
        self.scroll_area.setWidget(self.checks_container)
        self.layout.addWidget(self.scroll_area)

        # --- Add shortcuts ---
        focus_shortcut = QShortcut(QKeySequence("Alt+A"), self)
        focus_shortcut.activated.connect(self.check_input.setFocus)

        confirm_shortcut = QShortcut(QKeySequence("Alt+Return"), self)
        confirm_shortcut.activated.connect(self.add_check)

    def add_check(self):
        text = self.check_input.text().strip()
        if not text:
            return

        widget = Subcheck(self.checks_container)
        widget.set_check_text(text)
        self.checks_layout.addWidget(widget)
        self.checks.append(widget)
        self.check_input.clear()

        self.is_valid()

    def is_valid(self):
        if not self.checks:
            return True
        else:
            return all(check.is_valid() for check in self.checks)

    def get_data(self):
        return [check.get_data() for check in self.checks]


    def set_check_text(self, text):
        self.check_label.setText(text)

    def reset(self):
        # Remove all Subcheck widgets from the layout and UI
        for check in self.checks:
            check.setParent(None)
            check.deleteLater()

        # Clear the list tracking the widgets
        self.checks.clear()

        # Clear input field text
        self.check_input.clear()

        # Optional: update the layout to refresh UI
        self.checks_layout.update()






#TODO neuer fenster bestandteil, wo man die einzelnen
#TODO Final View machen, wo alles zusammengefasst wird und eine möglichkeit für ein Exitbriefing gegeben wird

class DoubleClickCheckButton(QPushButton):
    def __init__(self, text=""):
        super().__init__(text)
        self.setCheckable(True)
        self.setMinimumHeight(80)
        self.setStyleSheet("background-color: none")

    def mousePressEvent(self, event: QMouseEvent):
        # Prevent single clicks from toggling
        event.ignore()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        # Only toggle on double-click
        self.setChecked(not self.isChecked())
        self.update_style()

    def update_style(self):
        if self.isChecked():
            self.setStyleSheet("background-color: lightgreen")
        else:
            self.setStyleSheet("background-color: none")
class QuestionStepWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.question_label = QLabel("Question goes here")
        self.question_label.setAlignment(Qt.AlignCenter)
        self.question_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        layout.addWidget(self.question_label)

        self.answer_input = QLineEdit()
        self.answer_input.setPlaceholderText("Your answer (required)")
        layout.addWidget(self.answer_input)

        self.comment_input = QLineEdit()
        self.comment_input.setPlaceholderText("Optional comment")
        layout.addWidget(self.comment_input)

        self.answer_input.setFocus()

    def get_data(self):
        return {
            "answer": self.answer_input.text().strip(),
            "comment": self.comment_input.text().strip()
        }

    def is_valid(self):
        return bool(self.answer_input.text().strip())

    def set_question_text(self, text):
        self.question_label.setText(text)
        self.answer_input.clear()
        self.comment_input.clear()

class CheckStepWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.check_label = QLabel("Check item:")
        self.check_label.setAlignment(Qt.AlignCenter)
        self.check_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        layout.addWidget(self.check_label)

        self.check_button = DoubleClickCheckButton("Check Off")
        layout.addWidget(self.check_button)

        self.comment_input = QLineEdit()
        self.comment_input.setPlaceholderText("Optional comment")
        layout.addWidget(self.comment_input)

        # Ctrl + Space shortcut to toggle check
        toggle_shortcut = QShortcut(QKeySequence("Ctrl+Space"), self)
        toggle_shortcut.activated.connect(self.toggle_check_button)

    def toggle_check_button(self):
        self.check_button.setChecked(not self.check_button.isChecked())
        self.check_button.update_style()

    def get_data(self):
        return {
            "checked": self.check_button.isChecked(),
            "comment": self.comment_input.text().strip()
        }

    def is_valid(self):
        return self.check_button.isChecked()

    def set_check_text(self, text):
        self.check_label.setText(text)
        self.check_button.setChecked(False)
        self.check_button.update_style()
        self.comment_input.clear()



class RunProcessWidget(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main
        self.process_id = None
        self.current_index = 0
        self.process_data = None
        self.process_tracking = None
        self.step_widgets = {}

        self.layout = QVBoxLayout(self)

        self.title_label = QLabel("Run Process")
        self.title_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.title_label)

        self.sub_label = QLabel("Step will show here")
        self.sub_label.setFont(QFont("Arial", 12))
        self.sub_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.sub_label)

        # Container for step type widgets
        self.step_container = QStackedWidget()
        self.layout.addWidget(self.step_container)

        # Initialize step types
        self.widgets_by_type = {
            "question": QuestionStepWidget(),
            "check": CheckStepWidget(),
            "subcheck": ChecklistManagerWidget()
        }

        for w in self.widgets_by_type.values():
            self.step_container.addWidget(w)

        # Navigation buttons
        nav_layout = QHBoxLayout()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_process)
        nav_layout.addWidget(self.cancel_button)

        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(self.go_back)
        nav_layout.addWidget(self.back_button)

        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.go_next_or_finish)
        nav_layout.addWidget(self.next_button)

        next_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        next_shortcut.activated.connect(self.next_button.click)

        prev_shortcut = QShortcut(QKeySequence("Ctrl+Backspace"), self)
        prev_shortcut.activated.connect(self.back_button.click)

        self.layout.addLayout(nav_layout)

    def update_view(self):
        if not self.process_data or self.current_index >= len(self.process_data["sub_process_data"]):
            return

        current_step = self.process_data["sub_process_data"][self.current_index]
        step_type = current_step["type"]
        text = current_step.get("text", "No text")

        self.sub_label.setText(f"Step {self.current_index + 1} of {len(self.process_data['sub_process_data'])}")

        widget = self.widgets_by_type.get(step_type)
        if widget:
            if step_type == "question":
                widget.set_question_text(text)
            elif step_type == "check":
                widget.set_check_text(text)
            elif step_type == "subcheck":
                widget.set_check_text(text)
                widget.reset()

            self.step_container.setCurrentWidget(widget)

    def go_next_or_finish(self):
        current_step = self.process_data["sub_process_data"][self.current_index]
        widget = self.widgets_by_type.get(current_step["type"])

        if not widget or not widget.is_valid():
            print("Invalid input for this step.")
            return

        # Save response
        self.process_tracking.setdefault("responses", []).append({
            "step": self.current_index,
            "type": current_step["type"],
            "data": widget.get_data()
        })

        self.current_index += 1
        if self.current_index < len(self.process_data["sub_process_data"]):
            self.update_view()
        else:
            self.process_tracking["status"] = "Completed"
            self.process_tracking["end_time"] = datetime.now()
            self.main.answer_collection.insert_one(self.process_tracking)
            self.main.stacked.setCurrentWidget(self.main.grid_widget)

    def go_back(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.update_view()

    def cancel_process(self):
        self.process_tracking["status"] = "Cancelled"
        self.process_tracking["end_time"] = datetime.now()
        self.main.answer_collection.insert_one(self.process_tracking)
        self.process_tracking = None
        self.process_id = None
        self.main.stacked.setCurrentWidget(self.main.grid_widget)

    def start_process(self, process_data):
        self.process_data = process_data
        self.process_tracking = {
            "start_time": datetime.now(),
            "title": process_data["title"],
            "responses": []
        }
        self.current_index = 0
        self.update_view()
class MainGridWidget(QWidget):
    def __init__(self,main):
        super().__init__()
        self.layout = QGridLayout(self)
        self.main = main
        self.populate_grid()

    def populate_grid(self):
        print(self.main.process_data)
        for i in range(5):
            for j in range(5):
                button_id = None  # Reset at the start of each grid cell
                color = None
                for key, subdict in self.main.process_data.items():
                    if subdict.get("button_position") == [i, j]:
                        button_id = key
                        color = subdict.get("button_color")
                        break  # Stop after finding the first match

                button = RightClickableButton(self.main, (i, j), load_color=color, load_id = button_id)
                self.layout.addWidget(button, i, j)


class AddSubDialog(QDialog):
    def __init__(self, parent=None,edit = None):
        super().__init__(parent)
        self.setWindowTitle("Add New Sub")
        self.setModal(True)
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)

        # Type selection
        layout.addWidget(QLabel("Sub Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["question", "check","subcheck"])
        layout.addWidget(self.type_combo)

        # Text input
        layout.addWidget(QLabel("Text:"))
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Enter sub-process text...")
        if edit:
            self.text_input.setText(edit["text"])

        layout.addWidget(self.text_input)

        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        # Connect signals
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.ok_button.setEnabled(False)

        self.text_input.textChanged.connect(self.validate_input)

    def validate_input(self):
        self.ok_button.setEnabled(bool(self.text_input.text().strip()))

    def get_data(self):
        return {
            "type": self.type_combo.currentText(),
            "text": self.text_input.text().strip()
        }


class EditProcessesWidget(QWidget):
    def __init__(self, main):
        super().__init__()

        self.main = main

        # Main layout
        main_layout = QVBoxLayout(self)

        # Header label styled as a header
        header = QLabel("Edit Processes View")
        header.setFont(QFont("Arial", 16, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)

        # Horizontal layout: list on left, buttons on right
        content_layout = QHBoxLayout()

        # Left side: process list (single-select)
        self.process_list = QListWidget()
        self.process_list.setSelectionMode(QListWidget.SingleSelection)
        for key in self.main.process_data.keys():
            list_item = QListWidgetItem(self.main.process_data[key]["title"])  # show only the title
            list_item.setData(Qt.UserRole, key)  # store full dict
            self.process_list.addItem(list_item)
        content_layout.addWidget(self.process_list)

        # Right side: buttons
        button_layout = QVBoxLayout()

        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.run_process)
        button_layout.addWidget(self.run_button)

        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.add_process)
        button_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(self.edit_process)
        button_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_process)
        button_layout.addWidget(self.delete_button)

        content_layout.addLayout(button_layout)

        # Add content to main layout
        main_layout.addLayout(content_layout)

    # === Button Handlers ===
    def run_process(self):
        selected_item = self.process_list.currentItem()
        if selected_item is None:
            QMessageBox.warning(self, "No Selection", "Please select a process to run.")
            return

        process_id = selected_item.data(Qt.UserRole)
        self.main.run_process(process_id)

    def add_process(self):
        try:
            self.main.stacked.setCurrentWidget(self.main.new_widget)
            self.main.new_widget.process_id = str(uuid.uuid4())
            self.main.process_data[self.main.new_widget.process_id] = {"process_id":self.main.new_widget.process_id,"title":"new process","sub_process_data":[]}
            print(self.main.process_data)
        except Exception as err:
            print(888, str(err))

    def edit_process(self):

        selected_item = self.process_list.currentItem()
        process_id = selected_item.data(Qt.UserRole)
        self.process_id = process_id
        self.main.new_widget.process_id = self.process_id
        self.main.stacked.setCurrentWidget(self.main.new_widget)
        self.main.new_widget.title_input.setText(self.main.process_data[self.process_id]["title"])
        self.main.new_widget.subs_list.clear()
        for entry in self.main.process_data[self.process_id]["sub_process_data"]:
            self.main.new_widget.subs_list.addItem(str(entry))

        if not self.process_id:
            print("No process selected for editing.")
            return

        # Get the stored process ID from the item




    def delete_process(self):
        print("Delete")

class NewProcessWidget(QWidget):
    def __init__(self, main):
        super().__init__()

        if not hasattr(self, 'process_id'):
            self.process_id = None

        self.main = main  # reference to main window

        main_layout = QVBoxLayout(self)

        # Header
        self.header = QLabel("New Process View")
        self.header.setFont(QFont("Arial", 16, QFont.Bold))
        self.header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.header)

        # Title input + confirm button in a row
        title_row = QHBoxLayout()
        title_label = QLabel("Title:")
        self.title_input = QLineEdit()
        confirm_title_button = QPushButton("Confirm Title")
        confirm_title_button.clicked.connect(self.confirm_title)
        title_row.addWidget(title_label)
        title_row.addWidget(self.title_input)
        title_row.addWidget(confirm_title_button)
        main_layout.addLayout(title_row)

        # Horizontal layout: subs list on left, buttons on right
        content_layout = QHBoxLayout()

        # Sub-processes list
        subs_layout = QVBoxLayout()
        subs_label = QLabel("Sub-Processes:")
        subs_layout.addWidget(subs_label)

        self.subs_list = QListWidget()
        self.subs_list.setSelectionMode(QListWidget.SingleSelection)
        subs_layout.addWidget(self.subs_list)
        content_layout.addLayout(subs_layout)

        # Buttons layout (vertical)
        button_layout = QVBoxLayout()
        buttons = [
            ("Add", self.add_clicked),
            ("Edit", self.edit_clicked),
            ("Delete", self.delete_clicked),
            ("Up", self.up_clicked),
            ("Down", self.down_clicked),
        ]

        for text, handler in buttons:
            btn = QPushButton(text)
            btn.clicked.connect(handler)
            button_layout.addWidget(btn)

        button_layout.addStretch()  # push buttons to top
        content_layout.addLayout(button_layout)

        main_layout.addLayout(content_layout)

        # Bottom buttons: Cancel and Confirm
        bottom_buttons_layout = QHBoxLayout()
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.cancel_clicked)
        bottom_buttons_layout.addWidget(cancel_button)

        confirm_button = QPushButton("Confirm")
        confirm_button.clicked.connect(self.confirm_clicked)
        bottom_buttons_layout.addWidget(confirm_button)

        main_layout.addLayout(bottom_buttons_layout)

    # Button handlers (just print labels)

    def confirm_title(self):
        title = self.title_input.text()
        self.header.setText(title if title else "New Process View")
        self.main.process_data[self.process_id]["title"] = title
        self.main.save_process_to_mdb(self.process_id)

    def add_clicked(self):
        dialog = AddSubDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            self.main.process_data[self.process_id]["sub_process_data"].append(data)
            self.main.save_process_to_mdb(self.process_id)
            # self.temp["questions"] = self.temp["questions"] + [data]
            self.subs_list.clear()
            for entry in self.main.process_data[self.process_id]["sub_process_data"]:
                 self.subs_list.addItem(str(entry))

    def edit_clicked(self):
        selected_item = self.subs_list.currentItem()
        selected_index = self.subs_list.currentRow()
        d = ast.literal_eval(selected_item.text())
        dialog = AddSubDialog(self,edit = d)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            self.main.process_data[self.process_id]["sub_process_data"][selected_index] = data
            self.main.save_process_to_mdb(self.process_id)
            self.subs_list.clear()
            for entry in self.main.process_data[self.process_id]["sub_process_data"]:
                 self.subs_list.addItem(str(entry))



    def delete_clicked(self):
        print("Delete")

    def up_clicked(self):
        try:
            index = self.subs_list.currentRow()
            if index > 0:
                data = self.main.process_data[self.process_id]["sub_process_data"]
                data[index - 1], data[index] = data[index], data[index - 1]
                self.main.save_process_to_mdb(self.process_id)
                self.refresh_subs_list()
                self.subs_list.setCurrentRow(index - 1)
        except Exception as err:
            print(str(err))

    def down_clicked(self):
        index = self.subs_list.currentRow()
        data = self.main.process_data[self.process_id]["sub_process_data"]
        if 0 <= index < len(data) - 1:
            data[index + 1], data[index] = data[index], data[index + 1]
            self.main.save_process_to_mdb(self.process_id)
            self.refresh_subs_list()
            self.subs_list.setCurrentRow(index + 1)

    def refresh_subs_list(self):
        self.subs_list.clear()
        for entry in self.main.process_data[self.process_id]["sub_process_data"]:
            self.subs_list.addItem(str(entry))

    def cancel_clicked(self):
        # Switch back to edit processes widget
        self.main.stacked.setCurrentWidget(self.main.edit_widget)

        # Reset UI in NewProcessWidget
        self.main.new_widget.title_input.clear()
        self.main.new_widget.header.setText("New Process View")
        self.main.new_widget.subs_list.clear()

    def delete_clicked(self):
        selected_index = self.subs_list.currentRow()
        if selected_index >= 0:
            del self.main.process_data[self.process_id]["sub_process_data"][selected_index]
            self.main.save_process_to_mdb(self.process_id)
            self.subs_list.takeItem(selected_index)

    def confirm_clicked(self):
        title = self.title_input.text()
        subs = [self.subs_list.item(i).text() for i in range(self.subs_list.count())]

        print(f"Saving process with title: {title}")
        print("Sub-processes:", subs)

        self.main.edit_widget.process_list.clear()
        for key in self.main.process_data.keys():
            list_item = QListWidgetItem(self.main.process_data[key]["title"])  # show only the title
            list_item.setData(Qt.UserRole, key)  # store full dict
            self.main.edit_widget.process_list.addItem(list_item)

        # Reset UI in NewProcessWidget
        self.main.new_widget.title_input.clear()
        self.main.new_widget.header.setText("New Process View")
        self.main.new_widget.subs_list.clear()

        # Switch back to edit processes widget
        self.main.stacked.setCurrentWidget(self.main.edit_widget)
        self.main.save_process_to_mdb(self.process_id)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Process Manager")
        self.resize(800, 600)

        main_layout = QVBoxLayout(self)

        # init mongo connection
        client = MongoClient()
        db = client["process_tool"]
        self.answer_collection = db["processes_completed"]
        self.answer_collection.insert_one({"title":"connection","time":datetime.now()})
        self.process_collection = db["processes"]

        self.process_data = {
            doc["idkey"]: doc
            for doc in self.process_collection.find()
            if "idkey" in doc  # optional safety check
        }

        # Top buttons (only 3 now)
        button_layout = QHBoxLayout()
        self.run_button = QPushButton("Run")
        self.grid_button = QPushButton("Main Grid")
        self.edit_button = QPushButton("Edit Processes")

        for btn in (self.grid_button, self.edit_button):
            button_layout.addWidget(btn)

        main_layout.addLayout(button_layout)

        # Stacked widget setup
        self.stacked = QStackedWidget()
        self.run_widget = RunProcessWidget(self)
        self.grid_widget = MainGridWidget(self)
        self.edit_widget = EditProcessesWidget(self)
        self.new_widget = NewProcessWidget(self)  # Still available if needed

        self.stacked.addWidget(self.run_widget)
        self.stacked.addWidget(self.grid_widget)
        self.stacked.addWidget(self.edit_widget)
        self.stacked.addWidget(self.new_widget)

        main_layout.addWidget(self.stacked)

        # Connect buttons to view changes
        self.run_button.clicked.connect(lambda: self.stacked.setCurrentWidget(self.run_widget))
        self.grid_button.clicked.connect(lambda: self.stacked.setCurrentWidget(self.grid_widget))
        self.edit_button.clicked.connect(lambda: self.stacked.setCurrentWidget(self.edit_widget))

        # Default view
        self.stacked.setCurrentWidget(self.grid_widget)

    def save_process_to_mdb(self, id):
        self.process_collection.update_one(
            {"idkey": id},
            {"$set": self.process_data[id]},
            upsert=True
        )

    def run_process(self,id):
        #print(22,self.process_data[id])
        self.stacked.setCurrentWidget(self.run_widget)
        self.run_widget.start_process(self.process_data[id])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())