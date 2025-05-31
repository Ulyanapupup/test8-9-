const messagesDiv = document.getElementById("messages");
const chatInput = document.getElementById("chat-input");
const numberGrid = document.getElementById("number-grid");
const pageSpan = document.getElementById("page-number");

let currentPage = 0;
const allNumbers = Array.from({ length: 2001 }, (_, i) => i - 1000);
let dimmedNumbers = new Set();

function renderPage() {
  numberGrid.innerHTML = "";
  const half = allNumbers.length / 2;
  const start = currentPage * half;
  const end = start + half;
  const pageNumbers = allNumbers.slice(start, end);

  for (const num of pageNumbers) {
	const el = document.createElement("div");
	el.className = "number";
	if (dimmedNumbers.has(num)) {
	  el.classList.add("dimmed");
	}
	el.textContent = num;
	numberGrid.appendChild(el);
  }

  pageSpan.textContent = currentPage + 1;
}

function nextPage() {
  if (currentPage < 1) {
	currentPage++;
	renderPage();
  }
}

function prevPage() {
  if (currentPage > 0) {
	currentPage--;
	renderPage();
  }
}

renderPage();

// --- ЧАТ ЧЕРЕЗ SOCKET.IO ---
const socket = io();
const sessionId = "{{ session['session_id'] }}";
const room = "{{ room }}";

// После socket = io();
socket.emit("join_game_room", {
  room: room,
  session_id: sessionId
});

function sendMessage() {
    const msg = chatInput.value.trim();
    if (!msg) return;

    // Не добавляем сообщение здесь - оно придет с сервера
    // addMessage("Вы", msg); // УБИРАЕМ ЭТУ СТРОКУ

    // Отправляем на сервер
    socket.emit("chat_message", {
        room: room,
        session_id: sessionId,
        message: msg
    });

    chatInput.value = "";
}

// Добавим логгирование в обработчик question_response
socket.on('question_response', function(data) {
    console.log('Получен ответ на вопрос:', data); // Для отладки
    
    // Добавляем ответ в чат
    addMessage("Система", `На вопрос "${data.question}" ответ: ${data.response}`);
    
    // Затемняем неподходящие числа
    if (data.dim_numbers && data.dim_numbers.length) {
        console.log('Числа для затемнения:', data.dim_numbers); // Для отладки
        data.dim_numbers.forEach(n => dimmedNumbers.add(n));
        renderPage();
    }
});

function addMessage(sender, text) {
  const div = document.createElement("div");
  div.className = "message";
  div.textContent = `${sender}: ${text}`;
  messagesDiv.appendChild(div);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// Получение сообщения от сервера
socket.on("chat_message", function (data) {
  if (data.sender !== "Вы") {
	addMessage(data.sender, data.message);
  }
});

// Поддержка Enter для отправки
chatInput.addEventListener("keydown", function (e) {
  if (e.key === "Enter") sendMessage();
});



// Добавим в конец файла
socket.on('question_response', function(data) {
    // Добавляем ответ в чат
    addMessage("Система", `На вопрос "${data.question}" ответ: ${data.response}`);
    
    // Затемняем неподходящие числа
    if (data.dim_numbers && data.dim_numbers.length) {
        data.dim_numbers.forEach(n => dimmedNumbers.add(n));
        renderPage();
    }
});

socket.on('game_won', function(data) {
    if (data.winner === sessionId) {
        showModal(
            "🎉 Победа! 🎉",
            `Вы угадали число ${data.secret}!`,
            "Молодец! Вы настоящий мастер чисел!",
            "Играть снова"
        );
    } else {
        showModal(
            "Игра окончена",
            `Соперник угадал число ${data.secret}.`,
            "В следующий раз вам обязательно повезет!",
            "Новая игра"
        );
    }
});

function showModal(title, message, subtitle, buttonText) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content">
            <h2 class="modal-title">${title}</h2>
            <p>${message}</p>
            <p><small>${subtitle}</small></p>
            <button class="modal-button" onclick="location.reload()">${buttonText}</button>
        </div>
    `;
    document.body.appendChild(modal);
}

function checkForQuestion(message) {
    const questionPatterns = [
        /число (больше|меньше) -?\d+\??/i,
        /число (простое|четное|нечетное|двузначное|однозначное|трехзначное|положительное|отрицательное)\??/i,
        /число является (квадратом|кубом)\??/i,
        /это число -?\d+\??/i
    ];
    
    return questionPatterns.some(pattern => pattern.test(message));
}





// Добавим проверку перед затемнением

function renderPage() {
    console.log('Рендерим страницу, затемненные числа:', Array.from(dimmedNumbers)); // Для отладки
    numberGrid.innerHTML = "";
    const half = allNumbers.length / 2;
    const start = currentPage * half;
    const end = start + half;
    const pageNumbers = allNumbers.slice(start, end);

    for (const num of pageNumbers) {
        const el = document.createElement("div");
        el.className = "number";
        if (dimmedNumbers.has(num)) {
            el.classList.add("dimmed");
            console.log('Затемняем число:', num); // Для отладки
        }
        el.textContent = num;
        numberGrid.appendChild(el);
    }

    pageSpan.textContent = currentPage + 1;
}