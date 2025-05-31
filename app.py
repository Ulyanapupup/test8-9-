import eventlet
eventlet.monkey_patch()

import os
import uuid
import random
import string
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, send, join_room, leave_room, emit

# Импортируем логику игры
from game_logic import mode_1_1
from game_logic.mode_1_2 import Game  # импорт класса Game из mode_1_2

app = Flask(__name__)
app.secret_key = 'some_secret_key'  # для сессий
socketio = SocketIO(app, cors_allowed_origins="*")

games = {}  # хранилище активных игр для режима 1.2: {game_id: Game}

room_roles = {}  # {room_code: {'guesser': session_id, 'creator': session_id}}

# Хранилище комнат для сетевой игры режимов 2.1 и 2.2
rooms = {}
# Формат rooms:
# rooms = {
#   'ROOMCODE': {
#       'players': set(session_ids),
#       'creator': session_id,
#       'mode': None  # '2.1' или '2.2' после выбора
#   }
# }

session_to_sid = {}  # сопоставление session_id -> socket.id


def generate_session_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))

@app.before_request
def make_session_permanent():
    if 'session_id' not in session:
        session['session_id'] = generate_session_id()

# --- Маршруты ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/room_setup')
def room_setup():
    return render_template('room_setup.html')

@app.route('/game/<mode>')
def game_mode(mode):
    if mode == '1.1':
        return render_template('game_mode_1_1.html')
    elif mode == '1.2':
        return render_template('game_mode_1_2.html')
    elif mode in ['2.1', '2.2']:
        return render_template('room_setup.html', mode=mode)
    else:
        return "Неизвестный режим", 404

@app.route('/select_range_1_2')
def select_range_1_2():
    return render_template('range_select_1_2.html')

@app.route('/game_mode_1_2')
def game_mode_1_2():
    range_param = request.args.get('range', '0_100')
    try:
        min_range, max_range = map(int, range_param.split('_'))
    except ValueError:
        min_range, max_range = 0, 100
    return render_template('game_mode_1_2.html', min_range=min_range, max_range=max_range)


# Запуск игры 1.2 — создание новой игры
@app.route('/start_game_1_2', methods=['POST'])
def start_game_1_2():
    data = request.json
    secret = int(data.get('secret'))
    min_range = int(data.get('min_range'))
    max_range = int(data.get('max_range'))

    game_id = str(uuid.uuid4())
    games[game_id] = Game(secret, min_range, max_range)
    first_question = games[game_id].next_question()
    return jsonify({'game_id': game_id, 'question': first_question})

# Обработка ответа в игре 1.2
@app.route('/answer_1_2', methods=['POST'])
def answer_1_2():
    data = request.json
    game_id = data.get('game_id')
    answer = data.get('answer')

    game = games.get(game_id)
    if not game:
        return jsonify({'error': 'Игра не найдена'}), 404

    response = game.process_answer(answer)

    done = getattr(game, 'finished', False)

    return jsonify({'response': response, 'done': done})

# Обработка вопросов для режимов 1.1 и 1.2
@app.route('/ask', methods=['POST'])
def ask():
    question = request.json.get("question", "")
    mode = request.json.get("mode", "1.1")
    if mode == "1.1":
        answer = mode_1_1.process_question(question)
    elif mode == "1.2":
        answer_yes = request.json.get("answer") == "да"
        game_id = request.json.get("game_id")
        game = games.get(game_id)
        if not game:
            return jsonify({"answer": "Игра не найдена"})
        game.filter_numbers(question, answer_yes)
        answer = ", ".join(map(str, game.get_possible_numbers()))
    else:
        answer = "Неподдерживаемый режим"

    return jsonify({"answer": answer})

# Новый роут /game для сетевой игры с комнатой
@app.route('/game')
def game():
    room = request.args.get('room', '').upper()
    if not room:
        return redirect(url_for('room_setup'))

    session_id = session['session_id']

    if room not in rooms:
        # Создаём новую комнату, первый игрок - создатель
        rooms[room] = {
            'players': set(),
            'roles': {},
            'creator': session_id,
            'mode': None
        }
    # Добавляем игрока в комнату, если его там нет
    rooms[room]['players'].add(session_id)

    player_count = len(rooms[room]['players'])
    is_creator = (session_id == rooms[room]['creator'])

    return render_template('game.html', room=room, player_count=player_count, is_creator=is_creator)


# WebSocket обработчики

@socketio.on('join_room')
def on_join(data):
    room = data['room']
    session_id = data['session_id']

    # Проверяем есть ли комната, если нет — создаём с этим игроком как создателем
    if room not in rooms:
        rooms[room] = {
            'players': set(),
            'roles': {},
            'creator': session_id,
            'mode': None
        }

    players = rooms[room]['players']

    # Проверяем, если в комнате уже 2 игрока и текущий игрок не в списке — не пускаем
    if len(players) >= 2 and session_id not in players:
        emit('error', {'message': 'Комната заполнена, вход запрещен.'})
        return

    # Если всё ок, добавляем игрока в комнату и присоединяем socket.io к комнате
    join_room(room)
    players.add(session_id)

    # Отправляем обновление количества игроков всем в комнате
    emit('update_player_count', {'count': len(players)}, room=room)

    # Можно отправить подтверждение подключившемуся
    emit('joined', {'message': f'Вы подключились к комнате {room}.'})

@app.route('/game_mode_2_1')
def game_mode_2_1():
    room = request.args.get('room')
    # if not room or room not in rooms:
    #     return redirect(url_for('room_setup'))
    return render_template('game_mode_2_1.html', room=room)


@app.route('/game_mode_2_2')
def game_mode_2_2():
    room = request.args.get('room')
    # if not room or room not in rooms:
        # return redirect(url_for('room_setup'))
    return render_template('game_mode_2_2.html', room=room)

@socketio.on('choose_mode')
def on_choose_mode(data):
    room = data['room']
    mode = data['mode']

    if room in rooms:
        rooms[room]['mode'] = mode
        # Рассылаем событие для всех в комнате
        emit('start_game', {'room': room, 'mode': mode}, room=room)

@socketio.on('disconnect')
def on_disconnect():
    session_id = session.get('session_id')
    if not session_id:
        return

    for room, data in list(rooms.items()):
        if session_id in data['players']:
            data['players'].remove(session_id)
            leave_room(room)  # Игрок покидает комнату Socket.IO

            # Обновляем всех игроков в комнате о количестве
            emit('update_player_count', {'count': len(data['players'])}, room=room)

            # Если в комнате никого не осталось — удаляем её из словаря
            if len(data['players']) == 0:
                del rooms[room]
            break

# Простой WebSocket обработчик сообщений (можно убрать/настроить)
@socketio.on('message')
def handle_message(msg):
    send(msg, broadcast=True)
    
    
    
@socketio.on('join_game_room')
def handle_join_game_room(data):
    room = data['room']
    session_id = data['session_id']
    sid = request.sid

    join_room(room)
    session_to_sid[session_id] = sid  # сохраняем socket.id

    # Инициализация комнаты если её нет
    if room not in room_roles:
        room_roles[room] = {'guesser': None, 'creator': None}

    emit('roles_updated', {
        'roles': room_roles[room],
        'your_role': next((role for role, sid in room_roles[room].items() if sid == session_id), None)
    }, to=sid)


@socketio.on('select_role')
def handle_select_role(data):
    room = data['room']
    session_id = data['session_id']
    role = data['role']
    
    if room not in room_roles:
        emit('error', {'message': 'Комната не существует'}, to=session_id)
        return
    
    # Проверяем, что роль не занята другим игроком
    if room_roles[room][role] and room_roles[room][role] != session_id:
        emit('role_taken', {'role': role}, to=session_id)
        return
    
    # Удаляем игрока из других ролей (если он меняет выбор)
    for r in ['guesser', 'creator']:
        if room_roles[room][r] == session_id:
            room_roles[room][r] = None
    
    # Назначаем новую роль
    room_roles[room][role] = session_id
    
    # Отправляем обновление всем в комнате
    emit('roles_updated', {
        'roles': room_roles[room]
    }, room=room)
    
@socketio.on('choose_role')
def handle_choose_role(data):
    room = data['room']
    session_id = data['session_id']
    role = data['role']
    
    if room in rooms:
        rooms[room]['roles'][session_id] = role
        print(f"[SERVER] Игрок {session_id} выбрал роль {role} в комнате {room}")
        emit('role_chosen', {'session_id': session_id, 'role': role}, room=room)
        return
    
    # Инициализируем структуру roles если её нет
    if 'roles' not in rooms[room]:
        rooms[room]['roles'] = {}
    
    # Проверяем, что роль не занята другим игроком
    for existing_role, existing_id in rooms[room]['roles'].items():
        if existing_role == role and existing_id != session_id:
            emit('role_taken', {'role': role}, to=session_id)
            return
    
    # Сохраняем роль игрока
    rooms[room]['roles'][role] = session_id
    
    # Отправляем обновление ролей всем в комнате
    emit('roles_update', {'roles': rooms[room]['roles']}, room=room)

@socketio.on('leave_game')
def handle_leave_game(data):
    room = data['room']
    session_id = data['session_id']
    
    # Очищаем роли в rooms[room]['roles']
    if room in rooms:
        if 'players' in rooms[room] and session_id in rooms[room]['players']:
            rooms[room]['players'].remove(session_id)
        
        if 'roles' in rooms[room]:
            # Удаляем роль игрока из rooms[room]['roles']
            for role, sid in list(rooms[room]['roles'].items()):
                if sid == session_id:
                    del rooms[room]['roles'][role]
    
    # Очищаем роли в room_roles
    if room in room_roles:
        for role in ['guesser', 'creator']:
            if room_roles[room][role] == session_id:
                room_roles[room][role] = None
    
    # Уведомляем других игроков
    emit('player_left', {'session_id': session_id}, room=room)
    
    # Если комната пуста, удаляем её
    if room in rooms and 'players' in rooms[room] and not rooms[room]['players']:
        del rooms[room]
        if room in room_roles:
            del room_roles[room]
    
    # Перенаправляем всех игроков
    emit('force_leave', {}, room=room)

@socketio.on('start_game')
def handle_start_game(data):
    room = data['room']
    session_id = session.get('session_id')
    roles = room_roles.get(room, {})

    if not roles:
        return {'status': 'error', 'message': 'Комната не существует'}

    guesser_id = roles.get('guesser')
    creator_id = roles.get('creator')

    if guesser_id and creator_id and guesser_id != creator_id:
        # Получаем socket.id каждого игрока
        guesser_sid = session_to_sid.get(guesser_id)
        creator_sid = session_to_sid.get(creator_id)

        if not guesser_sid or not creator_sid:
            return {'status': 'error', 'message': 'Один из игроков отключён'}

        # Отправляем редирект каждому игроку
        print(f"Sending redirect to guesser: {roles['guesser']}")
        emit('redirect', {'url': f'/game2/guesser?room={room}'}, to=guesser_sid)
        emit('redirect', {'url': f'/game2/creator?room={room}'}, to=creator_sid)

        return {'status': 'ok'}
    else:
        return {'status': 'error', 'message': 'Оба игрока должны выбрать разные роли!'}

@socketio.on('chat_message')
def handle_chat_message(data):
    room = data.get('room')
    session_id = data.get('session_id')
    message = data.get('message')
    role = None

    # Определяем роль отправителя
    if room in room_roles:
        for r, sid in room_roles[room].items():
            if sid == session_id:
                role = r
                break

    # Название отправителя
    sender = "Неизвестный"
    if role == "guesser":
        sender = "Угадывающий"
    elif role == "creator":
        sender = "Загадывающий"

    emit('chat_message', {
        'sender': sender,
        'message': message
    }, room=room)
        
@app.route('/game2/guesser')
def game_guesser():
    room = request.args.get('room')
    return render_template('game2/guesser.html', room=room, session=session)

@app.route('/game2/creator')
def game_creator():
    room = request.args.get('room')
    return render_template('game2/creator.html', room=room, session=session)
    
@app.route('/debug/templates')
def debug_templates():
    return str(os.listdir('templates/game2'))  # Должен показать ['guesser.html', 'creator.html']



# Добавим в app.py
@socketio.on('process_question')
def handle_process_question(data):
    room = data['room']
    session_id = data['session_id']
    question = data['question']
    
    if room not in room_roles or session_id != room_roles[room].get('guesser'):
        return {'error': 'Недостаточно прав'}
    
    # Получаем загаданное число от создателя
    secret_number = rooms[room].get('secret_number')
    if secret_number is None:
        return {'error': 'Число еще не загадано'}
    
    # Обрабатываем вопрос
    response, dim_numbers = process_number_question(secret_number, question)
    
    # Отправляем ответ всем в комнате
    emit('question_response', {
        'question': question,
        'response': response,
        'dim_numbers': dim_numbers
    }, room=room)
    
    return {'status': 'ok'}

def process_number_question(number, question):
    question = question.lower().strip()
    dim_numbers = []
    response = "Не понимаю вопрос"
    
    try:
        # Обработка разных типов вопросов
        if question.startswith('число больше'):
            x = int(question.split()[2].rstrip('?'))
            response = "Да" if number > x else "Нет"
            dim_numbers = [n for n in range(-100, 101) if not n > x] if number > x else [n for n in range(-100, 101) if n > x]
            
        elif question.startswith('число меньше'):
            x = int(question.split()[2].rstrip('?'))
            response = "Да" if number < x else "Нет"
            dim_numbers = [n for n in range(-100, 101) if not n < x] if number < x else [n for n in range(-100, 101) if n < x]
            
        elif question == 'число простое' or question == 'число простое?':
            is_prime = is_number_prime(number)
            response = "Да" if is_prime else "Нет"
            dim_numbers = [n for n in range(-100, 101) if is_number_prime(n) != is_prime]
            
        elif question == 'число четное' or question == 'число четное?':
            response = "Да" if number % 2 == 0 else "Нет"
            dim_numbers = [n for n in range(-100, 101) if n % 2 != (0 if response == "Да" else 1)]
            
        elif question == 'число нечетное' or question == 'число нечетное?':
            response = "Да" if number % 2 != 0 else "Нет"
            dim_numbers = [n for n in range(-100, 101) if n % 2 != (1 if response == "Да" else 0)]
            
        elif question == 'число двузначное' or question == 'число двузначное?':
            response = "Да" if 10 <= abs(number) < 100 else "Нет"
            dim_numbers = [n for n in range(-100, 101) if (10 <= abs(n) < 100) != (response == "Да")]
            
        elif question == 'число однозначное' or question == 'число однозначное?':
            response = "Да" if 0 <= abs(number) < 10 else "Нет"
            dim_numbers = [n for n in range(-100, 101) if (0 <= abs(n) < 10) != (response == "Да")]
            
        elif question == 'число трехзначное' or question == 'число трехзначное?':
            response = "Да" if 100 <= abs(number) < 100 else "Нет"
            dim_numbers = [n for n in range(-100, 101) if (100 <= abs(n) < 100) != (response == "Да")]
            
        elif question == 'число положительное' or question == 'число положительное?':
            response = "Да" if number > 0 else "Нет"
            dim_numbers = [n for n in range(-100, 101) if (n > 0) != (response == "Да")]
            
        elif question == 'число отрицательное' or question == 'число отрицательное?':
            response = "Да" if number < 0 else "Нет"
            dim_numbers = [n for n in range(-100, 101) if (n < 0) != (response == "Да")]
            
        elif question == 'число является квадратом' or question == 'число является квадратом?':
            root = int(number**0.5)
            response = "Да" if root**2 == number else "Нет"
            dim_numbers = [n for n in range(-100, 101) if (int(n**0.5)**2 == n) != (response == "Да")]
            
        elif question == 'число является кубом' or question == 'число является кубом?':
            root = round(number**(1/3))
            response = "Да" if root**3 == number else "Нет"
            dim_numbers = [n for n in range(-100, 101) if (round(n**(1/3))**3 == n) != (response == "Да")]
            
        elif question.startswith('это число'):
            guess = int(question.split()[2].rstrip('?'))
            if guess == number:
                response = f"Поздравляем! Вы угадали число {number}!"
                # Отправляем событие победы
                emit('game_won', {
                    'winner': session_id,
                    'secret': number
                }, room=room)
            else:
                response = f"Нет, это не число {guess}. Попробуйте еще раз!"
                
    except (ValueError, IndexError):
        response = "Не понимаю вопрос. Пожалуйста, задайте вопрос в правильном формате."
    
    return response, dim_numbers

def is_number_prime(n):
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True
    
@socketio.on('set_secret_number')
def handle_set_secret_number(data):
    room = data['room']
    secret_number = data['secret_number']
    session_id = data.get('session_id')
    
    if room not in room_roles or session_id != room_roles[room].get('creator'):
        return {'error': 'Недостаточно прав'}
    
    # Сохраняем загаданное число
    if room not in rooms:
        rooms[room] = {}
    rooms[room]['secret_number'] = secret_number
    
    emit('secret_number_set', {
        'secret_number': secret_number
    }, to=session_to_sid[session_id])
    
    return {'status': 'ok'}



if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
