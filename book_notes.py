import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QDateEdit, QTextEdit, QLineEdit, QPushButton, QGridLayout, QSpinBox, QDialog, QAction, QLabel, QListWidget,QDialogButtonBox, QInputDialog,QMessageBox,
QListWidgetItem, QAbstractItemView, QCompleter
)
from PyQt5.QtCore import Qt
from pymongo import MongoClient
import uuid

class TagsDialog(QDialog):
    def __init__(self,main, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Tags")

        self.main = main

        # Main layout
        main_layout = QVBoxLayout(self)

        # Header label
        header_label = QLabel("Tags")
        header_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        main_layout.addWidget(header_label)

        # Row layout with list widget and buttons
        row_layout = QHBoxLayout()

        # Tag list
        self.tag_list = QListWidget()
        self.tag_list.setSelectionMode(QAbstractItemView.SingleSelection)

        row_layout.addWidget(self.tag_list, 2)

        # Button layout (Add, Edit, Delete)
        button_layout = QVBoxLayout()
        self.add_button = QPushButton("Add")
        self.edit_button = QPushButton("Edit")
        self.delete_button = QPushButton("Delete")
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()
        row_layout.addLayout(button_layout, 1)

        main_layout.addLayout(row_layout)

        # Confirm and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        # Connect button signals
        self.add_button.clicked.connect(self.add_tag)
        self.edit_button.clicked.connect(self.edit_tag)
        self.load_tags()

    def add_tag(self):
        text, ok = QInputDialog.getText(self, "Add Tag", "Enter tag name:")
        if ok and text:
            self.main.tags_col.insert_one({"id":str(uuid.uuid4()),"title":text})

        self.load_tags()

    def edit_tag(self):
        selected_items = self.tag_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a tag to edit.")
            return

        item = selected_items[0]
        current_title = item.text()
        tag_id = item.data(Qt.UserRole)

        # Show input dialog with current title pre-filled
        text, ok = QInputDialog.getText(self, "Edit Tag", "Edit tag name:", text=current_title)
        if ok and text:
            # Update in MongoDB
            self.main.tags_col.update_one({"id": tag_id}, {"$set": {"title": text}})
            # Update display
            item.setText(text)

            self.load_tags()


    def load_tags(self):
        self.main.update_tags()
        self.tag_list.clear()

        for tag in self.main.tags:
            item = QListWidgetItem(tag["title"])  # Visible text
            item.setData(Qt.UserRole, tag["id"])  # Internal data (you can use this to retrieve the id later)
            self.tag_list.addItem(item)


class AddBookDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Book")

        # Layouts
        layout = QVBoxLayout(self)

        # Title input
        title_layout = QHBoxLayout()
        title_label = QLabel("Title:")
        self.title_input = QLineEdit()
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.title_input)
        layout.addLayout(title_layout)

        # Author input
        author_layout = QHBoxLayout()
        author_label = QLabel("Name:")
        self.author_input = QLineEdit()
        author_layout.addWidget(author_label)
        author_layout.addWidget(self.author_input)
        fn_author_label = QLabel("First Name:")
        self.fn_author_input = QLineEdit()
        author_layout.addWidget(fn_author_label)
        author_layout.addWidget(self.fn_author_input)
        layout.addLayout(author_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.ok_button = QPushButton("Add Book")
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        layout.addLayout(button_layout)

    def get_data(self):
        return {
            "title": self.title_input.text().strip(),
            "author": self.author_input.text().strip(),
            "first_name": self.fn_author_input.text().strip(),
            "book_id": str(uuid.uuid4())

        }
class ButtonPanel(QWidget):
    def __init__(self,main):
        super().__init__()
        layout = QVBoxLayout()
        self.main = main

        # 5 rows of buttons (1 per row, you can adjust for more per row)
        for i in range(5):
            row = QHBoxLayout()
            for j in range(3):  # 3 buttons per row for example
                btn = QPushButton(f"Button {i * 3 + j + 1}")
                row.addWidget(btn)
            layout.addLayout(row)

        # Input line below the buttons
        self.input_line = QLineEdit()
        layout.addWidget(self.input_line)

        completer = QCompleter([item["title"] for item in self.main.tags])
        self.input_line.setCompleter(completer)


        self.setLayout(layout)


class MainView(QMainWindow):
    def __init__(self):
        self.client = MongoClient("mongodb://localhost:27017/")
        self.db = self.client["booknotes"]
        self.books_collection = self.db["sources"]
        self.tags_col = self.db["tags"]


        super().__init__()
        self.setWindowTitle("Main View Layout")
        self.setMinimumSize(600, 500)

        self.update_tags()

        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        # Row 1: ComboBox + Date toggler
        row1 = QHBoxLayout()
        self.combo = QComboBox()
        self.combo.addItems(["Item 1", "Item 2", "Item 3"])

        row1.addWidget(self.combo)
        self.number_toggle = QSpinBox()
        self.number_toggle.setMinimum(-100)
        self.number_toggle.setMaximum(1000)
        self.number_toggle.setValue(1)  # default value
        row1.addWidget(self.number_toggle)
        main_layout.addLayout(row1)

        # Row 2: First multi-line input (5 lines)
        self.input1 = QTextEdit()
        self.input1.setFixedHeight(100)
        self.input1.setPlaceholderText("Enter source text here...")

        main_layout.addWidget(self.input1)

        # Row 3: Second multi-line input (5 lines)
        self.input2 = QTextEdit()
        self.input2.setFixedHeight(100)
        self.input2.setPlaceholderText("Enter comment here...")
        main_layout.addWidget(self.input2)

        # Row 4: Button panel with 5 rows of buttons + input line
        self.button_panel = ButtonPanel(self)
        main_layout.addWidget(self.button_panel)

        # Row 5: Clear, Next, Finish buttons
        row5 = QHBoxLayout()
        self.clear_btn = QPushButton("Clear")
        self.next_btn = QPushButton("Next")
        self.finish_btn = QPushButton("Finish")
        row5.addWidget(self.clear_btn)
        row5.addWidget(self.next_btn)
        row5.addWidget(self.finish_btn)
        main_layout.addLayout(row5)

        self.setCentralWidget(central_widget)

        # Menu Bar
        menubar = self.menuBar()
        sources_menu = menubar.addMenu("Sources")
        tags_menu = menubar.addMenu("Tags")

        create_tag_action = QAction("Manage Tags", self)
        create_tag_action.triggered.connect(self.open_tag_dialog)
        tags_menu.addAction(create_tag_action)

        create_source_action = QAction("Create Source", self)
        create_source_action.triggered.connect(self.open_add_book_dialog)
        sources_menu.addAction(create_source_action)

        self.update_items()


    def update_items(self):
        self.combo.clear()
        books = list(self.books_collection.find())
        for book in books:
            display_text = f"{book['author']}, {book['first_name']} - {book['title']}"
            self.combo.addItem(display_text, book["book_id"])

    def open_tag_dialog(self):
        dialog = TagsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            print("yes")


    def open_add_book_dialog(self):
        dialog = AddBookDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            book = dialog.get_data()
            query = {"author": book["author"], "title": book["title"]}

            # Data to insert/update
            update_data = book

            # Use upsert=True to insert if not found
            result = self.books_collection.update_one(
                query,
                {"$set": update_data},
                upsert=True
            )

            if result.matched_count > 0:
                print("Existing book updated.")
            else:
                print("New book inserted.")

            # Here you could insert into DB or update a list view

    def update_tags(self):
        self.tags = list(self.tags_col.find({}))

    #def new_book_note(self):
    #    self.book

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainView()
    window.show()
    sys.exit(app.exec_())
