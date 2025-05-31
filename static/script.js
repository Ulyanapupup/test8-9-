const socket = io();

socket.on('message', (msg) => {
  const div = document.createElement('div');
  div.textContent = msg;
  document.getElementById('messages').appendChild(div);
});

function ask() {
  const input = document.getElementById('question');
  fetch('/ask', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({question: input.value})
  })
  .then(response => response.json())
  .then(data => {
    document.getElementById('answer').textContent = data.answer;
    socket.send(input.value);
    input.value = '';
  });
}
