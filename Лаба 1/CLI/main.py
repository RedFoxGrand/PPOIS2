import sys

from sources.exceptions import EnrollmentError, ResourceError, StorageError, StateError
from sources.storage import save_data, load_data

from sources.handle_functions import (
    add_student,
    remove_student,
    add_teacher,
    remove_teacher,
    add_curriculum,
    add_subject_to_curriculum,
    add_classroom,
    conduct_exam,
    lend_book_from_library,
    return_book_to_library,
    add_book_to_library,
)


def main():
    try:
        uni = load_data()
    except StorageError as e:
        print(f"Критическая ошибка: {e}")
        return

    while True:
        print(
            f"{uni.name} | Студентов: {len(uni.students)}, Преподавателей: {len(uni.teachers)}, Учебных планов: {len(uni.curriculums)}"
        )
        print("\nМеню:")
        print("1. Добавить студента")
        print("2. Отчислить студента")
        print("3. Добавить преподавателя")
        print("4. Увольнение преподавателя")
        print("5. Добавить учебный план")
        print("6. Добавить предмет в учебный план")
        print("7. Добавить аудиторию")
        print("8. Провести экзамен")
        print("9. Библиотека: Взять книгу")
        print("10. Библиотека: Вернуть книгу")
        print("11. Библиотека: Добавить книгу в ассортимент")
        print("12. Завершить семестр (Расчёт стипендии)")
        print("0. Выход и Сохранение")

        choice = input("Ваш выбор: ")

        try:
            if choice == "1":
                add_student(uni)

            elif choice == "2":
                remove_student(uni)

            elif choice == "3":
                add_teacher(uni)

            elif choice == "4":
                remove_teacher(uni)

            elif choice == "5":
                add_curriculum(uni)

            elif choice == "6":
                add_subject_to_curriculum(uni)

            elif choice == "7":
                add_classroom(uni)

            elif choice == "8":
                print("\n[Проведение экзамена]")
                if not uni.students:
                    print("Нет студентов для экзамена.")
                    continue

                conduct_exam(uni)

            elif choice == "9":
                lend_book_from_library(uni)

            elif choice == "10":
                return_book_to_library(uni)

            elif choice == "11":
                add_book_to_library(uni)

            elif choice == "12":
                print("\n[Завершение семестра (Расчёт стипендии)]")
                uni.process_semester_end()

            elif choice == "0":
                print("\n[Выход и Сохранение]")
                save_data(uni)
                sys.exit(0)

            else:
                print("Неверный ввод, попробуйте еще раз.")

        except EnrollmentError as e:
            print(f"Ошибка обучения: {e}")
        except ResourceError as e:
            print(f"Ошибка ресурса: {e}")
        except StateError as e:
            print(f"Ошибка состояния: {e}")
        except StorageError as e:
            print(f"Ошибка файла: {e}")
        except ValueError as e:
            print(f"Ошибка ввода. {e}")
        except Exception as e:
            print(f"Непредвиденная ошибка: {e}")


if __name__ == "__main__":
    main()
