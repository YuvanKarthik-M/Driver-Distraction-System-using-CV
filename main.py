import sys

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


app = QApplication(sys.argv)

with open("ui/styles.qss", "r") as file:
    app.setStyleSheet(file.read())

window = MainWindow()
window.show()

sys.exit(app.exec())