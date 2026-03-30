import json
import os


class RecordsManager:
    def __init__(self, filename="sources/json/records.json"):
        self.filename = filename
        self.records = self.load_records()

    def load_records(self):
        if not os.path.exists(self.filename):
            return [{"name": "Mario", "score": 1000}]

        with open(self.filename, "r", encoding="utf-8") as file:
            return json.load(file)

    def is_new_record(self, current_score):
        if not self.records:
            return True
        return current_score > self.records[0]["score"]

    def add_record(self, name, score):
        self.records.append({"name": name, "score": score})
        self.records = sorted(self.records, key=lambda x: x["score"], reverse=True)[:5]
        self.save_records()

    def save_records(self):
        with open(self.filename, "w", encoding="utf-8") as file:
            json.dump(self.records, file, indent=4, ensure_ascii=False)
