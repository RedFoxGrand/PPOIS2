import sys
import os
from flask import Flask, render_template, request, redirect, url_for, flash, abort

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from sources.storage import Storage  # noqa: E402
from sources.exceptions import UniversityError, StorageError  # noqa: E402
from sources.models import TeacherDegree, Book  # noqa: E402

app = Flask(__name__)
app.secret_key = "super_secret_key"
storage = Storage()


def get_uni():
    try:
        return storage.load_data()
    except (FileNotFoundError, StorageError):
        return storage.create_default_university()


@app.route("/")
def index():
    uni = get_uni()
    return render_template("index.html", uni=uni, TeacherDegree=TeacherDegree)


@app.route("/student/<student_id>")
def view_student(student_id):
    uni = get_uni()
    student = next((s for s in uni.students if s.id == student_id), None)
    if student is None:
        abort(404)
    return render_template("student_detail.html", student=student)


@app.route("/teacher/<teacher_id>")
def view_teacher(teacher_id):
    uni = get_uni()
    teacher = next((t for t in uni.teachers if t.id == teacher_id), None)
    if teacher is None:
        abort(404)
    return render_template("teacher_detail.html", teacher=teacher)


@app.route("/add_student", methods=["POST"])
def add_student():
    uni = get_uni()
    name = request.form.get("name")
    age = int(request.form.get("age"))
    specialty_name = request.form.get("specialty_name")
    try:
        uni.enroll_student(name, age, specialty_name)
        flash(f"Студент {name} успешно добавлен!", "success")
        storage.save_data(uni)
    except UniversityError as e:
        flash(f"Ошибка: {e}", "danger")

    return redirect(url_for("index"))


@app.route("/remove_student", methods=["POST"])
def remove_student():
    uni = get_uni()
    student_id = request.form.get("student_id")
    try:
        student_to_remove = next((s for s in uni.students if s.id == student_id), None)
        if student_to_remove:
            uni.expel_student(student_to_remove)
            flash(f"Студент {student_to_remove.full_name} успешно отчислен.", "success")
            storage.save_data(uni)
        else:
            flash("Студент не найден.", "danger")
    except UniversityError as e:
        flash(f"Ошибка: {e}", "danger")

    return redirect(url_for("index"))


@app.route("/add_teacher", methods=["POST"])
def add_teacher():
    uni = get_uni()
    name = request.form.get("name")
    age = int(request.form.get("age"))
    degree = request.form.get("degree")
    subjects = request.form.get("subjects")
    try:
        degree = TeacherDegree(degree)
        subjects = [s.strip() for s in subjects.split(",") if s.strip()]
        uni.enroll_teacher(name, age, degree, subjects)
        flash(f"Преподаватель {name} принят на работу!", "success")
        storage.save_data(uni)
    except (UniversityError, ValueError) as e:
        flash(f"Ошибка: {e}", "danger")

    return redirect(url_for("index"))


@app.route("/remove_teacher", methods=["POST"])
def remove_teacher():
    uni = get_uni()
    teacher_id = request.form.get("teacher_id")
    try:
        teacher = next((t for t in uni.teachers if t.id == teacher_id), None)
        if teacher:
            uni.fire_teacher(teacher)
            flash(f"Преподаватель {teacher.full_name} уволен.", "success")
            storage.save_data(uni)
        else:
            flash("Преподаватель не найден.", "danger")
    except UniversityError as e:
        flash(f"Ошибка: {e}", "danger")

    return redirect(url_for("index"))


@app.route("/add_curriculum", methods=["POST"])
def add_curriculum():
    uni = get_uni()
    specialty_name = request.form.get("specialty_name")
    try:
        uni.add_curriculum(specialty_name)
        flash(f"Учебный план '{specialty_name}' добавлен.", "success")
        storage.save_data(uni)
    except (UniversityError, ValueError) as e:
        flash(f"Ошибка: {e}", "danger")
        
    return redirect(url_for("index"))


@app.route("/add_subject", methods=["POST"])
def add_subject():
    uni = get_uni()
    specialty_name = request.form.get("specialty_name")
    subject_name = request.form.get("subject_name")
    try:
        curriculum = uni.get_curriculum(specialty_name)
        if curriculum:
            curriculum.add_subject(subject_name)
            flash(f"Предмет '{subject_name}' добавлен в план '{specialty_name}'.", "success")
            storage.save_data(uni)
        else:
            flash("Учебный план не найден.", "danger")
    except (UniversityError, ValueError) as e:
        flash(f"Ошибка: {e}", "danger")

    return redirect(url_for("index"))


@app.route("/add_classroom", methods=["POST"])
def add_classroom():
    uni = get_uni()
    number = int(request.form.get("number"))
    capacity = int(request.form.get("capacity"))
    try:
        uni.add_classroom(number, capacity)
        flash(f"Аудитория {number} добавлена.", "success")
        storage.save_data(uni)
    except UniversityError as e:
        flash(f"Ошибка: {e}", "danger")

    return redirect(url_for("index"))


@app.route("/conduct_exam", methods=["POST"])
def conduct_exam():
    uni = get_uni()
    subject = request.form.get("subject")
    try:
        teacher = next((t for t in uni.teachers if subject in t.subjects), None)
        if not teacher:
            raise UniversityError(f"Нет преподавателя по предмету '{subject}'!")
        classroom = next((c for c in uni.classrooms if not c.is_occupied), None)
        if not classroom:
            raise UniversityError("Все аудитории заняты!")
        students = [
            s
            for s in uni.students
            if s.curriculum and subject in s.curriculum.required_subjects
        ]
        if not students:
            raise UniversityError(f"Нет студентов с предметом '{subject}'.")

        exam = uni.create_exam(subject, teacher, classroom, students)
        failed_students = exam.conduct()
        for s in failed_students:
            uni.expel_student(s)
        msg = f"Экзамен по '{subject}' проведен. "
        msg += (
            f"Отчислено: {len(failed_students)}."
            if failed_students
            else "Все успешно сдали."
        )
        flash(msg, "success")
        storage.save_data(uni)
    except UniversityError as e:
        flash(f"Ошибка экзамена: {e}", "danger")

    return redirect(url_for("index"))


@app.route("/library_action", methods=["POST"])
def library_action():
    uni = get_uni()
    action = request.form.get("action")
    try:
        if action == "add_book":
            title = request.form.get("title")
            author = request.form.get("author")
            quantity = int(request.form.get("quantity"))
            book = next((b for b in uni.library.inventory if b.title == title), None)
            if book:
                uni.library.add_book(book, quantity)
            else:
                uni.library.add_book(Book(title, author), quantity)
            flash(f"Книга '{title}' добавлена ({quantity} шт.).", "success")
        else:
            student_id = request.form.get("student_id")
            title = request.form.get("title")
            student = next((s for s in uni.students if s.id == student_id), None)
            if not student:
                raise UniversityError("Студент не найден.")
            if action == "take_book":
                uni.library.lend_book(student, title)
                flash(f"Книга '{title}' выдана студенту.", "success")
            elif action == "return_book":
                uni.library.accept_return(student, title)
                flash(f"Книга '{title}' успешно возвращена.", "success")
        storage.save_data(uni)
    except UniversityError as e:
        flash(f"Ошибка библиотеки: {e}", "danger")

    return redirect(url_for("index"))


@app.route("/process_semester", methods=["POST"])
def process_semester():
    uni = get_uni()
    try:
        count = uni.process_semester_end()
        if count > 0:
            flash(f"Семестр закрыт. Стипендия назначена {count} студентам.", "success")
        else:
            flash("Семестр закрыт. Стипендии не назначены.", "info")
        storage.save_data(uni)
    except UniversityError as e:
        flash(f"Ошибка: {e}", "danger")

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
