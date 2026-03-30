import json
import os
from datetime import datetime
from typing import Optional
from sources.models import (
    Curriculum,
    Classroom,
    Book,
    Student,
    Teacher,
    TeacherDegree,
    Exam,
)
from sources.university import University
from sources.exceptions import StorageError


class Storage:
    def __init__(self, file: Optional[str] = None):
        if file:
            self.file = file
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.file = os.path.join(base_dir, "university.json")

    def save_data(self, university: University) -> None:
        data = {
            "name": university.name,
            "curriculums": [
                {
                    "specialty_name": c.specialty_name,
                    "required_subjects": c.required_subjects,
                }
                for c in university.curriculums
            ],
            "classrooms": [
                {
                    "number": c.number,
                    "capacity": c.capacity,
                    "is_occupied": c.is_occupied,
                }
                for c in university.classrooms
            ],
            "teachers": [
                {
                    "id": t.id,
                    "full_name": t.full_name,
                    "age": t.age,
                    "degree": t.degree.value if t.degree else None,
                    "subjects": t.subjects,
                }
                for t in university.teachers
            ],
            "students": [
                {
                    "id": s.id,
                    "full_name": s.full_name,
                    "age": s.age,
                    "curriculum_name": s.curriculum.specialty_name
                    if s.curriculum
                    else None,
                    "scholarship_amount": s.scholarship_amount,
                    "record_book": s.record_book,
                    "borrowed_books_isbns": [b.isbn for b in s.borrowed_books],
                }
                for s in university.students
            ],
            "library": [
                {
                    "book": {
                        "title": b.title,
                        "author": b.author,
                        "isbn": b.isbn,
                    },
                    "quantity": quantity,
                }
                for b, quantity in university.library.inventory.items()
            ],
            "exams": [
                {
                    "subject": e.subject,
                    "date": e.date.isoformat(),
                    "teacher_id": e.teacher.id,
                    "classroom_number": e.classroom.number,
                    "student_ids": [s.id for s in e.registered_students],
                }
                for e in university.exams
            ],
        }

        temp_file = self.file + ".tmp"
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            if os.path.exists(self.file):
                os.remove(self.file)
            os.rename(temp_file, self.file)
        except Exception as e:
            raise StorageError(f"Ошибка сохранения: {e}")

    def load_data(self) -> University:
        if not os.path.exists(self.file):
            raise FileNotFoundError
        try:
            with open(self.file, "r", encoding="utf-8") as f:
                data = json.load(f)
            uni = University(data["name"])

            for c_data in data["curriculums"]:
                curr = Curriculum(c_data["specialty_name"], c_data["required_subjects"])
                uni.register_curriculum(curr)

            for r_data in data["classrooms"]:
                room = Classroom(
                    r_data["number"],
                    r_data["capacity"],
                )
                room.is_occupied = r_data["is_occupied"]
                uni.register_classroom(room)

            teachers_map = {}
            for t_data in data["teachers"]:
                degree = TeacherDegree(t_data["degree"]) if t_data["degree"] else None
                teacher = Teacher(t_data["full_name"], t_data["age"])
                teacher.id = t_data["id"]
                teacher.degree = degree
                teacher.subjects = t_data["subjects"]
                uni.register_teacher(teacher)
                teachers_map[teacher.id] = teacher

            books_map = {}
            for item in data["library"]:
                b_data = item["book"]
                book = Book(b_data["title"], b_data["author"], isbn=b_data["isbn"])
                uni.library.add_book(book, item["quantity"])
                books_map[book.isbn] = book

            students_map = {}
            for s_data in data["students"]:
                curr = (
                    uni.get_curriculum(s_data["curriculum_name"])
                    if s_data["curriculum_name"]
                    else None
                )
                student = Student(s_data["full_name"], s_data["age"])
                student.id = s_data["id"]
                student.curriculum = curr
                student.scholarship_amount = s_data["scholarship_amount"]
                student.record_book = s_data["record_book"]
                for isbn in s_data.get("borrowed_books_isbns", []):
                    if isbn in books_map:
                        student.add_book(books_map[isbn])
                uni.register_student(student)
                students_map[student.id] = student

            for e_data in data.get("exams", []):
                teacher = teachers_map.get(e_data["teacher_id"])
                classroom = next(
                    (
                        c
                        for c in uni.classrooms
                        if c.number == e_data["classroom_number"]
                    ),
                    None,
                )
                reg_students = []
                for s_id in e_data["student_ids"]:
                    if s_id in students_map:
                        reg_students.append(students_map[s_id])
                if teacher and classroom:
                    exam = Exam(
                        e_data["subject"],
                        datetime.fromisoformat(e_data["date"]),
                        teacher,
                        classroom,
                    )
                    exam.registered_students = reg_students
                    uni.register_exam(exam)

            return uni
        except Exception as e:
            raise StorageError(e)

    def create_default_university(self) -> University:
        uni = University("BSUIR")
        curriculums_data = [
            ("СУИ", ["БД", "АПЭЦ", "ООП", "ОАиП"]),
            ("ИИ", ["МОИС", "ППОИС", "ЛОИС", "ОАиП"]),
            ("ВМиП", ["ДМ", "РИК", "ООПиП", "ОАиП"]),
        ]
        for name, subjects in curriculums_data:
            uni.register_curriculum(Curriculum(name, subjects))

        for number, capacity in [(114, 30), (312, 55), (503, 25), (408, 20), (721, 50)]:
            uni.register_classroom(Classroom(number, capacity))

        books_data = [
            ("Война и мир", "Л. Н. Толстой", 5),
            ("Преступление и наказание", "Ф. М. Достоевский", 3),
            ("Мастер и Маргарита", "М. Булгаков", 2),
            ("1984", "Дж. Оруэлл", 4),
        ]
        for title, author, quantity in books_data:
            uni.library.add_book(Book(title, author), quantity)

        sui = uni.curriculums[0]
        ii = uni.curriculums[1]
        vmip = uni.curriculums[2]

        students_data = [
            ("Иванов Иван Иванович", 20, sui),
            ("Петров Петр Петрович", 22, ii),
            ("Сидоров Сидор Сидорович", 19, vmip),
            ("Андрееев Андрей Андреевич", 18, ii),
            ("Денисов Денис Денисович", 27, sui),
            ("Максимов Максим Максимович", 20, ii),
            ("Сергеев Сергей Сергеевич", 18, vmip),
            ("Антонов Антон Антонович", 21, ii),
            ("Павлов Павел Павлович", 22, vmip),
            ("Захаров Захар Захарович", 18, sui),
            ("Алексеев Алексей Алексеевич", 19, sui),
            ("Васильев Василий Васильевич", 21, ii),
        ]

        for name, age, curr in students_data:
            s = Student(name, age)
            s.curriculum = curr
            uni.register_student(s)

        teachers_data = [
            (
                "Гукова Елена Игоревна",
                56,
                TeacherDegree.ASSOCIATE_PROFESSOR,
                ["БД", "МОИС", "ЛОИС"],
            ),
            (
                "Петров Сергей Иванович",
                43,
                TeacherDegree.SENIOR_LECTURER,
                ["МОИС", "ЛОИС"],
            ),
            (
                "Ронина Анна Ивановна",
                45,
                TeacherDegree.DOCTOR_OF_SCIENCES,
                ["ООП", "ООПиП", "ППОИС", "ОАиП"],
            ),
            (
                "Андреева Елена Александровна",
                39,
                TeacherDegree.CANDIDATE_OF_SCIENCES,
                ["ППОИС", "ОАиП", "БД", "ДМ"],
            ),
            ("Норд Ольга Эдуардовна", 25, TeacherDegree.LECTURER, ["АПЭЦ", "РИК"]),
            (
                "Асманов Константин Русланович",
                41,
                TeacherDegree.SENIOR_LECTURER,
                ["АПЭЦ", "ООПиП", "ООП"],
            ),
            (
                "Кондратьев Михаил Михайлович",
                72,
                TeacherDegree.PROFESSOR,
                ["РИК", "ДМ", "ОАиП"],
            ),
        ]

        for name, age, deg, subjs in teachers_data:
            t = Teacher(name, age)
            t.degree = deg
            t.subjects = subjs
            uni.register_teacher(t)

        return uni
