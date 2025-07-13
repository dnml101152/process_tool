import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QDateEdit, QTextEdit, QLineEdit, QPushButton, QGridLayout, QSpinBox, QDialog, QAction, QLabel, QListWidget,QDialogButtonBox, QInputDialog,QMessageBox,
QListWidgetItem, QAbstractItemView, QCompleter, QShortcut,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from pymongo import MongoClient
import uuid
from PATH import uri
from bson import ObjectId
import random

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
        self._id = None  # <-- this line
        self.book_title = None
        self.book_id = None
        self.book_author = None
        self.book_tags = []
        self.book_tags_id = []
        self.source_text = None
        self.comment_text = None
        self.page = None


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

        self.used_ids = set()  # Tracks which tag IDs are currently added
        self.title_to_id = {}
        self.id_to_title = {}
        self.tag_docs = tag_docs

        if not isinstance(tag_docs, list):
            raise ValueError("tag_docs must be a list of tag dictionaries.")

        self.build_title_to_id_keys()

        # Main layout container
        self.layout = QVBoxLayout(self)

        # Horizontal container for tags and input + tag list
        self.top_layout = QHBoxLayout()
        self.layout.addLayout(self.top_layout)

        # Layout for tag widgets (horizontally arranged)
        self.tags_layout = QHBoxLayout()
        self.top_layout.addLayout(self.tags_layout, stretch=3)

        # Vertical container for input and scrollable tag list
        self.right_panel_layout = QVBoxLayout()
        self.top_layout.addLayout(self.right_panel_layout, stretch=2)

        # Line edit for user to type tag titles
        self.input = QLineEdit()
        self.input.setPlaceholderText("Select a tag title")
        self.right_panel_layout.addWidget(self.input)

        # QCompleter for autocomplete suggestions based on known tag titles
        self.completer = QCompleter(sorted(self.title_to_id.keys()))
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.input.setCompleter(self.completer)

        # Scrollable list of all available tags
        self.tag_list = QListWidget()
        self.tag_list.setFixedHeight(150)  # Adjust height as needed
        self.right_panel_layout.addWidget(self.tag_list)

        self.populate_tag_list()

        # Connect return key to attempt to add tag from input
        self.input.returnPressed.connect(self.add_tag_from_input)

        # Connect clicking a tag in the list to add it
        self.tag_list.itemClicked.connect(self.add_tag_from_list)

    def build_title_to_id_keys(self):
        try:
            self.title_to_id = {
                doc["title"]: doc["id"] for doc in self.tag_docs
                if isinstance(doc, dict) and "title" in doc and "id" in doc
            }
            self.id_to_title = {
                doc["id"]: doc["title"] for doc in self.tag_docs
                if isinstance(doc, dict) and "title" in doc and "id" in doc
            }
        except Exception as e:
            raise ValueError(f"Failed to process tag_docs: {e}")

    def populate_tag_list(self):
        self.tag_list.clear()
        for title in sorted(self.title_to_id.keys()):
            item = QListWidgetItem(title)
            self.tag_list.addItem(item)

    def add_tag_from_input(self):
        title = self.input.text().strip()
        self.input.clear()

        if not title:
            print("No tag entered.")
            return

        tag_id = self.title_to_id.get(title)
        if tag_id is None:
            print(f"Tag '{title}' not found in available tags.")
            return

        if tag_id in self.used_ids:
            print(f"Tag '{title}' is already added.")
            return

        self.add_tag(title, tag_id)

    def add_tag_from_list(self, item):
        title = item.text()
        tag_id = self.title_to_id.get(title)
        if tag_id is None:
            print(f"Tag '{title}' not found in available tags.")
            return

        if tag_id in self.used_ids:
            print(f"Tag '{title}' is already added.")
            return

        self.add_tag(title, tag_id)

    def add_tag(self, title, tag_id):
        if not isinstance(title, str) or not isinstance(tag_id, str):
            print(f"Invalid tag data: title={title!r}, id={tag_id!r}")
            return

        if tag_id in self.used_ids:
            print(f"Tag '{title}' (ID: {tag_id}) is already in use.")
            return

        try:
            tag_widget = TagWidget(title, self.remove_tag)
            self.tags_layout.addWidget(tag_widget)
            self.used_ids.add(tag_id)
            print(f"Added tag: '{title}' (ID: {tag_id})")
        except Exception as e:
            print(f"Failed to add tag '{title}': {e}")

    def remove_tag(self, title):
        tag_id = self.title_to_id.get(title)
        if tag_id is None:
            print(f"Warning: Attempted to remove unknown tag title: '{title}'")
            return

        for i in reversed(range(self.tags_layout.count())):
            item = self.tags_layout.itemAt(i)
            if item is None:
                continue
            widget = item.widget()
            if widget is None:
                continue
            if isinstance(widget, TagWidget) and widget.label.text() == title:
                self.tags_layout.removeWidget(widget)
                widget.deleteLater()
                self.used_ids.discard(tag_id)
                print(f"Removed tag: '{title}' (ID: {tag_id})")
                break
        else:
            print(f"Warning: Tag widget for title '{title}' not found in layout.")

    def get_selected_tag_ids(self):
        return list(self.used_ids)

    def clear_tags(self):
        for i in reversed(range(self.tags_layout.count())):
            item = self.tags_layout.itemAt(i)
            if item is None:
                continue
            widget = item.widget()
            if widget is None:
                continue
            try:
                self.tags_layout.removeWidget(widget)
                widget.deleteLater()
            except Exception as e:
                print(f"Error while removing tag widget: {e}")

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
        self.uri = uri

        self.client = MongoClient(self.uri)
        self.db = self.client["booknotes"]
        self.books_collection = self.db["sources"]
        self.tags_col = self.db["tags"]
        self.notes_col = self.db["notes"]

        self.current_note = Booknote()


        super().__init__()
        self.setWindowTitle("Main View Layout")
        self.setMinimumSize(600, 500)


        self.update_tags()



        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        # Row 1: ComboBox + Date toggler
        row1 = QHBoxLayout()
        self.source_combo = QComboBox()
        self.source_combo.addItems(["Item 1", "Item 2", "Item 3"])

        row1.addWidget(self.source_combo)
        self.page_toggle = QSpinBox()
        self.page_toggle.setMinimum(-100)
        self.page_toggle.setMaximum(1000)
        self.page_toggle.setValue(1)  # default value
        row1.addWidget(self.page_toggle)
        main_layout.addLayout(row1)

        # Row 2: First multi-line input (5 lines)
        self.input_source_text = QTextEdit()
        self.input_source_text.setFixedHeight(100)
        self.input_source_text.setPlaceholderText("Enter source text here...")

        main_layout.addWidget(self.input_source_text)

        # Row 3: Second multi-line input (5 lines)
        self.input_comment_text = QTextEdit()
        self.input_comment_text.setFixedHeight(100)
        self.input_comment_text.setPlaceholderText("Enter comment here...")
        main_layout.addWidget(self.input_comment_text)

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
        edit_menu = menubar.addMenu("Edit")


        create_tag_action = QAction("Manage Tags", self)
        create_tag_action.triggered.connect(self.open_tag_dialog)
        tags_menu.addAction(create_tag_action)

        create_source_action = QAction("Create Source", self)
        create_source_action.triggered.connect(self.open_add_book_dialog)
        sources_menu.addAction(create_source_action)

        edit_note_action = QAction("Edit Note", self)
        edit_note_action.triggered.connect(self.prompt_note_selection)
        edit_menu.addAction(edit_note_action)

        random_untagged_action = QAction("Edit Random Untagged Note", self)
        random_untagged_action.setShortcut("Ctrl+R")  # ← this line adds the shortcut
        random_untagged_action.triggered.connect(self.load_random_untagged_note)
        edit_menu.addAction(random_untagged_action)


        self.next_btn.clicked.connect(self.next_clicked)


        self.update_items()

    def load_note_for_editing(self, note_id):
        note_doc = self.notes_col.find_one({"_id": ObjectId(note_id)})
        if not note_doc:
            print(f"[ERROR] Note with ID {note_id} not found.")
            return

        self.current_note = Booknote()
        self.current_note._id = note_doc["_id"]
        self.current_note.book_id = note_doc.get("book_id")
        self.current_note.page = note_doc.get("page")
        self.current_note.book_tags_id = note_doc.get("book_tags_id", [])
        self.current_note.source_text = note_doc.get("source_text", "")
        self.current_note.comment_text = note_doc.get("comment_text", "")

        # Set UI fields
        self.input_source_text.setPlainText(self.current_note.source_text)
        self.input_comment_text.setPlainText(self.current_note.comment_text)
        self.page_toggle.setValue(self.current_note.page or 0)

        # Set the correct book in the combo box
        index = self.source_combo.findData(self.current_note.book_id)
        if index >= 0:
            self.source_combo.setCurrentIndex(index)

        # Load tags into TagEditor
        self.tag_widget.clear_tags()
        self.update_tags()  # refresh tag list
        self.tag_widget.tag_docs = self.tags  # update tag editor with latest tags
        self.tag_widget.build_title_to_id_keys()  # rebuild ID maps

        for tag_id in self.current_note.book_tags_id:
            title = self.tag_widget.id_to_title.get(tag_id)
            if title:
                self.tag_widget.add_tag(title, tag_id)

    def next_clicked(self):
        """
        Triggered when the 'Next' button is clicked.
        Saves the current note, resets input fields, and initializes a new blank Booknote.
        """

        try:
            # Attempt to save the current note
            self.save_book_note()
        except Exception as e:
            print(f"[ERROR] Failed to save book note: {e}")

        # Clear input fields safely
        try:
            if hasattr(self, 'input_source_text') and self.input_source_text:
                self.input_source_text.clear()

            if hasattr(self, 'input_comment_text') and self.input_comment_text:
                self.input_comment_text.clear()
        except Exception as e:
            print(f"[ERROR] Failed to clear text inputs: {e}")

        # Clear tags in tag widget
        try:
            if hasattr(self, 'tag_widget') and self.tag_widget:
                self.tag_widget.clear_tags()
        except Exception as e:
            print(f"[ERROR] Failed to clear tags: {e}")

        # Reset current_note to a new blank instance
        try:
            self.current_note = Booknote()
        except Exception as e:
            print(f"[ERROR] Failed to initialize new Booknote: {e}")

        try:
            self.page_toggle.setFocus()
        except Exception as e:
            print(f"[ERROR] Failed to focus number toggler: {e}")



    def update_tags(self):
        self.tags = list(self.tags_col.find())

    def save_book_note(self):
        if not self.current_note:
            print("[ERROR] No current note set. Aborting save.")
            return

        try:
            self.current_note.book_tags_id = self.tag_widget.get_selected_tag_ids() or []

            id_to_title = {doc["id"]: doc["title"] for doc in self.tags}
            self.current_note.book_tags = [id_to_title.get(tid, "Unknown ID") for tid in self.current_note.book_tags_id]

            self.current_note.book_id = self.source_combo.currentData()

            book_doc = self.books_collection.find_one({"book_id": self.current_note.book_id})
            self.current_note.book_title = book_doc.get("title", "Unknown Title") if book_doc else "Unknown Title"
            last = book_doc.get("author", "Doe") if book_doc else "Doe"
            first = book_doc.get("first_name", "John") if book_doc else "John"
            self.current_note.book_author = f"{last}, {first}"

            self.current_note.source_text = self.input_source_text.toPlainText()
            self.current_note.comment_text = self.input_comment_text.toPlainText()
            self.current_note.page = self.page_toggle.value()

            note_doc = {
                'book_title': self.current_note.book_title,
                'book_id': self.current_note.book_id,
                'book_author': self.current_note.book_author,
                'book_tags': self.current_note.book_tags,
                'book_tags_id': self.current_note.book_tags_id,
                'source_text': self.current_note.source_text,
                'comment_text': self.current_note.comment_text,
                'page': self.current_note.page
            }

            if self.current_note._id:
                self.notes_col.update_one({"_id": self.current_note._id}, {"$set": note_doc})
                print(f"Updated note with ID {self.current_note._id}")
            else:
                result = self.notes_col.insert_one(note_doc)
                self.current_note._id = result.inserted_id
                print(f"Inserted new note with ID {result.inserted_id}")

            self.tag_widget.clear_tags()

        except Exception as e:
            print(f"[ERROR] Exception occurred while saving book note: {e}")
    def update_items(self):
        self.source_combo.clear()
        books = list(self.books_collection.find())
        for book in books:
            display_text = f"{book['author']}, {book['first_name']} - {book['title']}"
            self.source_combo.addItem(display_text, book["book_id"])

    def open_tag_dialog(self):
        dlg = TagsDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            self.update_tags()
            self.tag_widget.tag_docs = self.tags
            self.tag_widget.build_title_to_id_keys()
            self.tag_widget.populate_tag_list()
            self.tag_widget.completer = QCompleter(sorted(self.tag_widget.title_to_id.keys()))
            self.tag_widget.input.setCompleter(self.tag_widget.completer)

    def prompt_note_selection(self):
        notes = list(self.notes_col.find().sort("book_title"))

        items = [f"{n.get('book_title', 'Untitled')} — Pg {n.get('page', '?')} (ID: {str(n['_id'])})" for n in notes]
        item, ok = QInputDialog.getItem(self, "Select Note", "Choose a note to edit:", items, 0, False)

        if ok and item:
            # Extract ID from the item string
            note_id = item.split("ID: ")[-1].strip(")")
            self.load_note_for_editing(note_id)

    def load_random_untagged_note(self):
        untagged_notes = list(self.notes_col.find({
            "$or": [
                {"book_tags_id": {"$exists": False}},
                {"book_tags_id": {"$size": 0}}
            ]
        }))

        if not untagged_notes:
            print("[INFO] No untagged notes found.")
            return

        random_note = random.choice(untagged_notes)
        self.load_note_for_editing(str(random_note["_id"]))

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

            self.update_items()

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
