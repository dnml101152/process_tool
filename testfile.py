from PyQt5.QtWidgets import QApplication, QListWidget, QListWidgetItem, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt

app = QApplication([])

window = QWidget()
layout = QVBoxLayout()
list_widget = QListWidget()

def add_group(list_widget, group_title, items):
    # Add group title (disabled, styled)
    header = QListWidgetItem(group_title)
    header.setFlags(Qt.ItemIsEnabled)  # not selectable
    header.setForeground(Qt.gray)
    header.setBackground(Qt.lightGray)
    header.setTextAlignment(Qt.AlignCenter)
    list_widget.addItem(header)

    # Add group items
    for text in items:
        item = QListWidgetItem("  " + text)  # optional indent
        list_widget.addItem(item)


# Add groups
add_group(list_widget, "Fruits", ["Apple", "Banana", "Orange"])
add_group(list_widget, "Vegetables", ["Carrot", "Broccoli", "Spinach"])
add_group(list_widget, "Drinks", ["Water", "Soda", "Juice"])

layout.addWidget(list_widget)
window.setLayout(layout)
window.setWindowTitle("Grouped QListWidget")
window.show()

app.exec_()
