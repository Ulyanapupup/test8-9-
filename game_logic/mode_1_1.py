# game_logic/mode_1_1.py
import json, re, string
import os

# Определяем абсолютный путь к json (от корня проекта)
json_path = os.path.join('game_logic', 'questions_1_1.json')

with open(json_path, 'r', encoding='utf-8') as f:
    question_map = json.load(f)

secret_number = 17  # можно позже сделать динамическим

def is_greater(x): return secret_number > x
def is_less(x): return secret_number < x
def is_equal(x): return secret_number == x
def is_prime(_=None):
    if secret_number < 2: return False
    for i in range(2, int(secret_number ** 0.5) + 1):
        if secret_number % i == 0: return False
    return True

question_functions = {
    "is_greater": is_greater,
    "is_less": is_less,
    "is_equal": is_equal,
    "is_prime": is_prime
}

def process_question(q):
    q = q.lower().translate(str.maketrans('', '', string.punctuation))
    for keyword, func_name in question_map.items():
        if keyword in q:
            func = question_functions[func_name]
            if func_name == "is_prime":
                return "Да" if func() else "Нет"
            nums = re.findall(r'\d+', q)
            if not nums: return "Пожалуйста, укажите число"
            return "Да" if func(int(nums[0])) else "Нет"
    return "Неизвестный вопрос"
