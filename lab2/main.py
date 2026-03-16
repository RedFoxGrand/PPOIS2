import sys

from PyQt6.QtWidgets import QApplication

from controller.Controller import Controller
from view.MainWindow import MainWindow
from model.Model import Model

if __name__ == "__main__":
    app = QApplication(sys.argv)
    model = Model()
    main_win = MainWindow(model)
    controller = Controller(model, main_win)
    main_win.show()
    sys.exit(app.exec())
