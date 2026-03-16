from typing import Any, Dict, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHeaderView,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from model.Model import Model
from view.PaginationWidget import PaginationWidget


class SearchDialog(QDialog):
    def __init__(self, model: Model, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.model = model
        self.setWindowTitle("Поиск записей")
        self.setGeometry(250, 200, 700, 400)
        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        tab1 = QWidget()
        layout1 = QFormLayout(tab1)
        self.tab1_group = QLineEdit()
        self.tab1_name = QLineEdit()
        layout1.addRow("Номер группы:", self.tab1_group)
        layout1.addRow("Фамилия:", self.tab1_name)
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

        self.search_button = QPushButton("Найти")
        self.search_button.clicked.connect(self.perform_search)
        layout.addWidget(self.search_button)

        self.pagination_widget = PaginationWidget()
        layout.addWidget(self.pagination_widget)

        self.results_table = QTableWidget(0, 6)
        self.results_table.setHorizontalHeaderLabels(
            [
                "ФИО студента",
                "Группа",
                "По болезни",
                "По другим причинам",
                "Без уваж. причины",
                "Итого",
            ]
        )
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionsClickable(True)
        header.setSortIndicatorShown(True)
        header.sortIndicatorChanged.connect(self.sort_results)
        layout.addWidget(self.results_table)

        self.search_results = []
        self.pagination_widget.page_changed.connect(self.update_results_view)

    def get_criteria(self) -> Optional[Dict[str, Any]]:
        tab_index = self.tabs.currentIndex()
        criteria = {"type": tab_index + 1}

        if tab_index == 0:
            criteria["group"] = self.tab1_group.text().strip().lower()
            criteria["name"] = self.tab1_name.text().strip().lower()
            if not criteria["group"] and not criteria["name"]:
                QMessageBox.warning(
                    self, "Ошибка", "Введите номер группы или фамилию для поиска."
                )
                return None

        elif tab_index == 1:
            criteria["name"] = self.tab2_name.text().strip().lower()
            criteria["pass_type"] = self.tab2_type.currentData()

        elif tab_index == 2:
            criteria["name"] = self.tab3_name.text().strip().lower()
            criteria["pass_type"] = self.tab3_type.currentData()
            criteria["min"] = self.tab3_min.value()
            criteria["max"] = self.tab3_max.value()
            if criteria["min"] > criteria["max"]:
                QMessageBox.warning(
                    self,
                    "Ошибка",
                    "Минимальное значение не может быть больше максимального.",
                )
                return None

        return criteria

    def perform_search(self) -> None:
        criteria = self.get_criteria()
        if criteria:
            self.search_results = self.model.search_records(criteria)
            self.pagination_widget.set_total_records(len(self.search_results))
            if not self.search_results:
                QMessageBox.information(
                    self, "Результат", "По заданным условиям записей не найдено."
                )

    def sort_results(self, index: int, order: Qt.SortOrder) -> None:
        keys = {
            0: "name",
            1: "group",
            2: "sick",
            3: "other",
            4: "disrespectful",
            5: "total",
        }
        if index not in keys:
            return

        is_descending = order == Qt.SortOrder.DescendingOrder
        self.search_results.sort(key=lambda x: x[keys[index]], reverse=is_descending)

        self.pagination_widget._emit_page_change()

    def update_results_view(self, offset: int, limit: int) -> None:
        self.results_table.setRowCount(0)
        records_to_display = self.search_results[offset : offset + limit]

        for row_idx, record in enumerate(records_to_display):
            self.results_table.insertRow(row_idx)
            self.results_table.setItem(row_idx, 0, QTableWidgetItem(record["name"]))
            self.results_table.setItem(row_idx, 1, QTableWidgetItem(record["group"]))

            sick_item = QTableWidgetItem()
            sick_item.setData(Qt.ItemDataRole.DisplayRole, record["sick"])
            self.results_table.setItem(row_idx, 2, sick_item)

            other_item = QTableWidgetItem()
            other_item.setData(Qt.ItemDataRole.DisplayRole, record["other"])
            self.results_table.setItem(row_idx, 3, other_item)

            disrespectful_item = QTableWidgetItem()
            disrespectful_item.setData(
                Qt.ItemDataRole.DisplayRole, record["disrespectful"]
            )
            self.results_table.setItem(row_idx, 4, disrespectful_item)

            total_item = QTableWidgetItem()
            total_item.setData(Qt.ItemDataRole.DisplayRole, record["total"])
            self.results_table.setItem(row_idx, 5, total_item)
