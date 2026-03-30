from sources.models import TeacherDegree, Book
from sources.university import University
from sources.exceptions import EnrollmentError, StateError


def _get_int(text: str, min_value: int, max_value: int) -> int:
    while True:
        try:
            value = int(input(text))
            if min_value <= value <= max_value:
                return value
            print(f"Число должно быть от {min_value} до {max_value}.")
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
    print(f"Студент {name} успешно зачислен.")


def remove_student(uni: University) -> None:
    print("\n[Отчисление студента]")
    name = input("Введите ФИО студента: ").strip()
    student = next((s for s in uni.students if s.full_name == name), None)
    if student:
        uni.expel_student(student)
        print(f"Студент {student.full_name} отчислен.")
    else:
        print(f"Студент '{name}' не найден.")


def add_teacher(uni: University) -> None:
    print("\n[Добавление преподавателя]")
    name = input("ФИО: ")
    age = _get_int("Возраст: ", 20, 100)
    print("Степени:")
    degrees = list(TeacherDegree)
    for i, d in enumerate(degrees, 1):
        print(f"{i}. {d.value}")
    number = _get_int("Номер степени: ", 1, len(degrees))
    degree = degrees[number - 1]
    subjects_str = input("Предметы (через запятую): ")
    subjects = [s.strip() for s in subjects_str.split(",") if s.strip()]
    uni.enroll_teacher(name, age, degree, subjects)
    print(f"Преподаватель {name} принят на работу.")


def remove_teacher(uni: University) -> None:
    print("\n[Увольнение преподавателя]")
    name = input("Введите ФИО преподавателя: ").strip()
    teacher = next((t for t in uni.teachers if t.full_name == name), None)
    if teacher:
        uni.fire_teacher(teacher)
        print(f"Преподаватель {teacher.full_name} уволен.")
    else:
        print(f"Преподаватель '{name}' не найден.")


def add_curriculum(uni: University) -> None:
    print("\n[Добавление учебного план]")
    specialty_name = input("Название учебного плана: ")
    uni.add_curriculum(specialty_name)
    print(f"Учебный план '{specialty_name}' создан.")


def add_subject_to_curriculum(uni: University) -> None:
    print("\n[Добавление предмета в учебный план]")
    specialty_name = input("Название учебного плана: ")
    curr = uni.get_curriculum(specialty_name)
    if curr:
        subject = input("Название нового предмета: ")
        curr.add_subject(subject)
        print(f"Предмет '{subject}' добавлен в учебный план '{specialty_name}'.")
    else:
        print("Учебный план не найден.")


def add_classroom(uni: University) -> None:
    print("\n[Добавление аудитории]")
    number = _get_int("Номер аудитории: ", 1, 9999)
    capacity = _get_int("Вместимость: ", 1, 500)
    uni.add_classroom(number, capacity)
    print(f"Аудитория {number} добавлена.")


def conduct_exam(uni: University) -> None:
    subject = input("Предмет: ")
    teacher = next((t for t in uni.teachers if subject in t.subjects), None)
    if not teacher:
        raise EnrollmentError(f"Нет преподавателя по предмету '{subject}'!")
    classroom = next((c for c in uni.classrooms if not c.is_occupied), None)
    if not classroom:
        raise StateError("Все аудитории заняты!")
    students = [
        s
        for s in uni.students
        if s.curriculum and subject in s.curriculum.required_subjects
    ]
    if not students:
        raise EnrollmentError(
            f"Нет студентов, у которых предмет '{subject}' есть в учебном плане."
        )
    print(
        f"Экзамен будет принимать {teacher.full_name} в ауд. {classroom.number}. Студентов: {len(students)}."
    )
    exam = uni.create_exam(subject, teacher, classroom, students)
    print(f"\nЭкзамен по {subject} начался ({exam.date}): ")
    students_to_expel = exam.conduct()
    print("Экзамен завершён.")
    if students_to_expel:
        print(f"\nЗапуск процедуры отчисления для {len(students_to_expel)} студентов: ")
        for student in students_to_expel:
            uni.expel_student(student)
            print(f"{student.full_name} отчислен (не сдал экзамен).")
    else:
        print("Все студенты успешно сдали экзамен.")


def return_book_to_library(uni: University) -> None:
    print("\n[Возврат книги]")
    name = input("Введите ФИО студента: ").strip()
    student = next((s for s in uni.students if s.full_name == name), None)
    if student:
        title = input("Название книги: ")
        uni.library.accept_return(student, title)
        print(f"Книга '{title}' принята от студента {student.full_name}.")
    else:
        print(f"Студент '{name}' не найден.")


def lend_book_from_library(uni: University) -> None:
    print("\n[Выдача книги]")
    name = input("Введите ФИО студента: ").strip()
    student = next((s for s in uni.students if s.full_name == name), None)
    if student:
        title = input("Название книги: ")
        uni.library.lend_book(student, title)
        print(f"Книга '{title}' выдана студенту {student.full_name}.")
    else:
        print(f"Студент '{name}' не найден.")


def add_book_to_library(uni: University) -> None:
    print("\n[Добавление книги в ассортимент]")
    title = input("Название книги: ")
    author = input("Автор: ")
    quantity = _get_int("Количество экземпляров: ", 1, 1000)
    existing_book = next((b for b in uni.library.inventory if b.title == title), None)
    if existing_book:
        uni.library.add_book(existing_book, quantity)
        print(f"Добавлено {quantity} шт. к существующей книге '{existing_book.title}'.")
    else:
        new_book = Book(title, author)
        uni.library.add_book(new_book, quantity)
        print(f"Новая книга '{title}' добавлена в количестве {quantity} шт.")
