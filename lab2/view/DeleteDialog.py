from typing import Any, Dict, Optional

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class DeleteDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Удаление записей")
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        tab1 = QWidget()
        layout1 = QFormLayout(tab1)
        self.tab1_group = QLineEdit()
        self.tab1_name = QLineEdit()
        layout1.addRow("Номер группы:", self.tab1_group)
        layout1.addRow("ИЛИ Фамилия:", self.tab1_name)
        self.tabs.addTab(tab1, "Группа или фамилия")

        tab2 = QWidget()
        layout2 = QFormLayout(tab2)
        self.tab2_name = QLineEdit()
        self.tab2_type = QComboBox()
        self.tab2_type.addItem("По болезни", "sick")
        self.tab2_type.addItem("По другим причинам", "other")
        self.tab2_type.addItem("Без уважительной причины", "disrespectful")
        self.tab2_type.addItem("Итого", "total")
        layout2.addRow("Фамилия:", self.tab2_name)
        layout2.addRow("Вид пропуска (>0):", self.tab2_type)
        self.tabs.addTab(tab2, "Фамилия или вид")

        tab3 = QWidget()
        layout3 = QFormLayout(tab3)
        self.tab3_name = QLineEdit()
        self.tab3_type = QComboBox()
        self.tab3_type.addItem("По болезни", "sick")
        self.tab3_type.addItem("По другим причинам", "other")
        self.tab3_type.addItem("Без уважительной причины", "disrespectful")
        self.tab3_type.addItem("Итого", "total")
        self.tab3_min = QSpinBox()
        self.tab3_min.setRange(0, 100)
        self.tab3_max = QSpinBox()
        self.tab3_max.setRange(0, 100)
        self.tab3_max.setValue(10)
        layout3.addRow("Фамилия:", self.tab3_name)
        layout3.addRow("Вид пропуска:", self.tab3_type)
        layout3.addRow("От (мин):", self.tab3_min)
        layout3.addRow("До (макс):", self.tab3_max)
        self.tabs.addTab(tab3, "Фамилия или количество")

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.criteria = None

    def accept(self) -> None:
        tab_index = self.tabs.currentIndex()
        criteria = {"type": tab_index + 1}

        if tab_index == 0:
            group = self.tab1_group.text().strip().lower()
            name = self.tab1_name.text().strip().lower()
            if not group and not name:
                QMessageBox.warning(self, "Ошибка", "Введите группу или фамилию.")
                return
            criteria["group"] = group
            criteria["name"] = name

        elif tab_index == 1:
            criteria["name"] = self.tab2_name.text().strip().lower()
            criteria["pass_type"] = self.tab2_type.currentData()

        elif tab_index == 2:
            min_val = self.tab3_min.value()
            max_val = self.tab3_max.value()
            if min_val > max_val:
                QMessageBox.warning(
                    self,
                    "Ошибка",
                    "Минимальное значение не может быть больше максимального.",
                )
                return

            criteria["name"] = self.tab3_name.text().strip().lower()
            criteria["pass_type"] = self.tab3_type.currentData()
            criteria["min"] = min_val
            criteria["max"] = max_val

        self.criteria = criteria
        super().accept()

    def get_criteria(self) -> Optional[Dict[str, Any]]:
        return self.criteria
