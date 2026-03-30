from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from sources.models import (
    Student,
    Teacher,
    Classroom,
    Curriculum,
    Exam,
    Library,
    ScholarshipDepartment,
    TeacherDegree,
)
from sources.exceptions import EnrollmentError, ResourceError


@dataclass
class University:
    _name: str
    _library: Library = field(default_factory=Library)
    _students: list[Student] = field(default_factory=list)
    _teachers: list[Teacher] = field(default_factory=list)
    _classrooms: list[Classroom] = field(default_factory=list)
    _curriculums: list[Curriculum] = field(default_factory=list)
    _exams: list[Exam] = field(default_factory=list)
    _accounting: ScholarshipDepartment = field(default_factory=ScholarshipDepartment)

    @property
    def name(self) -> str:
        return self._name

    @property
    def library(self) -> Library:
        return self._library

    @property
    def students(self) -> list[Student]:
        return self._students

    @property
    def teachers(self) -> list[Teacher]:
        return self._teachers

    @property
    def classrooms(self) -> list[Classroom]:
        return self._classrooms

    @property
    def curriculums(self) -> list[Curriculum]:
        return self._curriculums

    @property
    def exams(self) -> list[Exam]:
        return self._exams

    def register_curriculum(self, curriculum: Curriculum) -> None:
        self._curriculums.append(curriculum)

    def register_classroom(self, classroom: Classroom) -> None:
        self._classrooms.append(classroom)

    def register_teacher(self, teacher: Teacher) -> None:
        self._teachers.append(teacher)

    def register_student(self, student: Student) -> None:
        self._students.append(student)

    def register_exam(self, exam: Exam) -> None:
        self._exams.append(exam)

    def get_curriculum(self, name: str) -> Optional[Curriculum]:
        return next(
            (c for c in self._curriculums if c.specialty_name.lower() == name.lower()),
            None,
        )

    def enroll_student(self, full_name: str, age: int, curriculum_name: str) -> Student:
        curr = self.get_curriculum(curriculum_name)
        if not curr:
            raise EnrollmentError(f"Учебный план '{curriculum_name}' не существует!")
        new_student = Student(full_name, age)
        new_student.curriculum = curr
        self._students.append(new_student)
        return new_student

    def expel_student(self, student: Student) -> None:
        self._students.remove(student)

    def enroll_teacher(
        self, full_name: str, age: int, degree: TeacherDegree, subjects: list[str]
    ) -> Teacher:
        if not subjects:
            raise EnrollmentError(
                f"Преподаватель {full_name} должен вести хотя бы один предмет!"
            )
        new_teacher = Teacher(full_name, age)
        new_teacher.degree = degree
        new_teacher.subjects = subjects
        self._teachers.append(new_teacher)
        return new_teacher

    def fire_teacher(self, teacher: Teacher) -> None:
        self._teachers.remove(teacher)

    def create_exam(
        self,
        subject: str,
        teacher: Teacher,
        classroom: Classroom,
        students: list[Student],
    ) -> Exam:
        if subject not in teacher.subjects:
            raise EnrollmentError(
                f"Преподаватель {teacher.full_name} не знает {subject}!"
            )
        exam = Exam(subject, datetime.now(), teacher, classroom)
        exam.registered_students = students
        self._exams.append(exam)
        return exam

    def add_curriculum(self, specialty_name: str) -> Curriculum:
        if not specialty_name.strip():
            raise ValueError("Название учебного плана не может быть пустым!")
        if self.get_curriculum(specialty_name):
            raise ResourceError(f"Учебный план '{specialty_name}' уже существует!")
        new_curr = Curriculum(specialty_name)
        self._curriculums.append(new_curr)
        return new_curr

    def add_classroom(self, number: int, capacity: int) -> Classroom:
        if any(c.number == number for c in self._classrooms):
            raise ResourceError(f"Аудитория {number} уже существует!")
        new_room = Classroom(number, capacity)
        self._classrooms.append(new_room)
        return new_room

    def process_semester_end(self) -> int:
        return self._accounting.calculate_and_assign(self._students)
