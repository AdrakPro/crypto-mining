import { decryptData } from "./crypto.js";
import { receiveMessage, startReceivingMessages } from "./execMessages.js";
import { registerUser } from "./register.js";
import { loginUser } from "./login.js";
import CONFIG from "./config.js";

const backendUrl = CONFIG.BACKEND_URL;
const COOLDOWN_MS = 3000;

function withCooldown(handler, buttonId, cooldown = COOLDOWN_MS) {
  return function (event) {
    const button = document.getElementById(buttonId);
    if (button.disabled) return;

    button.disabled = true;
    setTimeout(() => {
      button.disabled = false;
    }, cooldown);

    handler(event);
  };
}

const submitAnswerBtn = document.getElementById("submitAnswerBtn");

async function loginUserWrapper(e) {
  await loginUser(e);
  if (sessionStorage.getItem("accessToken")) {
    startReceivingMessages();
    startTaskPolling();
    await getCurrentTask();
  }
}

function startTaskPolling() {
  setInterval(async () => {
    await getCurrentTask();
  }, 5000);
}

async function getCurrentTask() {
  const token = sessionStorage.getItem("accessToken");
  if (!token) return;

  try {
    const response = await fetch(`${backendUrl}/task`, {
      method: "GET",
      headers: { "Authorization": `Bearer ${token}` }
    });

    if (!response.ok) throw new Error("Failed to fetch task");

    const encryptedResponse = await response.json();
    const decrypted = await decryptData(encryptedResponse.encrypted);
    const task = JSON.parse(decrypted);

    if (!window.currentTask || window.currentTask.task_id !== task.task_id) {
      window.currentTask = task;
      renderTask(task);
    }

    return task;
  } catch (error) {
    console.error("Error fetching task:", error);
    return null;
  }
}

function renderTask(task) {
  const taskInfo = document.getElementById("taskInfo");
  const taskForm = document.getElementById("taskForm");

  taskInfo.innerHTML = `
    <p><strong>ID zadania:</strong> ${task.task_id}</p>
    <p><strong>Treść:</strong> ${task.content}</p>
    <p><strong>Liczby:</strong> ${task.a} i ${task.b}</p>
    <p><strong>Operacja:</strong> ${task.operation}</p>
  `;

  taskForm.style.display = "block";
  document.getElementById("answerInput").value = "";
  document.getElementById("taskResult").innerText = "";

  // Re-enable button when a new task arrives
  const submitBtn = document.getElementById("submitAnswerBtn");
  if (submitBtn) {
    submitBtn.disabled = false;
  }
}

async function submitTaskAnswer() {
  const token = sessionStorage.getItem("accessToken");
  if (!token || !window.currentTask) return;

  const answer = parseFloat(document.getElementById("answerInput").value);
  if (isNaN(answer)) {
    document.getElementById("taskResult").innerText = "Proszę wprowadzić poprawną liczbę";
    return;
  }

  try {
    const response = await fetch(`${backendUrl}/task/${window.currentTask.task_id}/result?result=${encodeURIComponent(answer)}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      }
    });

    if (!response.ok) throw new Error('Failed to submit answer');

    const encryptedResponse = await response.json();
    const decrypted = await decryptData(encryptedResponse.encrypted);
    const result = JSON.parse(decrypted);

    document.getElementById("taskResult").innerText =
      result.is_correct ? "Odpowiedź poprawna!" : "Odpowiedź niepoprawna!";

    return result;
  } catch (error) {
    console.error("Error submitting answer:", error);
    document.getElementById("taskResult").innerText = "Błąd przy przesyłaniu odpowiedzi";
    return null;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("loginBtn").addEventListener("click", withCooldown(loginUserWrapper, "loginBtn"));
  document.getElementById("formRegister").addEventListener("submit", withCooldown(registerUser, "formRegister"));

  function showLogin() {
    document.getElementById("loginForm").style.display = "block";
    document.getElementById("registerForm").style.display = "none";
    document.getElementById("resultDisplay").style.display = "none";
  }

  function showRegister() {
    document.getElementById("loginForm").style.display = "none";
    document.getElementById("registerForm").style.display = "block";
    document.getElementById("resultDisplay").style.display = "none";
  }

  document.getElementById("registerBtn").addEventListener("click", showRegister);
  document.getElementById("loginToggleBtn").addEventListener("click", showLogin);

  if (submitAnswerBtn) {
    submitAnswerBtn.addEventListener("click", async () => {
      submitAnswerBtn.disabled = true; // disable after one send
      await submitTaskAnswer();
      // do NOT re-enable here; only re-enabled in renderTask when new task arrives
    });
  }
});
