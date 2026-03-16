from typing import Any, Dict, List

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QFileDialog,
    QHeaderView,
    QLabel,
    QMainWindow,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QToolBar,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from view.DeleteDialog import DeleteDialog
from view.InputDialog import InputDialog
from model.Model import Model
from view.PaginationWidget import PaginationWidget
from view.SearchDialog import SearchDialog


class MainWindow(QMainWindow):
    add_record_signal = pyqtSignal(dict)
    delete_records_signal = pyqtSignal(dict)
    sort_records_signal = pyqtSignal(int, bool)
    load_db_signal = pyqtSignal(str)
    save_db_signal = pyqtSignal(str)
    load_xml_signal = pyqtSignal(str)
    save_xml_signal = pyqtSignal(str)
    page_changed_signal = pyqtSignal(int, int)

    def __init__(self, model: Model) -> None:
        super().__init__()
        self.setWindowTitle("Менеджер Записей")
        self.setGeometry(250, 200, 700, 400)
        self.model = model

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.create_actions()
        self.create_menu()
        self.create_toolbar()
        self.main_layout = QVBoxLayout(self.central_widget)

        self.tabs = QTabWidget()

        table_tab = QWidget()
        table_layout = QVBoxLayout(table_tab)

        self.table_widget = QTableWidget(0, 6)
        self.table_widget.setHorizontalHeaderLabels(
            [
                "ФИО студента",
                "Группа",
                "По болезни",
                "По др. причинам",
                "Без ув. причины",
                "Итого",
            ]
        )
        self.table_widget.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        )
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionsClickable(True)
        header.setSortIndicatorShown(True)
        header.sortIndicatorChanged.connect(self.sort_records)
        table_layout.addWidget(self.table_widget)

        self.pagination_widget = PaginationWidget()
        table_layout.addWidget(self.pagination_widget)

        self.tabs.addTab(table_tab, "Таблица")

        # --- ВКЛАДКА С ДЕРЕВОМ ---
        tree_tab = QWidget()
        tree_layout = QVBoxLayout(tree_tab)
        self.tree_widget = QTreeWidget()
        self.tree_widget.setColumnCount(2)
        self.tree_widget.setHeaderLabels(["Поле", "Значение"])
        self.tree_widget.header().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.tree_widget.header().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.tree_widget.setSortingEnabled(True)
        self.tree_widget.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        tree_layout.addWidget(self.tree_widget)
        self.tabs.addTab(tree_tab, "Дерево")

        self.main_layout.addWidget(QLabel("Текущие записи:"))
        self.main_layout.addWidget(self.tabs)

        self.pagination_widget.page_changed.connect(self.page_changed_signal.emit)

    def create_menu(self) -> None:
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Файл")

        load_db_action = QAction("Загрузить из БД", self)
        load_db_action.triggered.connect(self.action_load_db)
        file_menu.addAction(load_db_action)

        save_db_action = QAction("Сохранить в БД", self)
        save_db_action.triggered.connect(self.action_save_db)
        file_menu.addAction(save_db_action)

        file_menu.addSeparator()

        load_xml_action = QAction("Загрузить из XML", self)
        load_xml_action.triggered.connect(self.action_load_xml)
        file_menu.addAction(load_xml_action)

        save_xml_action = QAction("Сохранить в XML", self)
        save_xml_action.triggered.connect(self.action_save_xml)
        file_menu.addAction(save_xml_action)

        edit_menu = menubar.addMenu("Правка")
        edit_menu.addAction(self.add_action)
        edit_menu.addAction(self.search_action)
        edit_menu.addAction(self.delete_action)

    def create_toolbar(self) -> None:
        toolbar = QToolBar("Главная панель инструментов")
        self.addToolBar(toolbar)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        toolbar.addAction(self.add_action)
        toolbar.addAction(self.search_action)
        toolbar.addAction(self.delete_action)

    def create_actions(self) -> None:
        self.add_action = QAction("Добавить запись", self)
        self.add_action.triggered.connect(self.add_record)

        self.search_action = QAction("Найти записи", self)
        self.search_action.triggered.connect(self.open_search_dialog)

        self.delete_action = QAction("Удалить записи", self)
        self.delete_action.triggered.connect(self.open_delete_dialog)

    def action_load_db(self) -> None:
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Загрузить из БД", "", "SQLite DB (*.db *.sqlite);;Все файлы (*)"
        )
        if filepath:
            self.load_db_signal.emit(filepath)

    def action_save_db(self) -> None:
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Сохранить в БД", "", "SQLite DB (*.db *.sqlite);;Все файлы (*)"
        )
        if filepath:
            self.save_db_signal.emit(filepath)

    def action_load_xml(self) -> None:
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Загрузить из XML", "", "XML Файлы (*.xml);;Все файлы (*)"
        )
        if filepath:
            self.load_xml_signal.emit(filepath)

    def action_save_xml(self) -> None:
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Сохранить в XML", "", "XML Файлы (*.xml);;Все файлы (*)"
        )
        if filepath:
            self.save_xml_signal.emit(filepath)

    def add_record(self) -> None:
        dialog = InputDialog(self)
        if dialog.exec():
            self.add_record_signal.emit(dialog.get_record())

    def open_search_dialog(self) -> None:
        dialog = SearchDialog(self.model, self)
        dialog.exec()

    def open_delete_dialog(self) -> None:
        dialog = DeleteDialog(self)
        if dialog.exec():
            criteria = dialog.get_criteria()
            if criteria:
                self.delete_records_signal.emit(criteria)

    def set_total_records(self, count: int) -> None:
        self.pagination_widget.set_total_records(count)

    def update_tree_view(self, records: List[Dict[str, Any]]) -> None:
        self.tree_widget.setSortingEnabled(False)
        self.tree_widget.clear()
        for record in records:
            name = record.get("name", "Новая запись")
            record_item = QTreeWidgetItem(self.tree_widget, [name])

            QTreeWidgetItem(record_item, ["Группа", str(record.get("group", ""))])

            pass_item = QTreeWidgetItem(record_item, ["Число пропусков занятий за год"])
            QTreeWidgetItem(pass_item, ["По болезни", str(record.get("sick", 0))])
            QTreeWidgetItem(
                pass_item, ["По другим причинам", str(record.get("other", 0))]
            )
            QTreeWidgetItem(
                pass_item,
                ["Без уважительной причины", str(record.get("disrespectful", 0))],
            )
            QTreeWidgetItem(pass_item, ["Итого", str(record.get("total", 0))])
        self.tree_widget.setSortingEnabled(True)

    def sort_records(self, index: int, order: Qt.SortOrder) -> None:
        is_descending = order == Qt.SortOrder.DescendingOrder
        self.sort_records_signal.emit(index, is_descending)

    def update_table_view(self, records_to_display: List[Dict[str, Any]]) -> None:
        self.table_widget.setRowCount(0)

        for row_idx, record in enumerate(records_to_display):
            self.table_widget.insertRow(row_idx)
            self.table_widget.setItem(row_idx, 0, QTableWidgetItem(record["name"]))
            self.table_widget.setItem(row_idx, 1, QTableWidgetItem(record["group"]))

            sick_item = QTableWidgetItem()
            sick_item.setData(Qt.ItemDataRole.DisplayRole, record["sick"])
            self.table_widget.setItem(row_idx, 2, sick_item)

            other_item = QTableWidgetItem()
            other_item.setData(Qt.ItemDataRole.DisplayRole, record["other"])
            self.table_widget.setItem(row_idx, 3, other_item)

            disrespectful_item = QTableWidgetItem()
            disrespectful_item.setData(
                Qt.ItemDataRole.DisplayRole, record["disrespectful"]
            )
            self.table_widget.setItem(row_idx, 4, disrespectful_item)

            total_item = QTableWidgetItem()
            total_item.setData(Qt.ItemDataRole.DisplayRole, record["total"])
            self.table_widget.setItem(row_idx, 5, total_item)
