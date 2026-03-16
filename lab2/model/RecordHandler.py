import xml.dom.minidom
import xml.sax
from typing import Any, Dict, List


class RecordHandler(xml.sax.ContentHandler):
    def __init__(self) -> None:
        self.current_data = ""
        self.name = ""
        self.group = ""
        self.sick = ""
        self.other = ""
        self.disrespectful = ""
        self.records = []

    def startElement(self, tag: str, attributes: Any) -> None:
        self.current_data = tag
        if tag == "record":
            self.name = ""
            self.group = ""
            self.sick = ""
            self.other = ""
            self.disrespectful = ""

    def endElement(self, tag: str) -> None:
        if tag == "record":
            self.records.append(
                {
                    "name": self.name.strip(),
                    "group": self.group.strip(),
                    "sick": int(self.sick.strip())
                    if self.sick.strip().isdigit()
                    else 0,
                    "other": int(self.other.strip())
                    if self.other.strip().isdigit()
                    else 0,
                    "disrespectful": int(self.disrespectful.strip())
                    if self.disrespectful.strip().isdigit()
                    else 0,
                }
            )
        self.current_data = ""

    def characters(self, content: str) -> None:
        if self.current_data == "name":
            self.name += content
        elif self.current_data == "group":
            self.group += content
        elif self.current_data == "sick":
            self.sick += content
        elif self.current_data == "other":
            self.other += content
        elif self.current_data == "disrespectful":
            self.disrespectful += content

    @staticmethod
    def save_to_xml(filepath: str, records_list: List[Dict[str, Any]]) -> None:
        doc = xml.dom.minidom.Document()
        root = doc.createElement("records")
        doc.appendChild(root)

        for record in records_list:
            record_elem = doc.createElement("record")
            root.appendChild(record_elem)

            for key, value in record.items():
                elem = doc.createElement(key)
                text_value = str(value)
                text_node = doc.createTextNode(text_value)
                elem.appendChild(text_node)
                record_elem.appendChild(elem)

        with open(filepath, "wb") as file:
            file.write(doc.toprettyxml(indent="  ", encoding="utf-8"))
