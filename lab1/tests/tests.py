import unittest

from unittest.mock import patch, mock_open
import sources.storage as storage
from sources.models import (
    Curriculum,
    Student,
    Teacher,
    Classroom,
    Book,
    Library,
    TeacherDegree,
    ScholarshipDepartment,
)
from sources.university import University
from sources.exceptions import EnrollmentError, ResourceError, StateError


class TestCurriculum(unittest.TestCase):
    def setUp(self):
        self.curr = Curriculum("ПОИТ")

    def test_add_subject(self):
        self.curr.add_subject("Python")
        self.assertIn("Python", self.curr.required_subjects)

    def test_add_empty_subject(self):
        with self.assertRaises(ValueError):
            self.curr.add_subject("   ")

    def test_add_duplicate_subject(self):
        self.curr.add_subject("Python")
        self.curr.add_subject("Python")
        self.assertEqual(self.curr.required_subjects.count("Python"), 1)


class TestClassroom(unittest.TestCase):
    def setUp(self):
        self.room = Classroom(101, 30)

    def test_occupy_vacate(self):
        self.assertFalse(self.room.is_occupied)
        self.room.occupy()
        self.assertTrue(self.room.is_occupied)

        with self.assertRaises(StateError):
            self.room.occupy()  # Уже занята

        self.room.vacate()
        self.assertFalse(self.room.is_occupied)

        with self.assertRaises(StateError):
            self.room.vacate()  # Уже свободна


class TestStudent(unittest.TestCase):
    def setUp(self):
        self.curr = Curriculum("ИИ", ["Math", "Code"])
        self.student = Student("Ivan", 20, _curriculum=self.curr)

    def test_take_exam_success(self):
        self.student.take_exam("Math", 9)
        self.assertEqual(self.student.record_book["Math"], 9)

    def test_take_exam_invalid_grade(self):
        with self.assertRaises(ValueError):
            self.student.take_exam("Math", 11)

    def test_take_exam_wrong_subject(self):
        with self.assertRaises(EnrollmentError):
            self.student.take_exam("History", 5)

    def test_average_score(self):
        self.assertEqual(self.student.average_score, 0.0)
        self.student.take_exam("Math", 8)
        self.student.take_exam("Code", 10)
        self.assertEqual(self.student.average_score, 9.0)


class TestTeacher(unittest.TestCase):
    def setUp(self):
        self.teacher = Teacher("Dr. House", 50, _subjects=["Anatomy"])
        self.room = Classroom(202, 20)


class TestLibrary(unittest.TestCase):
    def setUp(self):
        self.lib = Library()
        self.book = Book("1984", "Orwell")
        self.student = Student("Reader", 20)
        self.lib.add_book(self.book, 2)

    def test_lend_book(self):
        self.lib.lend_book(self.student, "1984")
        self.assertEqual(self.lib.inventory[self.book], 1)
        self.assertIn(self.book, self.student.borrowed_books)

    def test_lend_book_not_found(self):
        with self.assertRaises(ResourceError):
            self.lib.lend_book(self.student, "Unknown")

    def test_lend_book_out_of_stock(self):
        self.lib.lend_book(self.student, "1984")
        other_student = Student("Other", 21)
        self.lib.lend_book(other_student, "1984")

        with self.assertRaises(ResourceError):
            self.lib.lend_book(Student("Late", 22), "1984")

    def test_return_book(self):
        self.lib.lend_book(self.student, "1984")
        self.lib.accept_return(self.student, "1984")
        self.assertEqual(self.lib.inventory[self.book], 2)
        self.assertNotIn(self.book, self.student.borrowed_books)


class TestUniversity(unittest.TestCase):
    def setUp(self):
        self.uni = University("TestUni")
        self.uni.add_curriculum("CS")
        self.uni.add_classroom(101, 20)

    def test_add_curriculum_duplicate(self):
        with self.assertRaises(ResourceError):
            self.uni.add_curriculum("CS")

    def test_add_curriculum_empty(self):
        with self.assertRaises(ValueError):
            self.uni.add_curriculum("   ")

    def test_enroll_student(self):
        s = self.uni.enroll_student("Alex", 18, "CS")
        self.assertIn(s, self.uni.students)
        assert s.curriculum is not None
        self.assertEqual(s.curriculum.specialty_name, "CS")

    def test_enroll_student_case_insensitive(self):
        # Проверка "cs" вместо "CS"
        s = self.uni.enroll_student("Bob", 19, "cs")
        assert s.curriculum is not None
        self.assertEqual(s.curriculum.specialty_name, "CS")

    def test_enroll_student_no_curriculum(self):
        with self.assertRaises(EnrollmentError):
            self.uni.enroll_student("Eve", 20, "Biology")

    def test_enroll_teacher(self):
        t = self.uni.enroll_teacher("Prof", 40, TeacherDegree.PROFESSOR, ["Math"])
        self.assertIn(t, self.uni.teachers)

    def test_enroll_teacher_no_subjects(self):
        with self.assertRaises(EnrollmentError):
            self.uni.enroll_teacher("Bad Prof", 40, TeacherDegree.LECTURER, [])

    def test_create_exam(self):
        t = self.uni.enroll_teacher("T", 30, TeacherDegree.LECTURER, ["Math"])
        c = self.uni.classrooms[0]
        exam = self.uni.create_exam("Math", t, c, [])
        self.assertIn(exam, self.uni.exams)

    def test_create_exam_wrong_teacher(self):
        t = self.uni.enroll_teacher("T", 30, TeacherDegree.LECTURER, ["History"])
        c = self.uni.classrooms[0]
        with self.assertRaises(EnrollmentError):
            self.uni.create_exam("Math", t, c, [])


class TestExamProcess(unittest.TestCase):
    def setUp(self):
        self.uni = University("ExamUni")
        self.curr = self.uni.add_curriculum("IT")
        self.curr.add_subject("OOP")

        self.student1 = self.uni.enroll_student("S1", 20, "IT")
        self.student2 = self.uni.enroll_student("S2", 20, "IT")

        self.teacher = self.uni.enroll_teacher(
            "T", 40, TeacherDegree.ASSOCIATE_PROFESSOR, ["OOP"]
        )
        self.classroom = self.uni.add_classroom(101, 10)

        self.exam = self.uni.create_exam(
            "OOP", self.teacher, self.classroom, [self.student1, self.student2]
        )

    @patch("sources.models.randint")
    def test_conduct_exam_success(self, mock_randint):
        # Настраиваем randint, чтобы он возвращал 5 (сдал)
        mock_randint.return_value = 5

        expelled = self.exam.conduct()

        self.assertEqual(self.student1.record_book["OOP"], 5)
        self.assertEqual(self.student2.record_book["OOP"], 5)
        self.assertFalse(self.classroom.is_occupied)  # Аудитория должна освободиться
        self.assertEqual(len(expelled), 0)  # Никого не должны отчислить
        self.assertEqual(len(self.uni.students), 2)  # Никого не отчислили

    @patch("sources.models.randint")
    def test_conduct_exam_expulsion(self, mock_randint):
        # Настраиваем randint, чтобы он возвращал 2 (не сдал)
        mock_randint.return_value = 2

        expelled = self.exam.conduct()

        # Проверяем, что метод вернул обоих студентов на отчисление
        self.assertIn(self.student1, expelled)
        self.assertIn(self.student2, expelled)

        # Сам список студентов в университете пока не изменился (это делает контроллер)
        self.assertEqual(len(self.uni.students), 2)

        # Эмулируем действие контроллера для проверки интеграции
        for s in expelled:
            self.uni.expel_student(s)

        self.assertEqual(len(self.uni.students), 0)


class TestScholarship(unittest.TestCase):
    def setUp(self):
        self.dept = ScholarshipDepartment(_min_average_score=6.0, _base_amount=100.0)
        self.s1 = Student("Good", 20)  # Avg 8.0
        self.s1._record_book = {"A": 8, "B": 8}
        self.s2 = Student("Bad", 20)  # Avg 4.0
        self.s2._record_book = {"A": 4, "B": 4}

    def test_calculation(self):
        self.dept.calculate_and_assign([self.s1, self.s2])

        # s1: 8.0 avg. Bonus = (8.0 - 6.0) * 0.1 = 0.2. Total = 100 * 1.2 = 120
        self.assertEqual(self.s1.scholarship_amount, 120.0)

        # s2: < 6.0. Total = 0
        self.assertEqual(self.s2.scholarship_amount, 0.0)


class TestStorage(unittest.TestCase):
    def setUp(self):
        self.uni = University("SaveUni")

    @patch("sources.storage.DB_FILE", "university_db.pkl")
    @patch("builtins.open", new_callable=mock_open)
    @patch("pickle.dump")
    @patch("os.rename")
    @patch("os.remove")
    @patch("os.path.exists")
    def test_save_data(
        self, mock_exists, mock_remove, mock_rename, mock_dump, mock_file
    ):
        mock_exists.return_value = True  # Симулируем, что старый файл есть

        storage.save_data(self.uni)

        # Проверяем, что открывался временный файл
        mock_file.assert_called_with("university_db.pkl.tmp", "wb")
        # Проверяем, что pickle.dump был вызван
        mock_dump.assert_called()
        # Проверяем ротацию файлов
        mock_remove.assert_called_with("university_db.pkl")
        mock_rename.assert_called_with("university_db.pkl.tmp", "university_db.pkl")

    @patch("sources.storage.DB_FILE", "university_db.pkl")
    @patch("builtins.open", new_callable=mock_open, read_data=b"data")
    @patch("pickle.load")
    @patch("os.path.exists")
    def test_load_data_success(self, mock_exists, mock_load, mock_file):
        mock_exists.return_value = True
        expected_uni = University("LoadedUni")
        mock_load.return_value = expected_uni

        result = storage.load_data()

        self.assertEqual(result.name, "LoadedUni")

    @patch("sources.storage.DB_FILE", "university_db.pkl")
    @patch("os.path.exists")
    def test_load_data_no_file(self, mock_exists):
        mock_exists.return_value = False
        result = storage.load_data()
        self.assertEqual(result.name, "BSUIR")  # Дефолтный университет


if __name__ == "__main__":
    unittest.main()
