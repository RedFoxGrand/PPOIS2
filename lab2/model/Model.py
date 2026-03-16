import sqlite3
import xml.sax
from typing import Any, Dict, List, Optional, Tuple

from faker import Faker
from PyQt6.QtCore import QObject, pyqtSignal

from model.RecordHandler import RecordHandler


class Model(QObject):
    data_changed = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.connection = sqlite3.connect("students.db")
        self.connection.create_function(
            "LOWERCASE", 1, lambda x: str(x).lower() if x is not None else None
        )
        self.cursor = self.connection.cursor()
        self._sort_column = "name"
        self._sort_order = "ASC"
        self._create_table()
        self._generate_fake_data()

    def _create_table(self) -> None:
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                "group" TEXT,
                sick INTEGER,
                other INTEGER,
                disrespectful INTEGER,
                total INTEGER
            )
        """
        )
        self.connection.commit()

    def _generate_fake_data(self) -> None:
        fake = Faker("ru_RU")
        self.cursor.execute("SELECT COUNT(*) FROM records")
        if self.cursor.fetchone()[0] == 0:
            groups = ["ИИ-1", "ИИ-2", "ИИ-3", "ИИ-4", "ИИ-5"]
            for _ in range(50):
                self.add_record(
                    {
                        "name": fake.name(),
                        "group": fake.random_element(groups),
                        "sick": fake.random_int(0, 30),
                        "other": fake.random_int(0, 30),
                        "disrespectful": fake.random_int(0, 30),
                    },
                    emit_signal=False,
                )
            self.connection.commit()

    def add_record(self, record: Dict[str, Any], emit_signal: bool = True) -> None:
        total = record["sick"] + record["other"] + record["disrespectful"]
        self.cursor.execute(
            'INSERT INTO records (name, "group", sick, other, disrespectful, total) VALUES (?, ?, ?, ?, ?, ?)',
            (
                record["name"],
                record["group"],
                record["sick"],
                record["other"],
                record["disrespectful"],
                total,
            ),
        )
        self.connection.commit()
        if emit_signal:
            self.data_changed.emit()

    def _find_by_conditions(
        self, criteria: Optional[Dict[str, Any]]
    ) -> Tuple[str, tuple]:
        if not criteria:
            return "", ()

        condition_type = criteria.get("type")
        commands = []
        parameters = []

        if condition_type == 1:
            choice_group = criteria.get("group")
            choice_name = criteria.get("name")
            if choice_group:
                commands.append('LOWERCASE("group") LIKE ?')
                parameters.append(f"%{choice_group}%")
            if choice_name:
                commands.append("LOWERCASE(name) LIKE ?")
                parameters.append(f"%{choice_name}%")

        elif condition_type == 2:
            choice_name = criteria.get("name")
            choice_pass_type = criteria.get("pass_type")
            if choice_name:
                commands.append("LOWERCASE(name) LIKE ?")
                parameters.append(f"%{choice_name}%")
            if choice_pass_type:
                commands.append(f'"{choice_pass_type}" > 0')

        elif condition_type == 3:
            choice_name = criteria.get("name")
            choice_pass_type = criteria.get("pass_type")
            choice_min = criteria.get("min")
            choice_max = criteria.get("max")
            if choice_name:
                commands.append("LOWERCASE(name) LIKE ?")
                parameters.append(f"%{choice_name}%")
            if choice_pass_type:
                commands.append(f'"{choice_pass_type}" BETWEEN ? AND ?')
                parameters.extend([choice_min, choice_max])

        if not commands:
            return "", ()

        return " OR ".join(commands), tuple(parameters)

    def delete_records(self, criteria: Dict[str, Any]) -> int:
        query, parameters = self._find_by_conditions(criteria)
        if not query:
            return 0

        full_query = f"DELETE FROM records WHERE {query}"
        self.cursor.execute(full_query, parameters)
        deleted_count = self.cursor.rowcount
        self.connection.commit()

        if deleted_count > 0:
            self.data_changed.emit()
        return deleted_count

    def _row_to_dict(self, row: tuple) -> Dict[str, Any]:
        return {
            "name": row[0],
            "group": row[1],
            "sick": row[2],
            "other": row[3],
            "disrespectful": row[4],
            "total": row[5],
        }

    def search_records(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        query, parameters = self._find_by_conditions(criteria)
        if not query:
            return []

        full_query = f'SELECT name, "group", sick, other, disrespectful, total FROM records WHERE {query}'
        self.cursor.execute(full_query, parameters)
        rows = self.cursor.fetchall()

        return [self._row_to_dict(row) for row in rows]

    def sort_records(self, index: int, is_descending: bool) -> None:
        keys = {
            0: "name",
            1: '"group"',
            2: "sick",
            3: "other",
            4: "disrespectful",
            5: "total",
        }
        if index in keys:
            self._sort_column = keys[index]
            self._sort_order = "DESC" if is_descending else "ASC"
            self.data_changed.emit()

    def get_total_count(self) -> int:
        self.cursor.execute("SELECT COUNT(*) FROM records")
        return self.cursor.fetchone()[0]

    def get_paged_records(self, offset: int, limit: int) -> List[Dict[str, Any]]:
        query = f'SELECT name, "group", sick, other, disrespectful, total FROM records ORDER BY {self._sort_column} {self._sort_order} LIMIT ? OFFSET ?'
        self.cursor.execute(query, (limit, offset))
        rows = self.cursor.fetchall()
        return [self._row_to_dict(row) for row in rows]

    def get_all_records(self) -> List[Dict[str, Any]]:
        self.cursor.execute(
            'SELECT name, "group", sick, other, disrespectful, total FROM records'
        )
        rows = self.cursor.fetchall()
        return [self._row_to_dict(row) for row in rows]

    def load_from_db(self, filepath: str) -> None:
        source_connection = sqlite3.connect(filepath)
        source_cursor = source_connection.cursor()
        source_cursor.execute(
            'SELECT name, "group", sick, other, disrespectful FROM records'
        )
        rows = source_cursor.fetchall()
        source_connection.close()

        rows_with_total = [(*row, row[2] + row[3] + row[4]) for row in rows]

        self.cursor.execute("DELETE FROM records")
        self.cursor.executemany(
            'INSERT INTO records (name, "group", sick, other, disrespectful, total) VALUES (?, ?, ?, ?, ?, ?)',
            rows_with_total,
        )
        self.connection.commit()
        self.data_changed.emit()

    def save_to_db(self, filepath: str) -> None:
        records_to_save = self.get_all_records()

        destination_connection = sqlite3.connect(filepath)
        dest_cursor = destination_connection.cursor()
        dest_cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, "group" TEXT,
                sick INTEGER, other INTEGER, disrespectful INTEGER, total INTEGER
            )"""
        )
        dest_cursor.execute("DELETE FROM records")
        for rec in records_to_save:
            dest_cursor.execute(
                'INSERT INTO records (name, "group", sick, other, disrespectful, total) VALUES (?, ?, ?, ?, ?, ?)',
                (
                    rec["name"],
                    rec["group"],
                    rec["sick"],
                    rec["other"],
                    rec["disrespectful"],
                    rec["total"],
                ),
            )
        destination_connection.commit()
        destination_connection.close()

    def load_from_xml(self, filepath: str) -> None:
        handler = RecordHandler()
        xml.sax.parse(filepath, handler)
        self.cursor.execute("DELETE FROM records")
        for record in handler.records:
            self.add_record(record, emit_signal=False)
        self.connection.commit()
        self.data_changed.emit()

    def save_to_xml(self, filepath: str) -> None:
        records_to_save = self.get_all_records()
        RecordHandler.save_to_xml(filepath, records_to_save)
