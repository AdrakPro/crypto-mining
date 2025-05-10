import { authenticate, getTask, submitResult, getSessions, sendMessage } from './index.js';

document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("login-form");
  const taskDashboard = document.getElementById("task-dashboard");
  const usernameInput = document.getElementById("username");
  const passwordInput = document.getElementById("password");
  const loginButton = document.getElementById("login-btn");
  const getTaskButton = document.getElementById("get-task");
  const submitButton = document.getElementById("submit-result");
  const taskContainer = document.getElementById("task-container");
  const responseContainer = document.getElementById("response");
  const taskHistoryContainer = document.getElementById("task-history");
  const loadSessionsButton = document.getElementById("load-sessions");
  const sessionsList = document.getElementById("sessions-list");
  const userSelect = document.getElementById("user-select");
  const messageInput = document.getElementById("message-input");
  const sendMessageButton = document.getElementById("send-message");
  const messageResponse = document.getElementById("message-response");

  let currentToken = null;
  let currentKeyPair = null;
  let currentTask = null;

  loginButton.addEventListener("click", async (e) => {
    e.preventDefault();
    const authData = await authenticate(usernameInput.value, passwordInput.value);

    if (authData) {
      currentToken = authData.access_token;
      currentKeyPair = authData.keyPair;
      loginForm.style.display = "none";
      taskDashboard.style.display = "block";
    }
  });

  getTaskButton.addEventListener("click", async () => {
    const task = await getTask(currentToken, currentKeyPair);

    if (task) {
      currentTask = task;
      taskContainer.innerHTML = `Solve: ${task.a} + ${task.b}`;
      getTaskButton.style.display = "none";
      submitButton.style.display = "inline-block";
    }
  });

  submitButton.addEventListener("click", async () => {
    if (!currentTask) return;

    const result = currentTask.a + currentTask.b;
    const resultData = await submitResult(currentToken, result, currentKeyPair);

    if (resultData) {
      responseContainer.innerHTML = `Status: ${resultData.status}`;

      const historyEntry = document.createElement("div");
      historyEntry.className = "history-entry";
      historyEntry.textContent = `Task: ${currentTask.a} + ${currentTask.b} = ${result} → ${resultData.status}`;
      taskHistoryContainer.appendChild(historyEntry);

      getTaskButton.style.display = "inline-block";
      submitButton.style.display = "none";
      currentTask = null;
    }
  });

  loadSessionsButton.addEventListener("click", async () => {
    const sessions = await getSessions();

    sessionsList.innerHTML = "";
    userSelect.innerHTML = "";

    if (sessions.length === 0) {
      sessionsList.innerHTML = "<li>Brak aktywnych sesji</li>";
      const option = document.createElement("option");
      option.textContent = "Brak aktywnych użytkowników";
      userSelect.appendChild(option);
      return;
    }

    sessions.forEach(session => {
      const li = document.createElement("li");
      li.textContent = `${session.username} @ ${session.ip} - ${session.timestamp}`;
      sessionsList.appendChild(li);

      const option = document.createElement("option");
      option.value = session.username;
      option.textContent = session.username;
      userSelect.appendChild(option);
    });
  });

  sendMessageButton.addEventListener("click", async () => {
    const recipient = userSelect.value;
    const message = messageInput.value;

    if (!recipient || !message) {
      messageResponse.textContent = "Wybierz użytkownika i wpisz wiadomość.";
      return;
    }

    try {
      const response = await sendMessage(recipient, message, currentToken);
      messageResponse.textContent = `Wysłano: ${response.status || "OK"}`;
    } catch (err) {
      messageResponse.textContent = `Błąd: ${err.message}`;
    }
  });
});


