console.log('game_mode_1_2.js загружен');

const minRange = window.minRange;
const maxRange = window.maxRange;
let gameId = null;

document.getElementById('min-range-setup').textContent = minRange;
document.getElementById('max-range-setup').textContent = maxRange;

document.getElementById('start-button').onclick = startGame;


function startGame() {
  const secret = Number(document.getElementById('user-secret').value);
  if (isNaN(secret) || secret < minRange || secret > maxRange) {
    alert(`Введите число от ${minRange} до ${maxRange}`);
    return;
  }

  document.getElementById('secret-number').textContent = `Загаданное число: ${secret}`;
  
  fetch('/start_game_1_2', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ secret, min_range: minRange, max_range: maxRange })
  })
    .then(res => res.json())
    .then(data => {
      if (data.error) {
        alert(data.error);
        return;
      }
      gameId = data.game_id;
	  
      document.getElementById('setup').style.display = 'none';
	  document.getElementById('game').style.display = 'block';
	  
      appendToChat("Компьютер", data.question);
    });
}

function processAnswer() {
	console.log('processAnswer вызвана');
	
  const answerInput = document.getElementById('answer');
  const answer = answerInput.value.trim().toLowerCase();

  if (answer !== 'да' && answer !== 'нет') {
    alert('Пожалуйста, введите "да" или "нет"');
    return;
  }

  appendToChat("Вы", answer);
  answerInput.value = '';

  fetch('/answer_1_2', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ game_id: gameId, answer })
  })
    .then(res => res.json())
    .then(data => {
		console.log('Ответ сервера:', data); // отладка
	  if (data.error) {
		alert(data.error);
		return;
	  }

	  appendToChat("Компьютер", data.response);

	  // Предположим, что сервер возвращает finished === true и number — угаданное число
	  if (data.done) {
		  disableInput();
		  console.log('Игра закончена, вызываю showResultBanner с результатом:', data.response);

		  // В data.response содержится текст: "Ура! Я угадала!" или "О нет, я ошиблась"
		  // Используем startsWith чтобы проверить
		  const success = data.response.startsWith("Ура");
		  showResultBanner(success);

		  if (data.number !== undefined) {
			document.getElementById('secret-number').textContent = `Компьютер угадал: ${data.number}`;
		  }
		}
	});
}

function appendToChat(sender, text) {
  const messages = document.getElementById('messages');
  const div = document.createElement('div');
  div.innerHTML = `<strong>${sender}:</strong> ${text}`;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
}

function exitGame() {
  window.location.href = '/';
}

function disableInput() {
  console.log('Выключаю ввод');
  document.getElementById('answer').disabled = true;
  document.getElementById('send-button').disabled = true;
}

function showResultBanner(success) {
	console.log('showResultBanner вызвана');

  const container = document.getElementById('result-banner-container');
  container.innerHTML = '';

  const banner = document.createElement('div');
  banner.className = 'result-banner';
  banner.innerText = success ? 'Система угадала число!' : 'Система не угадала число.';
  banner.style.marginTop = '20px';
  banner.style.padding = '10px';
  banner.style.backgroundColor = success ? '#d4edda' : '#f8d7da';
  banner.style.color = success ? '#155724' : '#721c24';
  banner.style.border = '1px solid';
  banner.style.borderColor = success ? '#c3e6cb' : '#f5c6cb';
  banner.style.borderRadius = '5px';

  container.appendChild(banner);
}
document.getElementById('send-button').addEventListener('click', processAnswer);




