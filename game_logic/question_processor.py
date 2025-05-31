import math
from typing import List, Tuple, Optional

class QuestionProcessor:
    @staticmethod
    def process_question(question: str, secret_number: int) -> Tuple[Optional[str], List[int]]:
        """
        Обрабатывает вопрос и возвращает:
        - ответ (или None, если вопрос не распознан)
        - список чисел для затемнения
        """
        question = question.lower().strip()
        response = None
        dim_numbers = []

        try:
            # Обработка вопросов с числами
            if question.startswith("число больше"):
                x = int(question.split()[2].replace('?', ''))
                response = "Да" if secret_number > x else "Нет"
                dim_numbers = [n for n in range(-1000, 1001) if n <= x]

            elif question.startswith("число меньше"):
                x = int(question.split()[2].replace('?', ''))
                response = "Да" if secret_number < x else "Нет"
                dim_numbers = [n for n in range(-1000, 1001) if n >= x]

            # Обработка специальных вопросов
            elif "число простое" in question:
                response = "Да" if QuestionProcessor._is_prime(secret_number) else "Нет"
                dim_numbers = [n for n in range(-1000, 1001) if not QuestionProcessor._is_prime(n)]

            elif "число четное" in question:
                response = "Да" if secret_number % 2 == 0 else "Нет"
                dim_numbers = [n for n in range(-1000, 1001) if n % 2 != 0]

            elif "число нечетное" in question:
                response = "Да" if secret_number % 2 != 0 else "Нет"
                dim_numbers = [n for n in range(-1000, 1001) if n % 2 == 0]

            elif "число двузначное" in question:
                response = "Да" if 10 <= abs(secret_number) <= 99 else "Нет"
                dim_numbers = [n for n in range(-1000, 1001) if not (10 <= abs(n) <= 99)]

            elif "число однозначное" in question:
                response = "Да" if 0 <= abs(secret_number) <= 9 else "Нет"
                dim_numbers = [n for n in range(-1000, 1001) if not (0 <= abs(n) <= 9)]

            elif "число трехзначное" in question:
                response = "Да" if 100 <= abs(secret_number) <= 999 else "Нет"
                dim_numbers = [n for n in range(-1000, 1001) if not (100 <= abs(n) <= 999)]

            elif "число положительное" in question:
                response = "Да" if secret_number > 0 else "Нет"
                dim_numbers = [n for n in range(-1000, 1001) if n <= 0]

            elif "число отрицательное" in question:
                response = "Да" if secret_number < 0 else "Нет"
                dim_numbers = [n for n in range(-1000, 1001) if n >= 0]

            elif "число является квадратом" in question:
                response = "Да" if QuestionProcessor._is_perfect_square(secret_number) else "Нет"
                dim_numbers = [n for n in range(-1000, 1001) if not QuestionProcessor._is_perfect_square(n)]

            elif "число является кубом" in question:
                response = "Да" if QuestionProcessor._is_perfect_cube(secret_number) else "Нет"
                dim_numbers = [n for n in range(-1000, 1001) if not QuestionProcessor._is_perfect_cube(n)]

            # Проверка угадывания числа
            elif question.startswith("это число"):
                guessed_num = int(question.split()[2])
                if guessed_num == secret_number:
                    response = "Поздравляем! Вы угадали число!"
                else:
                    response = f"Нет, это не {guessed_num}. Попробуйте еще!"

        except (IndexError, ValueError):
            pass

        return response, dim_numbers

    @staticmethod
    def _is_prime(n: int) -> bool:
        if n <= 1:
            return False
        if n == 2:
            return True
        if n % 2 == 0:
            return False
        for i in range(3, int(math.sqrt(n)) + 1, 2):
            if n % i == 0:
                return False
        return True

    @staticmethod
    def _is_perfect_square(n: int) -> bool:
        if n < 0:
            return False
        root = math.isqrt(n)
        return root * root == n

    @staticmethod
    def _is_perfect_cube(n: int) -> bool:
        if n < 0:
            n = -n
        return round(n ** (1/3)) ** 3 == n