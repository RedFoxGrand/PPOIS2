from dataclasses import dataclass, field
from abc import ABC
from datetime import datetime
from enum import Enum
from typing import Optional
from random import randint
from uuid import uuid4

from sources.exceptions import ResourceError, EnrollmentError, StateError


class TeacherDegree(Enum):
    DOCTOR_OF_SCIENCES = "Доктор наук"
    CANDIDATE_OF_SCIENCES = "Кандидат наук"
    ASSOCIATE_PROFESSOR = "Доцент"
    PROFESSOR = "Профессор"
    SENIOR_LECTURER = "Старший преподаватель"
    LECTURER = "Преподаватель"


@dataclass(frozen=True)
class Book:
    title: str
    author: str
    isbn: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class Curriculum:
    _specialty_name: str
    _required_subjects: list[str] = field(default_factory=list)

    @property
    def required_subjects(self) -> list[str]:
        return self._required_subjects

    @property
    def specialty_name(self) -> str:
        return self._specialty_name

    def add_subject(self, subject_name: str) -> None:
        if not subject_name.strip():
            raise ValueError("Название предмета не может быть пустым.")
        if subject_name not in self.required_subjects:
            self.required_subjects.append(subject_name)
            print(
                f"Предмет {subject_name} добавлен в учебный план {self.specialty_name}."
            )


@dataclass
class Classroom:
    _number: int
    _capacity: int
    _is_occupied: bool = False

    @property
    def is_occupied(self) -> bool:
        return self._is_occupied

    @property
    def number(self) -> int:
        return self._number

    @property
    def capacity(self) -> int:
        return self._capacity

    def occupy(self) -> None:
        if self.is_occupied:
            raise StateError(f"Аудитория {self.number} уже занята!")
        self._is_occupied = True
        print(f"Аудитория {self.number} забронирована.")

    def vacate(self) -> None:
        if not self.is_occupied:
            raise StateError(f"Аудитория {self.number} и так свободна!")
        self._is_occupied = False
        print(f"Аудитория {self.number} освобождена.")


@dataclass
class Person(ABC):
    _full_name: str
    _age: int
    _id: str = field(default_factory=lambda: str(uuid4()))

    @property
    def full_name(self) -> str:
        return self._full_name

    @property
    def age(self) -> int:
        return self._age

    @property
    def id(self) -> str:
        return self._id

    def __str__(self) -> str:
        return f"[{self.id[:6]}] {self.full_name} ({self.age} лет)"


@dataclass
class Student(Person):
    _curriculum: Optional[Curriculum] = None
    _scholarship_amount: float = 0.0
    _record_book: dict[str, int] = field(default_factory=dict)
    _borrowed_books: list[Book] = field(default_factory=list)

    @property
    def curriculum(self) -> Optional[Curriculum]:
        return self._curriculum

    @property
    def scholarship_amount(self) -> float:
        return self._scholarship_amount

    @property
    def record_book(self) -> dict[str, int]:
        return self._record_book

    @property
    def borrowed_books(self) -> list[Book]:
        return self._borrowed_books

    @property
    def average_score(self) -> float:
        if not self.record_book:
            return 0.0
        return sum(self.record_book.values()) / len(self.record_book)

    def assign_scholarship(self, amount: float) -> None:
        self._scholarship_amount = amount
        print(f"Студенту {self.full_name} назначена стипендия: {amount}")

    def take_exam(self, subject_name: str, grade: int) -> None:
        if not (0 <= grade <= 10):
            raise ValueError("Оценка должна быть от 0 до 10!")

        if self.curriculum and subject_name not in self.curriculum.required_subjects:
            raise EnrollmentError(
                f"Предмет {subject_name} не входит в учебный план студента!"
            )

        self.record_book[subject_name] = grade

    def borrow_book(self, book: Book) -> None:
        if book in self.borrowed_books:
            raise ResourceError(
                f"У студента {self.full_name} уже есть книга '{book.title}'!"
            )
        self.borrowed_books.append(book)

    def return_book(self, book: Book) -> None:
        if book in self.borrowed_books:
            self.borrowed_books.remove(book)
        else:
            raise ResourceError(f"Студент не брал книгу '{book.title}'!")


@dataclass
class Teacher(Person):
    _degree: Optional[TeacherDegree] = None
    _subjects: list[str] = field(default_factory=list)

    @property
    def degree(self) -> Optional[TeacherDegree]:
        return self._degree

    @property
    def subjects(self) -> list[str]:
        return self._subjects

    def evaluate_student(self, student: Student, subject: str, grade: int) -> None:
        student.take_exam(subject, grade)
        print(
            f"Преподаватель {self.full_name} поставил {grade} студенту {student.full_name}."
        )


@dataclass
class ScholarshipDepartment:
    _min_average_score: float = 6.0
    _base_amount: float = 100.0

    @property
    def min_average_score(self) -> float:
        return self._min_average_score

    @property
    def base_amount(self) -> float:
        return self._base_amount

    def calculate_and_assign(self, students: list[Student]) -> None:
        count = 0
        for student in students:
            if student.average_score >= self.min_average_score:
                bonus = (student.average_score - self.min_average_score) * 0.1
                final_amount = round(self.base_amount * (1 + bonus), 2)
                student.assign_scholarship(final_amount)
                count += 1
            else:
                student.assign_scholarship(0.0)
        print(f"Стипендия назначена {count} студентам.")


@dataclass
class Library:
    _inventory: dict[Book, int] = field(default_factory=dict)

    @property
    def inventory(self) -> dict[Book, int]:
        return self._inventory

    def add_book(self, book: Book, quantity: int = 1) -> None:
        if book in self.inventory:
            self.inventory[book] += quantity
        else:
            self.inventory[book] = quantity

    def lend_book(self, student: Student, book_title: str) -> None:
        found_book = next((b for b in self.inventory if b.title == book_title), None)

        if not found_book:
            raise ResourceError(f"Книга '{book_title}' не найдена в каталоге.")

        if self.inventory[found_book] <= 0:
            raise ResourceError(f"Все экземпляры '{book_title}' выданы.")

        try:
            student.borrow_book(found_book)
            self.inventory[found_book] -= 1
            print(f"Книга '{book_title}' выдана студенту {student.full_name}.")
        except ResourceError as e:
            raise e

    def accept_return(self, student: Student, book_title: str) -> None:
        found_book = next((b for b in self.inventory if b.title == book_title), None)

        if not found_book:
            raise ResourceError(f"Книга '{book_title}' не принадлежит этой библиотеке.")

        if found_book not in student.borrowed_books:
            raise ResourceError(
                f"Студент {student.full_name} не брал книгу '{book_title}'!"
            )

        student.return_book(found_book)
        self.inventory[found_book] += 1
        print(f"Студент {student.full_name} вернул книгу '{found_book.title}'.")


@dataclass
class Exam:
    _subject: str
    _date: datetime
    _teacher: Teacher
    _classroom: Classroom
    _registered_students: list[Student] = field(default_factory=list)

    @property
    def subject(self) -> str:
        return self._subject

    @property
    def date(self) -> datetime:
        return self._date

    @property
    def teacher(self) -> Teacher:
        return self._teacher

    @property
    def classroom(self) -> Classroom:
        return self._classroom

    @property
    def registered_students(self) -> list[Student]:
        return self._registered_students

    def conduct(self) -> list[Student]:
        print(f"\nЭкзамен по {self.subject} начался ({self.date.date()})\n")

        self.classroom.occupy()

        students_to_expel = []

        for student in self.registered_students:
            grade = randint(1, 10)

            self.teacher.evaluate_student(student, self.subject, grade)

            if grade < 4:
                print(f"{student.full_name} не сдал (Оценка: {grade})")
                students_to_expel.append(student)

        self.classroom.vacate()
        print("\nЭкзамен завершён\n")
        return students_to_expel
