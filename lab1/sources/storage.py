import pickle
import os
from sources.models import (
    Curriculum,
    Classroom,
    Book,
    Student,
    Teacher,
    TeacherDegree,
)
from sources.university import University
from sources.exceptions import StorageError

# Делаем путь абсолютным, чтобы файл всегда лежал рядом со скриптом storage.py
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "university_db.pkl")


def save_data(university: University) -> None:
    temp_file = DB_FILE + ".tmp"
    try:
        with open(temp_file, "wb") as f:
            pickle.dump(university, f)
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        os.rename(temp_file, DB_FILE)
        print(f"Данные сохранены в '{DB_FILE}'")
    except Exception as e:
        raise StorageError(f"Ошибка сохранения: {e}")


def load_data() -> University:
    if not os.path.exists(DB_FILE):
        print("\nФайл базы данных не найден. Создаём новый университет.")
        return _create_default_university()

    try:
        with open(DB_FILE, "rb") as f:
            uni = pickle.load(f)
            print(f"\nЗагружена база: {uni.name}")
            return uni
    except Exception:
        print("\nФайл повреждён, создаём новую базу.")
        return _create_default_university()


def _create_default_university() -> University:
    uni = University("BSUIR")

    curriculums_data = [
        ("СУИ", ["БД", "АПЭЦ", "ООП", "ОАиП"]),
        ("ИИ", ["МОИС", "ППОИС", "ЛОИС", "ОАиП"]),
        ("ВМиП", ["ДМ", "РИК", "ООПиП", "ОАиП"]),
    ]
    for name, subjs in curriculums_data:
        uni.curriculums.append(Curriculum(name, subjs))

    for num, cap in [(114, 30), (312, 55), (503, 25), (408, 20), (721, 50)]:
        uni.classrooms.append(Classroom(num, cap))

    books_data = [
        ("Война и мир", "Л. Н. Толстой", 5),
        ("Преступление и наказание", "Ф. М. Достоевский", 3),
        ("Мастер и Маргарита", "М. Булгаков", 2),
        ("1984", "Дж. Оруэлл", 4),
    ]
    for title, author, qty in books_data:
        uni.library.inventory[Book(title, author)] = qty

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
        uni.students.append(Student(name, age, _curriculum=curr))

    teachers_data = [
        (
            "Гукова Елена Игоревна",
            56,
            TeacherDegree.ASSOCIATE_PROFESSOR,
            ["БД", "МОИС", "ЛОИС"],
        ),
        ("Петров Сергей Иванович", 43, TeacherDegree.SENIOR_LECTURER, ["МОИС", "ЛОИС"]),
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
        uni.teachers.append(Teacher(name, age, _degree=deg, _subjects=subjs))

    return uni
