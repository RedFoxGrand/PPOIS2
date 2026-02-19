from typing import Callable, Optional, Any
from sources.models import TeacherDegree, Book
from sources.university import University
from sources.exceptions import EnrollmentError, StateError


def _select_person(
    candidates: list, prompt_label: str, not_found_label: str, info_extractor: Callable
) -> Optional[Any]:
    query = input(f"Имя {prompt_label} (можно часть): ").strip()
    if not query:
        print("Пустой ввод.")
        return None

    found = [p for p in candidates if query.lower() in p.full_name.lower()]

    if not found:
        print(f"{not_found_label} не найден.")
        return None

    if len(found) == 1:
        return found[0]

    print(f"Найдено {len(found)} совпадений:")
    for i, p in enumerate(found, 1):
        print(f"{i}. {p.full_name} ({info_extractor(p)})")

    try:
        choice = int(input("Выберите номер: "))
        if 1 <= choice <= len(found):
            return found[choice - 1]
    except ValueError:
        pass
    print("Некорректный выбор.")
    return None


def _get_int(prompt: str, min_val: int, max_val: int) -> int:
    while True:
        try:
            val = int(input(prompt))
            if min_val <= val <= max_val:
                return val
            print(f"Число должно быть от {min_val} до {max_val}.")
        except ValueError:
            print("Пожалуйста, введите число.")


def add_student(uni: University) -> None:
    print("\n[Добавление студента]")
    name = input("ФИО: ")
    age = _get_int("Возраст: ", 16, 100)
    print(
        f"Доступные учебные планы: {', '.join([c.specialty_name for c in uni.curriculums])}"
    )
    spec = input("Введите название учебного плана: ")
    uni.enroll_student(name, age, spec)


def remove_student(uni: University) -> None:
    print("\n[Отчисление студента]")
    student = _select_person(
        uni.students,
        "студента",
        "Студент",
        lambda s: s.curriculum.specialty_name if s.curriculum else "Нет спец.",
    )
    if student:
        uni.expel_student(student)


def add_teacher(uni: University) -> None:
    print("\n[Добавление преподавателя]")
    name = input("ФИО: ")
    age = _get_int("Возраст: ", 20, 100)

    print("Степени:")
    degrees = list(TeacherDegree)
    for i, d in enumerate(degrees, 1):
        print(f"{i}. {d.value}")

    d_idx = _get_int("Номер степени: ", 1, len(degrees))
    degree = degrees[d_idx - 1]

    subj_str = input("Предметы (через запятую): ")
    subjects = [s.strip() for s in subj_str.split(",") if s.strip()]

    uni.enroll_teacher(name, age, degree, subjects)


def remove_teacher(uni: University) -> None:
    print("\n[Увольнение преподавателя]")
    teacher = _select_person(
        uni.teachers,
        "преподавателя",
        "Преподаватель",
        lambda t: t.degree.value if t.degree else "Нет степени",
    )
    if teacher:
        uni.fire_teacher(teacher)


def add_curriculum(uni: University) -> None:
    print("\n[Добавление учебного план]")
    spec_name = input("Название учебного плана: ")
    uni.add_curriculum(spec_name)


def add_subject_to_curriculum(uni: University) -> None:
    print("\n[Добавление предмета в учебный план]")
    spec_name = input("Название учебного плана: ")
    curr = uni.get_curriculum(spec_name)
    if curr:
        subject = input("Название нового предмета: ")
        curr.add_subject(subject)
    else:
        print("Учебный план не найден.")


def add_classroom(uni: University) -> None:
    print("\n[Добавление аудитории]")
    num = _get_int("Номер аудитории: ", 1, 9999)
    cap = _get_int("Вместимость: ", 1, 500)
    uni.add_classroom(num, cap)


def conduct_exam(uni: University) -> None:
    subject = input("Предмет: ")

    teacher = next((t for t in uni.teachers if subject in t.subjects), None)
    if not teacher:
        raise EnrollmentError(f"Нет преподавателя по предмету '{subject}'!")

    classroom = next((c for c in uni.classrooms if not c.is_occupied), None)
    if not classroom:
        raise StateError("Все аудитории заняты!")

    eligible_students = [
        s
        for s in uni.students
        if s.curriculum and subject in s.curriculum.required_subjects
    ]

    if not eligible_students:
        raise EnrollmentError(
            f"Нет студентов, у которых предмет '{subject}' есть в учебном плане."
        )

    print(
        f"Экзамен будет принимать {teacher.full_name} в ауд. {classroom.number}. Студентов: {len(eligible_students)}"
    )
    exam = uni.create_exam(subject, teacher, classroom, eligible_students)

    input("Нажмите Enter, чтобы начать экзамен")
    students_to_expel = exam.conduct()

    if students_to_expel:
        print(f"\nЗапуск процедуры отчисления для {len(students_to_expel)} студентов: ")
        for student in students_to_expel:
            uni.expel_student(student)
    else:
        print("Все студенты успешно сдали экзамен.")


def return_book_to_library(uni: University) -> None:
    print("\n[Возврат книги]")
    student = _select_person(
        uni.students,
        "студента",
        "Студент",
        lambda s: s.curriculum.specialty_name if s.curriculum else "Нет спец.",
    )

    if student:
        b_title = input("Название книги: ")
        uni.library.accept_return(student, b_title)


def lend_book_from_library(uni: University) -> None:
    print("\n[Выдача книги]")
    student = _select_person(
        uni.students,
        "студента",
        "Студент",
        lambda s: s.curriculum.specialty_name if s.curriculum else "Нет спец.",
    )

    if student:
        b_title = input("Название книги: ")

        book_in_library = next(
            (b for b in uni.library.inventory if b.title == b_title), None
        )
        if not book_in_library:
            print("Книга новая, добавляем в фонд 3 экземпляра...")
            new_book = Book(b_title, "Автор неизвестен")
            uni.library.add_book(new_book, 3)

        uni.library.lend_book(student, b_title)


def add_book_to_library(uni: University) -> None:
    print("\n[Добавление книги в ассортимент]")
    title = input("Название книги: ")
    author = input("Автор: ")
    qty = _get_int("Количество экземпляров: ", 1, 1000)

    existing_book = next(
        (b for b in uni.library.inventory if b.title.lower() == title.lower()), None
    )

    if existing_book:
        uni.library.add_book(existing_book, qty)
        print(f"Добавлено {qty} шт. к существующей книге '{existing_book.title}'.")
    else:
        new_book = Book(title, author)
        uni.library.add_book(new_book, qty)
        print(f"Новая книга '{title}' добавлена в количестве {qty} шт.")
