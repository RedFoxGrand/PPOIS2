from typing import Any, Dict

from PyQt6.QtWidgets import QMessageBox

from view.MainWindow import MainWindow
from model.Model import Model


class Controller:
    def __init__(self, model: Model, view: MainWindow) -> None:
        self.model = model
        self.view = view

        self.view.add_record_signal.connect(self.model.add_record)
        self.view.delete_records_signal.connect(self.delete_records)
        self.view.sort_records_signal.connect(self.model.sort_records)
        self.view.load_db_signal.connect(self.load_db)
        self.view.save_db_signal.connect(self.save_db)
        self.view.load_xml_signal.connect(self.load_xml)
        self.view.save_xml_signal.connect(self.save_xml)
        self.view.page_changed_signal.connect(self.update_view)

        self.model.data_changed.connect(self.on_data_changed)

        self.on_data_changed()

    def delete_records(self, criteria: Dict[str, Any]) -> None:
        deleted = self.model.delete_records(criteria)
        if deleted > 0:
            QMessageBox.information(
                self.view, "Результат", f"Успешно удалено записей: {deleted}"
            )
        else:
            QMessageBox.information(
                self.view, "Результат", "По заданным условиям записей не найдено."
            )

    def load_db(self, filepath: str) -> None:
        try:
            self.model.load_from_db(filepath)
            QMessageBox.information(
                self.view, "Успех", "Записи успешно загружены из БД."
            )
        except Exception as e:
            QMessageBox.critical(
                self.view, "Ошибка", f"Не удалось загрузить из БД: {e}"
            )

    def save_db(self, filepath: str) -> None:
        try:
            self.model.save_to_db(filepath)
            QMessageBox.information(
                self.view, "Успех", "Записи успешно сохранены в БД."
            )
        except Exception as e:
            QMessageBox.critical(self.view, "Ошибка", f"Не удалось сохранить в БД: {e}")

    def load_xml(self, filepath: str) -> None:
        try:
            self.model.load_from_xml(filepath)
            QMessageBox.information(
                self.view, "Успех", "Записи успешно загружены из XML."
            )
        except Exception as e:
            QMessageBox.critical(
                self.view, "Ошибка", f"Не удалось загрузить из XML: {e}"
            )

    def save_xml(self, filepath: str) -> None:
        try:
            self.model.save_to_xml(filepath)
            QMessageBox.information(
                self.view, "Успех", "Записи успешно сохранены в XML."
            )
        except Exception as e:
            QMessageBox.critical(
                self.view, "Ошибка", f"Не удалось сохранить в XML: {e}"
            )

    def on_data_changed(self) -> None:
        total_records = self.model.get_total_count()
        self.view.set_total_records(total_records)
        all_records = self.model.get_all_records()
        self.view.update_tree_view(all_records)

    def update_view(self, offset: int, limit: int) -> None:
        records = self.model.get_paged_records(offset, limit)
        self.view.update_table_view(records)
