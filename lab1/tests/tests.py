import unittest
from unittest.mock import patch, mock_open
from sources.storage import Storage
from sources.models import (
    Curriculum,
    Student,
    Classroom,
    Book,
    Library,
    TeacherDegree,
    ScholarshipDepartment,
)
from sources.university import University
from sources.exceptions import EnrollmentError, ResourceError, StorageError


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

        self.room.vacate()
        self.assertFalse(self.room.is_occupied)


class TestStudent(unittest.TestCase):
    def setUp(self):
        self.curr = Curriculum("ИИ", ["Math", "Code"])
        self.student = Student("Ivan", 20, _curriculum=self.curr)

    def test_average_score(self):
        self.assertEqual(self.student.average_score, 0.0)
        self.student.take_exam("Math", 8)
        self.assertEqual(self.student.record_book["Math"], 8)
        self.student.take_exam("Code", 10)
        self.assertEqual(self.student.average_score, 9.0)


class TestLibrary(unittest.TestCase):
    def setUp(self):
        self.lib = Library()
        self.book = Book("1984", "Orwell")
        self.student = Student("Reader", 20)
        self.lib.add_book(self.book, 2)

    def test_lend_return_cycle(self):
        self.lib.lend_book(self.student, "1984")
        self.assertEqual(self.lib.inventory[self.book], 1)
        self.assertIn(self.book, self.student.borrowed_books)

        self.lib.accept_return(self.student, "1984")
        self.assertEqual(self.lib.inventory[self.book], 2)
        self.assertNotIn(self.book, self.student.borrowed_books)

    def test_lend_book_not_found(self):
        with self.assertRaises(ResourceError):
            self.lib.lend_book(self.student, "Unknown")

    def test_lend_book_out_of_stock(self):
        self.lib.lend_book(self.student, "1984")
        other_student = Student("Other", 21)
        self.lib.lend_book(other_student, "1984")

        with self.assertRaises(ResourceError):
            self.lib.lend_book(Student("Late", 22), "1984")


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
    def test_conduct_exam(self, mock_randint):
        mock_randint.side_effect = [5, 2]

        expelled = self.exam.conduct()

        self.assertEqual(self.student1.record_book["OOP"], 5)
        self.assertEqual(self.student2.record_book["OOP"], 2)
        self.assertFalse(self.classroom.is_occupied)

        self.assertNotIn(self.student1, expelled)
        self.assertIn(self.student2, expelled)


class TestScholarship(unittest.TestCase):
    def setUp(self):
        self.dept = ScholarshipDepartment(_min_average_score=6.0, _base_amount=100.0)
        self.s1 = Student("Good", 20)
        self.s1._record_book = {"A": 8, "B": 8}
        self.s2 = Student("Bad", 20)
        self.s2._record_book = {"A": 4, "B": 4}

    def test_calculation(self):
        self.dept.calculate_and_assign([self.s1, self.s2])

        self.assertEqual(self.s1.scholarship_amount, 120.0)

        self.assertEqual(self.s2.scholarship_amount, 0.0)


class TestStorage(unittest.TestCase):
    def setUp(self):
        self.uni = University("SaveUni")
        self.storage = Storage("university_db.json")

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    @patch("os.rename")
    @patch("os.remove")
    @patch("os.path.exists")
    def test_save_data(
        self, mock_exists, mock_remove, mock_rename, mock_dump, mock_file
    ):
        mock_exists.return_value = True

        self.storage.save_data(self.uni)

        mock_file.assert_called_with("university_db.json.tmp", "w", encoding="utf-8")
        mock_dump.assert_called()
        mock_remove.assert_called_with("university_db.json")
        mock_rename.assert_called_with("university_db.json.tmp", "university_db.json")

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists")
    def test_save_data_error(self, mock_exists, mock_file):
        mock_exists.return_value = True
        mock_file.side_effect = IOError("Permission denied")

        with self.assertRaises(StorageError):
            self.storage.save_data(self.uni)

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.load")
    @patch("os.path.exists")
    def test_load_data_corrupted(self, mock_exists, mock_load, mock_file):
        mock_exists.return_value = True
        mock_load.side_effect = ValueError("JSON Decode Error")

        # Should raise StorageError
        with self.assertRaises(StorageError):
            self.storage.load_data()

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.load")
    @patch("os.path.exists")
    def test_load_data_full_reconstruction(self, mock_exists, mock_load, mock_file):
        mock_exists.return_value = True

        data = {
            "name": "RestoredUni",
            "curriculums": [
                {"specialty_name": "CS", "required_subjects": ["Math", "Code"]}
            ],
            "classrooms": [{"number": 101, "capacity": 30, "is_occupied": False}],
            "teachers": [
                {
                    "id": "t-uuid",
                    "full_name": "Dr. Smith",
                    "age": 45,
                    "degree": "Доцент",
                    "subjects": ["Math"],
                }
            ],
            "library": [
                {
                    "book": {"title": "PyBook", "author": "Guido", "isbn": "b-uuid"},
                    "quantity": 10,
                }
            ],
            "students": [
                {
                    "id": "s-uuid",
                    "full_name": "Alice",
                    "age": 20,
                    "curriculum_name": "CS",
                    "scholarship_amount": 100.0,
                    "record_book": {"Math": 9},
                    "borrowed_books_isbns": ["b-uuid"],
                }
            ],
            "exams": [
                {
                    "subject": "Math",
                    "date": "2023-06-01T09:00:00",
                    "teacher_id": "t-uuid",
                    "classroom_number": 101,
                    "student_ids": ["s-uuid"],
                }
            ],
        }

        mock_load.return_value = data

        uni = self.storage.load_data()

        self.assertEqual(uni.name, "RestoredUni")

        student = uni.students[0]
        assert student.curriculum is not None
        self.assertEqual(student.curriculum.specialty_name, "CS")
        self.assertEqual(len(student.borrowed_books), 1)
        self.assertEqual(student.borrowed_books[0].title, "PyBook")

        exam = uni.exams[0]
        self.assertEqual(exam.teacher.full_name, "Dr. Smith")
        self.assertEqual(exam.classroom.number, 101)
        self.assertEqual(exam.registered_students[0].full_name, "Alice")

    @patch("os.path.exists")
    def test_load_data_no_file(self, mock_exists):
        mock_exists.return_value = False
        with self.assertRaises(FileNotFoundError):
            self.storage.load_data()


if __name__ == "__main__":
    unittest.main()
