from dataclasses import dataclass, field
from abc import ABC
from datetime import datetime
from enum import Enum
from typing import Optional
from random import randint
from uuid import uuid4
from sources.exceptions import ResourceError


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
    def specialty_name(self) -> str:
        return self._specialty_name

    @property
    def required_subjects(self) -> list[str]:
        return self._required_subjects

    def add_subject(self, subject_name: str) -> None:
        if not subject_name.strip():
            raise ValueError("Название предмета не может быть пустым!")
        if subject_name not in self._required_subjects:
            self._required_subjects.append(subject_name)


@dataclass
class Classroom:
    _number: int
    _capacity: int
    _is_occupied: bool = False

    @property
    def number(self) -> int:
        return self._number

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def is_occupied(self) -> bool:
        return self._is_occupied

    @is_occupied.setter
    def is_occupied(self, value: bool) -> None:
        self._is_occupied = value

    def occupy(self) -> None:
        self._is_occupied = True

    def vacate(self) -> None:
        self._is_occupied = False


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

    @id.setter
    def id(self, value: str) -> None:
        self._id = value


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
        if not self._record_book:
            return 0.0
        return sum(self._record_book.values()) / len(self._record_book)

    @curriculum.setter
    def curriculum(self, curriculum: Optional[Curriculum]) -> None:
        self._curriculum = curriculum

    @scholarship_amount.setter
    def scholarship_amount(self, amount: float) -> None:
        self._scholarship_amount = amount

    @record_book.setter
    def record_book(self, record_book: dict[str, int]) -> None:
        self._record_book = record_book

    def assign_scholarship(self, amount: float) -> None:
        self._scholarship_amount = amount

    def take_exam(self, subject_name: str, grade: int) -> None:
        self._record_book[subject_name] = grade

    def borrow_book(self, book: Book) -> None:
        if book in self._borrowed_books:
            raise ResourceError(
                f"У студента {self._full_name} уже есть книга '{book.title}'!"
            )
        self._borrowed_books.append(book)

    def return_book(self, book: Book) -> None:
        if book in self._borrowed_books:
            self._borrowed_books.remove(book)
        else:
            raise ResourceError(f"Студент не брал книгу '{book.title}'!")

    def add_book(self, book: Book) -> None:
        self._borrowed_books.append(book)


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

    @degree.setter
    def degree(self, degree: Optional[TeacherDegree]) -> None:
        self._degree = degree

    @subjects.setter
    def subjects(self, subjects: list[str]) -> None:
        self._subjects = subjects

    def evaluate_student(self, student: Student, subject: str, grade: int) -> None:
        student.take_exam(subject, grade)


@dataclass
class ScholarshipDepartment:
    _min_average_score: float = 6.0
    _base_amount: float = 100.0

    def calculate_and_assign(self, students: list[Student]) -> int:
        count = 0
        for student in students:
            if student.average_score >= self._min_average_score:
                bonus = (student.average_score - self._min_average_score) * 0.1
                final_amount = round(self._base_amount * (1 + bonus), 2)
                student.assign_scholarship(final_amount)
                count += 1
            else:
                student.assign_scholarship(0.0)
        return count


@dataclass
class Library:
    _inventory: dict[Book, int] = field(default_factory=dict)

    @property
    def inventory(self) -> dict[Book, int]:
        return self._inventory

    def add_book(self, book: Book, quantity: int) -> None:
        if book in self._inventory:
            self._inventory[book] += quantity
        else:
            self._inventory[book] = quantity

    def lend_book(self, student: Student, book_title: str) -> None:
        found_book = next((b for b in self._inventory if b.title == book_title), None)
        if not found_book:
            raise ResourceError(f"Книга '{book_title}' не найдена в каталоге!")
        if self._inventory[found_book] <= 0:
            raise ResourceError(f"Все экземпляры '{book_title}' выданы!")
        student.borrow_book(found_book)
        self._inventory[found_book] -= 1

    def accept_return(self, student: Student, book_title: str) -> None:
        found_book = next((b for b in self._inventory if b.title == book_title), None)
        if not found_book:
            raise ResourceError(f"Книга '{book_title}' не принадлежит этой библиотеке!")
        student.return_book(found_book)
        self._inventory[found_book] += 1


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
    
    @registered_students.setter
    def registered_students(self, students: list[Student]) -> None:
        self._registered_students = students

    def conduct(self) -> list[Student]:
        self._classroom.occupy()
        students_to_expel = []
        for student in self._registered_students:
            grade = randint(1, 10)
            self._teacher.evaluate_student(student, self._subject, grade)
            if grade < 4:
                students_to_expel.append(student)
        self._classroom.vacate()
        return students_to_expel

