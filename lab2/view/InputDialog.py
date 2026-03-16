from typing import Any, Dict, Optional

from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QWidget,
)


class InputDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Добавить новую запись")
        layout = QFormLayout(self)

        letter_regex = QRegularExpression(r"^[a-zA-Zа-яА-ЯёЁ\s\-]+$")
        letter_validator = QRegularExpressionValidator(letter_regex)

        self.name_input = QLineEdit(self)
        self.name_input.setValidator(letter_validator)
        layout.addRow("ФИО студента:", self.name_input)

        self.group_input = QLineEdit(self)
        layout.addRow("Группа:", self.group_input)

        self.sick_input = QSpinBox(self)
        self.sick_input.setRange(0, 30)
        layout.addRow("По болезни:", self.sick_input)

        self.other_input = QSpinBox(self)
        self.other_input.setRange(0, 30)
        layout.addRow("По другим причинам:", self.other_input)

        self.disrespectful_input = QSpinBox(self)
        self.disrespectful_input.setRange(0, 30)
        layout.addRow("Без уважительной причины:", self.disrespectful_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    def accept(self) -> None:
        name = self.name_input.text().strip()
        group = self.group_input.text().strip()

        if not name or not group:
            QMessageBox.warning(
                self,
                "Ошибка ввода",
                "Пожалуйста, корректно заполните все поля!\nФИО и Группа обязательны.",
            )
            return

        super().accept()

    def get_record(self) -> Dict[str, Any]:
        return {
            "name": self.name_input.text().strip(),
            "group": self.group_input.text().strip(),
            "sick": self.sick_input.value(),
            "other": self.other_input.value(),
            "disrespectful": self.disrespectful_input.value(),
        }
