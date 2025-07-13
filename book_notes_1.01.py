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

class Booknote():
    def __init__(self):
        self.book_title = None
        self.book_id = None
        self.book_author = None
        self.book_tags = []
        self.book_tags_id = []

    def add_tag(self,tag_name, tag_id):
        self.book_tags.append(tag_name)
        self.book_tags_id.append(id)


class TagWidget(QWidget):
    def __init__(self, title, remove_callback):
        super().__init__()

        # Validate input types
        if not isinstance(title, str):
            raise TypeError(f"TagWidget title must be a string, got: {type(title).__name__}")
        if not callable(remove_callback):
            raise TypeError("remove_callback must be a callable function.")

        # Create horizontal layout
        layout = QHBoxLayout(self)

        # Label showing the tag title
        self.label = QLabel(title)

        # Small "x" button to remove the tag
        self.remove_btn = QPushButton("x")
        self.remove_btn.setFixedSize(16, 16)

        # Add widgets to layout
        layout.addWidget(self.label)
        layout.addWidget(self.remove_btn)

        # Fine-tune spacing and margins for compact appearance
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)

        # Apply basic styling to the tag widget
        self.setStyleSheet("background-color: lightgray; border-radius: 5px; padding: 2px;")

        try:
            # Connect the remove button to the callback
            self.remove_btn.clicked.connect(lambda: remove_callback(title))
        except Exception as e:
            print(f"Failed to connect remove button for tag '{title}': {e}")


class TagEditor(QWidget):
    def __init__(self, main, tag_docs):
        super().__init__()

        # Initialize internal state
        self.used_ids = set()  # Tracks which tag IDs are currently added
        self.title_to_id = {}
        self.id_to_title = {}

        # Validate input tag_docs: must be a list of dicts with 'title' and 'id'
        if not isinstance(tag_docs, list):
            raise ValueError("tag_docs must be a list of tag dictionaries.")
        try:
            # Build fast lookup dictionaries
            self.title_to_id = {
                doc["title"]: doc["id"] for doc in tag_docs
                if isinstance(doc, dict) and "title" in doc and "id" in doc
            }
            self.id_to_title = {
                doc["id"]: doc["title"] for doc in tag_docs
                if isinstance(doc, dict) and "title" in doc and "id" in doc
            }
        except Exception as e:
            raise ValueError(f"Failed to process tag_docs: {e}")

        # Main layout container
        self.layout = QVBoxLayout(self)

        # Layout for tag widgets (horizontally arranged)
        self.tags_layout = QHBoxLayout()
        self.layout.addLayout(self.tags_layout)

        # Line edit for user to type tag titles
        self.input = QLineEdit()
        self.input.setPlaceholderText("Select a tag title")
        self.layout.addWidget(self.input)

        # QCompleter for autocomplete suggestions based on known tag titles
        self.completer = QCompleter(sorted(self.title_to_id.keys()))
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.input.setCompleter(self.completer)

        # Connect return key to attempt to add tag
        self.input.returnPressed.connect(self.add_tag_from_input)

    def add_tag_from_input(self):

        # Get and sanitize user input
        title = self.input.text().strip()

        # Clear the input field regardless of result
        self.input.clear()

        # Ignore empty input
        if not title:
            print("No tag entered.")
            return

        # Look up the tag ID from the entered title
        tag_id = self.title_to_id.get(title)

        # If the title doesn't match any known tag, log and exit
        if tag_id is None:
            print(f"Tag '{title}' not found in available tags.")
            return

        # Prevent adding duplicate tags
        if tag_id in self.used_ids:
            print(f"Tag '{title}' is already added.")
            return

        # Try to add the tag widget and track usage
        try:
            self.add_tag(title, tag_id)
        except Exception as e:
            # Catch unexpected errors during widget creation
            print(f"Error adding tag '{title}': {e}")

    def add_tag(self, title, tag_id):
        # Validate input types
        if not isinstance(title, str) or not isinstance(tag_id, str):
            print(f"Invalid tag data: title={title!r}, id={tag_id!r}")
            return

        # Prevent adding duplicate tags
        if tag_id in self.used_ids:
            print(f"Tag '{title}' (ID: {tag_id}) is already in use.")
            return

        try:
            # Create the tag widget and connect it to the removal callback
            tag_widget = TagWidget(title, self.remove_tag)

            # Add the widget to the horizontal layout
            self.tags_layout.addWidget(tag_widget)

            # Track this tag ID as used
            self.used_ids.add(tag_id)

            print(f"Added tag: '{title}' (ID: {tag_id})")
        except Exception as e:
            # Catch any unexpected error (e.g., widget creation issues)
            print(f"Failed to add tag '{title}': {e}")

    def remove_tag(self, title):
        # Attempt to get the tag ID from the title
        tag_id = self.title_to_id.get(title)

        # If the title is unknown, abort safely
        if tag_id is None:
            print(f"Warning: Attempted to remove unknown tag title: '{title}'")
            return

        # Search the layout in reverse to find and remove the correct widget
        for i in reversed(range(self.tags_layout.count())):
            item = self.tags_layout.itemAt(i)
            if item is None:
                continue

            widget = item.widget()
            if widget is None:
                continue

            # Identify the TagWidget matching the title
            if isinstance(widget, TagWidget) and widget.label.text() == title:
                # Remove the widget from the layout and delete it
                self.tags_layout.removeWidget(widget)
                widget.deleteLater()

                # Remove tag ID from the used set (safe discard)
                self.used_ids.discard(tag_id)
                print(f"Removed tag: '{title}' (ID: {tag_id})")
                break
        else:
            # Reached if no matching widget was found
            print(f"Warning: Tag widget for title '{title}' not found in layout.")

    def get_selected_tag_ids(self):
        return list(self.used_ids)

    def clear_tags(self):
        # Iterate through all tag widgets in reverse order to safely remove them
        for i in reversed(range(self.tags_layout.count())):
            item = self.tags_layout.itemAt(i)
            if item is None:
                continue  # Skip if item is unexpectedly None

            widget = item.widget()
            if widget is None:
                continue  # Skip if widget is unexpectedly None

            try:
                # Remove the widget from the layout
                self.tags_layout.removeWidget(widget)
                # Schedule the widget for deletion to free memory
                widget.deleteLater()
            except Exception as e:
                # Log any unexpected issue during removal
                print(f"Error while removing tag widget: {e}")

        # Clear the internal record of used tag IDs
        self.used_ids.clear()
        print("All tags cleared.")


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


        self.current_note = Booknote()


        super().__init__()
        self.setWindowTitle("Main View Layout")
        self.setMinimumSize(600, 500)

        self.update_tags()
        print(self.tags)


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
        #self.button_panel = ButtonPanel(self)
        self.tag_widget = TagEditor(self,self.tags)
        main_layout.addWidget(self.tag_widget )

        # Row 5: Clear, Next, Finish buttons
        row5 = QHBoxLayout()
        self.clear_btn = QPushButton("Clear")
        self.next_btn = QPushButton("Next")
        #self.finish_btn = QPushButton("Finish")
        row5.addWidget(self.clear_btn)
        row5.addWidget(self.next_btn)
        #row5.addWidget(self.finish_btn)
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

        self.next_btn.clicked.connect(self.next_clicked)


        self.update_items()

    def next_clicked(self):

        # If current note is not set return
        if not hasattr(self, "current_note") or self.current_note is None:
            print("Error: No current note set.")
            return

        #clear note 1 and 2
        self.input1.clear()
        self.input2.clear()

        #get selected ids or fallback to empty list to ensure stability
        self.current_note.book_tags_id  = self.tag_widget.get_selected_tag_ids() or []

        # Create a lookup dictionary
        id_to_title = {
            doc["id"]: doc["title"]
            for doc in (self.tags or [])
            if isinstance(doc, dict) and "id" in doc and "title" in doc
        }

        # Get titles for IDs in xyz
        self.current_note.book_tags = [id_to_title.get(tag_id, "Unknown ID") for tag_id in self.current_note.book_tags_id]

        self.tag_widget.clear_tags()



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
