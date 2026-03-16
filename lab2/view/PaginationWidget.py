from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QWidget,
)


class PaginationWidget(QWidget):
    page_changed = pyqtSignal(int, int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.first_button = QPushButton("<<")
        self.first_button.setToolTip("Первая страница")
        self.previous_button = QPushButton("<")
        self.previous_button.setToolTip("Предыдущая страница")
        self.next_button = QPushButton(">")
        self.next_button.setToolTip("Следующая страница")
        self.last_button = QPushButton(">>")
        self.last_button.setToolTip("Последняя страница")

        self.page_size_label = QLabel("Записей на странице:")
        self.page_size_spinbox = QSpinBox()
        self.page_size_spinbox.setRange(5, 100)
        self.page_size_spinbox.setValue(10)
        self.page_size_spinbox.setSingleStep(5)

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setMinimumWidth(250)

        layout.addWidget(self.first_button)
        layout.addWidget(self.previous_button)
        layout.addStretch()
        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(self.page_size_label)
        layout.addWidget(self.page_size_spinbox)
        layout.addWidget(self.next_button)
        layout.addWidget(self.last_button)

        self.first_button.clicked.connect(self._on_first)
        self.previous_button.clicked.connect(self._on_prev)
        self.next_button.clicked.connect(self._on_next)
        self.last_button.clicked.connect(self._on_last)
        self.page_size_spinbox.valueChanged.connect(self._on_page_size_changed)

        self._total_records = 0
        self._current_page = 1

    def set_total_records(self, count: int) -> None:
        self._total_records = count
        self._current_page = 1
        self._update_ui()
        self._emit_page_change()

    def _on_page_size_changed(self) -> None:
        self._current_page = 1
        self._update_ui()
        self._emit_page_change()

    def _on_first(self) -> None:
        if self._current_page > 1:
            self._current_page = 1
            self._update_ui()
            self._emit_page_change()

    def _on_prev(self) -> None:
        if self._current_page > 1:
            self._current_page -= 1
            self._update_ui()
            self._emit_page_change()

    def _on_next(self) -> None:
        total_pages = self._get_total_pages()
        if self._current_page < total_pages:
            self._current_page += 1
            self._update_ui()
            self._emit_page_change()

    def _on_last(self) -> None:
        total_pages = self._get_total_pages()
        if self._current_page < total_pages:
            self._current_page = total_pages
            self._update_ui()
            self._emit_page_change()

    def _emit_page_change(self) -> None:
        page_size = self.page_size_spinbox.value()
        offset = (self._current_page - 1) * page_size
        self.page_changed.emit(offset, page_size)

    def _get_total_pages(self) -> int:
        page_size = self.page_size_spinbox.value()
        if self._total_records == 0 or page_size == 0:
            return 1
        return (self._total_records + page_size - 1) // page_size

    def _update_ui(self) -> None:
        page_size = self.page_size_spinbox.value()
        total_pages = self._get_total_pages()

        if self._total_records == 0:
            self.status_label.setText("Нет записей")
            self.first_button.setEnabled(False)
            self.previous_button.setEnabled(False)
            self.next_button.setEnabled(False)
            self.last_button.setEnabled(False)
            return

        self.first_button.setEnabled(self._current_page > 1)
        self.previous_button.setEnabled(self._current_page > 1)
        self.next_button.setEnabled(self._current_page < total_pages)
        self.last_button.setEnabled(self._current_page < total_pages)

        start_record = (self._current_page - 1) * page_size + 1
        end_record = min(self._current_page * page_size, self._total_records)

        status_text = (
            f"Страница: {self._current_page}/{total_pages} | "
            f"Записи: {start_record}-{end_record} из {self._total_records}"
        )
        self.status_label.setText(status_text)
