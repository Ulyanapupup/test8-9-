const messagesDiv = document.getElementById("messages");
const chatInput = document.getElementById("chat-input");
const statusP = document.getElementById("status");

let secret = null;

/ Обновим функцию confirmNumber
function confirmNumber() {
    const num = parseInt(document.getElementById("secret-number").value);
    if (num >= -1000 && num <= 1000) {
        secret = num;
        statusP.textContent = `Вы загадали: ${secret}`;
        
        // Отправляем число на сервер
        socket.emit("set_secret_number", {
            room: room,
            secret_number: secret
        });
    } else {
        alert("Введите число в диапазоне -1000 до 1000");
    }
}

// --- ЧАТ С SOCKET.IO ---
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

  // Отправляем на сервер
  socket.emit("chat_message", {
	room: room,
	session_id: sessionId,
	message: msg
  });

  addMessage("Вы", msg);
  chatInput.value = "";
}

function addMessage(sender, text) {
  const div = document.createElement("div");
  div.className = "message";
  div.textContent = `${sender}: ${text}`;
  messagesDiv.appendChild(div);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

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

socket.on("chat_message", function (data) {
  if (data.sender !== "Вы") {
	addMessage(data.sender, data.message);
  }
});

chatInput.addEventListener("keydown", function (e) {
  if (e.key === "Enter") sendMessage();
});

// Добавим обработчик для вопросов
socket.on('question_response', function(data) {
  addMessage("Система", `На вопрос "${data.question}" ответ: ${data.response}`);
});

// Добавим обработчик победы
socket.on('game_won', function(data) {
  showModal(
    data.winner === sessionId ? "Вы проиграли" : "Игра окончена",
    `Число было угадано: ${data.secret}`,
    data.winner === sessionId ? "Попробуйте еще раз!" : "Хорошая игра!",
    "Новая игра"
  );
});

socket.on('secret_number_set', function(data) {
    statusP.textContent = `Вы загадали: ${data.secret_number}`;
});