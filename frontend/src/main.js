import {
  authenticate,
  getTask,
  submitResult,
  getSessions,
  sendMessage,
  broadcastTask,
  getBroadcastHistory
} from './index.js';

document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("login-form");
  const taskDashboard = document.getElementById("task-dashboard");
  const usernameInput = document.getElementById("username");
  const passwordInput = document.getElementById("password");
  const loginButton = document.getElementById("login-btn");
  const sendTasksButton = document.getElementById("get-task");
  const taskContainer = document.getElementById("task-container");
  const responseContainer = document.getElementById("response");
  const taskHistoryContainer = document.getElementById("task-history");
  const loadSessionsButton = document.getElementById("load-sessions");
  const sessionsList = document.getElementById("sessions-list");
  const userSelect = document.getElementById("user-select");
  const messageInput = document.getElementById("message-input");
  const sendMessageButton = document.getElementById("send-message");
  const messageResponse = document.getElementById("message-response");
  const broadcastTaskButton = document.getElementById("broadcast-task");
  const refreshHistoryButton = document.getElementById("refresh-history");
  const historyTableBody = document.getElementById("history-body");
  const broadcastResponse = document.getElementById("broadcast-response");

  let currentToken = null;
  let currentKeyPair = null;
  let currentTask = null;

  broadcastTaskButton.addEventListener("click", async () => {
    if (!currentToken) {
      broadcastResponse.textContent = "Please log in first.";
      return;
    }

    try {
      const response = await broadcastTask(currentToken);
      if (response) {
        broadcastResponse.textContent = `Task broadcasted! Task ID: ${response.task_id}`;
        // Refresh history after broadcasting
        await loadBroadcastHistory();
      } else {
        broadcastResponse.textContent = "Broadcast failed.";
      }
    } catch (error) {
      broadcastResponse.textContent = `Error: ${error.message}`;
    }
  });

  // Refresh history button
  refreshHistoryButton.addEventListener("click", async () => {
    await loadBroadcastHistory();
  });

  // Load broadcast history
  async function loadBroadcastHistory() {
    if (!currentToken) return;

    try {
      const history = await getBroadcastHistory(currentToken);
      renderHistoryTable(history);
    } catch (error) {
      historyTableBody.innerHTML = `<tr><td colspan="7">Error loading history: ${error.message}</td></tr>`;
    }
  }

  // Render history table
  function renderHistoryTable(history) {
    if (history.length === 0) {
      historyTableBody.innerHTML = '<tr><td colspan="7">No broadcast history available</td></tr>';
      return;
    }

    historyTableBody.innerHTML = '';

    history.forEach(task => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td>${task.id}</td>
        <td>${task.content}</td>
        <td>${task.operation}</td>
        <td>${task.created_at}</td>
        <td>${task.total_submissions}</td>
        <td>${task.correct_count}</td>
        <td>${task.accuracy}%</td>
      `;
      historyTableBody.appendChild(row);
    });
  }

  loginButton.addEventListener("click", async (e) => {
    e.preventDefault();
    const authData = await authenticate(usernameInput.value, passwordInput.value);

    if (authData) {
      currentToken = authData.access_token;
      currentKeyPair = authData.keyPair;
      loginForm.style.display = "none";
      taskDashboard.style.display = "block";

      await loadBroadcastHistory();
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
      const response = await sendMessage(currentToken, recipient, message)
      messageInput.value = ""; ;
      messageResponse.textContent = `Wysłano: ${response.status || "OK"}`;
    } catch (err) {
      messageResponse.textContent = `Błąd: ${err.message}`;
    }
  });
});
