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
    _accounting: ScholarshipDepartment = field(default_factory=ScholarshipDepartment)
    _students: list[Student] = field(default_factory=list)
    _teachers: list[Teacher] = field(default_factory=list)
    _classrooms: list[Classroom] = field(default_factory=list)
    _curriculums: list[Curriculum] = field(default_factory=list)
    _exams: list[Exam] = field(default_factory=list)

    @property
    def name(self) -> str:
        return self._name

    @property
    def library(self) -> Library:
        return self._library

    @property
    def accounting(self) -> ScholarshipDepartment:
        return self._accounting

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

    def get_curriculum(self, name: str) -> Optional[Curriculum]:
        return next(
            (c for c in self.curriculums if c.specialty_name.lower() == name.lower()), None
        )

    def enroll_student(self, full_name: str, age: int, curriculum_name: str) -> Student:
        curr = self.get_curriculum(curriculum_name)

        if not curr:
            raise EnrollmentError(f"Учебный план '{curriculum_name}' не существует.")

        new_student = Student(full_name, age, _curriculum=curr)
        self.students.append(new_student)
        print(f"Студент {new_student.full_name} зачислен в университет.")
        return new_student

    def expel_student(self, student: Student) -> None:
        if student in self.students:
            self.students.remove(student)
            print(f"Студент {student.full_name} отчислен за неуспеваемость.")
        else:
            print(f"Студент {student.full_name} не найден в списках.")

    def enroll_teacher(
        self, full_name: str, age: int, degree: TeacherDegree, subjects: list[str]
    ) -> Teacher:
        if not subjects:
            raise EnrollmentError(
                f"Преподаватель {full_name} должен вести хотя бы один предмет!"
            )

        new_teacher = Teacher(full_name, age, _degree=degree, _subjects=subjects)

        self.teachers.append(new_teacher)
        print(f"{new_teacher} {new_teacher.full_name} принят на кафедру.")

        return new_teacher

    def fire_teacher(self, teacher: Teacher) -> None:
        if teacher in self.teachers:
            self.teachers.remove(teacher)
            print(f"Преподаватель {teacher.full_name} сокращён.")
        else:
            print(f"Преподаватель {teacher.full_name} не найден в списках.")

    def create_exam(
        self,
        subject: str,
        teacher: Teacher,
        classroom: Classroom,
        students: list[Student],
    ) -> Exam:
        if subject not in teacher.subjects:
            raise EnrollmentError(
                f"Преподаватель {teacher.full_name} не знает {subject}"
            )

        exam = Exam(
            _subject=subject,
            _date=datetime.now(),
            _teacher=teacher,
            _classroom=classroom,
            _registered_students=students,
        )
        self.exams.append(exam)
        return exam

    def add_curriculum(self, specialty_name: str) -> Curriculum:
        if not specialty_name.strip():
            raise ValueError("Название специальности не может быть пустым.")
            
        if self.get_curriculum(specialty_name):
            raise ResourceError(f"Учебный план '{specialty_name}' уже существует.")

        new_curr = Curriculum(specialty_name)
        self.curriculums.append(new_curr)
        print(f"Учебный план '{specialty_name}' успешно создан.")
        return new_curr

    def add_classroom(self, number: int, capacity: int) -> Classroom:
        if any(c.number == number for c in self.classrooms):
            raise ResourceError(f"Аудитория {number} уже существует.")

        new_room = Classroom(number, capacity)
        self.classrooms.append(new_room)
        print(f"Аудитория {number} (вместимость: {capacity}) добавлена.")
        return new_room

    def process_semester_end(self) -> None:
        if not self.students:
            print("Нет студентов для начисления стипендии.")
            return

        self.accounting.calculate_and_assign(self.students)
        print("Семестр успешно закрыт\n")
