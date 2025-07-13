import sys
import uuid
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTreeView, QMenu, QAction, QInputDialog,QMessageBox, QDialog, QVBoxLayout,QLabel,QDialogButtonBox
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, QPoint
import json

class MoveDialog(QDialog):
    def __init__(self, tree_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select an Item")
        self.resize(400, 300)

        self._selected_uid = None  # internal variable

        layout = QVBoxLayout(self)

        self.tree_view = QTreeView()
        layout.addWidget(self.tree_view)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept_selection)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Items"])
        self.tree_view.setModel(self.model)
        self.tree_view.setHeaderHidden(False)
        self.tree_view.setEditTriggers(QTreeView.NoEditTriggers)

        self.tree_data = tree_data
        self.uid_to_item = {}

        self.build_tree()

    def build_tree(self):
        # Create all items first
        for uid, data in self.tree_data.items():
            item = QStandardItem(data["label"])
            item.setData(uid, Qt.UserRole)
            item.setEditable(False)
            self.uid_to_item[uid] = item

        # Attach children to parents
        for uid, data in self.tree_data.items():
            parent_uid = data.get("parent_uid")
            item = self.uid_to_item[uid]
            if parent_uid and parent_uid in self.uid_to_item:
                self.uid_to_item[parent_uid].appendRow(item)
            else:
                self.model.appendRow(item)

        self.tree_view.expandAll()

    def accept_selection(self):
        index = self.tree_view.currentIndex()
        if index.isValid():
            self._selected_uid = index.data(Qt.UserRole)
        self.accept()

    def selected_uid(self):
        return self._selected_uid

class TreeApp(QMainWindow):
    def __init__(self,file_path):
        super().__init__()
        self.setWindowTitle("Tree with Context Menus")
        self.resize(500, 400)

        self.last_selected_uid = None

        self.tree_data = {}  # Your data dict



        self.model = QStandardItemModel()
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.open_context_menu)

        self.setCentralWidget(self.tree_view)

        if file_path:
            self.file_path = file_path
            self.load_tree_from_file()

        self.tree_view.selectionModel().currentChanged.connect(self.on_selection_changed)

    def on_selection_changed(self, current, previous):
        if current.isValid():
            self.last_selected_uid = current.data(Qt.UserRole)

    def open_context_menu(self, position: QPoint):
        index = self.tree_view.indexAt(position)

        menu = QMenu()

        if not index.isValid():
            add_action = QAction("Add New Item", self)
            add_action.triggered.connect(lambda: self.add_item(None))
            menu.addAction(add_action)
        else:
            rename_action = QAction("Rename", self)
            delete_action = QAction("Delete", self)
            new_sub_action = QAction("Create new Subitem", self)

            menu.addAction(rename_action)
            menu.addAction(delete_action)
            menu.addAction(new_sub_action)

            rename_action.triggered.connect(lambda: self.rename_item(index))
            delete_action.triggered.connect(lambda: self.delete_item(index))
            new_sub_action.triggered.connect(lambda: self.add_new_subitem(index))

            # inside open_context_menu()
            move_action = QAction("Move", self)
            menu.addAction(move_action)
            move_action.triggered.connect(lambda: self.move_item_dialog(index))

            # inside open_context_menu()
            duplicate_action = QAction("Duplicate", self)
            menu.addAction(duplicate_action)
            duplicate_action.triggered.connect(lambda: self.duplicate_item(index))


        menu.exec_(self.tree_view.viewport().mapToGlobal(position))

    # Placeholder method for adding a new item
    def add_item(self, parent_uid):
        uid = str(uuid.uuid4())

        # Set label and parent_uid properly
        self.tree_data[uid] = {"label": "New Item", "parent_uid": parent_uid}

        item = QStandardItem(self.tree_data[uid]["label"])
        item.setData(uid, Qt.UserRole)
        item.setEditable(False)

        if parent_uid is None:
            # Add as root item
            self.model.appendRow(item)
        else:
            parent_item = self.find_item_by_uid(parent_uid)
            if parent_item:
                parent_item.appendRow(item)
            else:
                # If parent not found, add as root (fallback)
                self.model.appendRow(item)

        self.save_tree_to_file()

    def load_tree_from_file(self):
        import json
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.tree_data = json.load(f)
            self.rebuild_tree_from_data()
        except Exception as e:
            print(f"Error loading tree: {e}")
    def save_tree_to_file(self):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.tree_data, f, indent=4)

    def duplicate_item(self, index):
        """Duplicate the selected item and its entire subtree,
        placing the copy under the same parent."""
        original_item = self.model.itemFromIndex(index)
        if original_item is None:
            return

        original_uid = original_item.data(Qt.UserRole)
        parent_uid = self.tree_data[original_uid].get("parent_uid")  # may be None

        def clone_subtree(source_uid, new_parent_uid):
            # -------- create copy of the source node ----------
            src_data = self.tree_data[source_uid]
            new_uid = str(uuid.uuid4())
            new_label = f"{src_data['label']} (copy)"

            # add to data dict
            self.tree_data[new_uid] = {
                "label": new_label,
                "parent_uid": new_parent_uid
            }

            # add to the visual tree
            new_item = QStandardItem(new_label)
            new_item.setData(new_uid, Qt.UserRole)
            new_item.setEditable(False)

            if new_parent_uid is None:
                self.model.appendRow(new_item)
            else:
                parent_item = self.find_item_by_uid(new_parent_uid)
                parent_item.appendRow(new_item)

            # -------- clone children safely ----------
            # take a snapshot of the *original* children list
            child_uids = [
                uid for uid, d in self.tree_data.items()
                if d.get("parent_uid") == source_uid
            ]
            for child_uid in child_uids:
                clone_subtree(child_uid, new_uid)

        clone_subtree(original_uid, parent_uid)
        self.save_tree_to_file()
    def add_new_subitem(self,index):
        item = self.model.itemFromIndex(index)
        parent_uid = item.data(Qt.UserRole)
        self.add_item(parent_uid)

    def move_item_dialog(self, index):
        try:
            item = self.model.itemFromIndex(index)
            source_uid = item.data(Qt.UserRole)
            print(555,source_uid)

            dlg = MoveDialog(self.tree_data,parent =self)
            if dlg.exec_() != QDialog.Accepted:
                return

            target_uid = dlg.selected_uid()
            print(target_uid)
            # None → user picked nothing; also allow moving to root if target is root
            if target_uid == source_uid:
                return  # no‑op

            # ----- re‑parent in the UI -----
            # 1. take the row from current parent
            parent_item = item.parent()
            row_data = parent_item.takeRow(item.row()) if parent_item else self.model.takeRow(item.row())

            # 2. append it to new parent (or root)
            if target_uid:
                new_parent_item = self.find_item_by_uid(target_uid)
                new_parent_item.appendRow(row_data)
            else:
                self.model.appendRow(row_data)

            # ----- update tree_data dict -----
            self.tree_data[source_uid]["parent_uid"] = target_uid
            self.save_tree_to_file()

            #TODO Change parent settings once there are parent settings to change
        except Exception as err:
            print (err)

    def rebuild_tree_from_data(self):
        self.model.clear()
        self.model.setHorizontalHeaderLabels(["Items"])

        uid_to_item = {}
        for uid, data in self.tree_data.items():
            item = QStandardItem(data["label"])
            item.setData(uid, Qt.UserRole)
            item.setEditable(False)
            uid_to_item[uid] = item

        for uid, data in self.tree_data.items():
            parent_uid = data.get("parent_uid")
            if parent_uid and parent_uid in uid_to_item:
                uid_to_item[parent_uid].appendRow(uid_to_item[uid])
            else:
                self.model.appendRow(uid_to_item[uid])

        QApplication.processEvents()  # Let the view catch up

        # Explicitly collapse root items
        root = self.model.invisibleRootItem()
        for row in range(root.rowCount()):
            idx = root.child(row).index()
            self.tree_view.collapse(idx)

        # Now expand the last selected path, if any
        if self.last_selected_uid and self.last_selected_uid in uid_to_item:
            target_item = uid_to_item[self.last_selected_uid]
            self._expand_path_to_item(target_item)
            idx = target_item.index()
            self.tree_view.setCurrentIndex(idx)
            self.tree_view.scrollTo(idx)

    def _expand_path_to_item(self, item):
        """Expand parents from root down to the given item."""
        idx = item.index()
        while idx.isValid():
            self.tree_view.expand(idx)
            idx = idx.parent()

        # if self.last_selected_uid and self.last_selected_uid in uid_to_item:
        #     print(888)
        #     target_item = uid_to_item[self.last_selected_uid]
        #     self.expand_path_to_uid(target_item)
        #     idx = target_item.index()
        #     self.tree_view.setCurrentIndex(idx)
        #     self.tree_view.scrollTo(idx)

    # Placeholder method for renaming an item
    def rename_item(self, index):
        item = self.model.itemFromIndex(index)
        uid = item.data(Qt.UserRole)
        current_name = item.text()

        new_name, ok = QInputDialog.getText(self, "Rename Item", "Enter new name:", text=current_name)
        if ok and new_name.strip():
            # Update the item text (UI)
            item.setText(new_name.strip())
            # Update your data dict
            if uid in self.tree_data:
                self.tree_data[uid]['label'] = new_name.strip()

        self.save_tree_to_file()
        # TODO: Implement renaming logic here

    # Placeholder method for deleting an item

    def delete_item(self, index):
        if not index.isValid():
            return

        item = self.model.itemFromIndex(index)
        uid = item.data(Qt.UserRole)

        # Show confirmation dialog
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this item and all descending subitems?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Recursive delete in data dict
            def recursive_delete(uid_to_delete):
                children_uids = [child_uid for child_uid, data in self.tree_data.items()
                                 if data.get("parent_uid") == uid_to_delete]
                for child_uid in children_uids:
                    recursive_delete(child_uid)
                if uid_to_delete in self.tree_data:
                    del self.tree_data[uid_to_delete]

            recursive_delete(uid)

            # Remove item from model
            parent = item.parent()
            if parent:
                parent.removeRow(item.row())
            else:
                self.model.removeRow(item.row())
        self.save_tree_to_file()


    def find_item_by_uid(self, uid):
        def search(parent):
            for row in range(parent.rowCount()):
                child = parent.child(row)
                if child.data(Qt.UserRole) == uid:
                    return child
                found = search(child)
                if found:
                    return found
            return None

        root = self.model.invisibleRootItem()
        return search(root)


def main():
    app = QApplication(sys.argv)
    window = TreeApp("tree_data.json")
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
