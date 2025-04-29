import { authenticate, getTask, submitResult, submitCalculation} from './index.js';

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
  const calculationForm = document.getElementById("calculation-form");
  const calculationInput = document.getElementById("calculation");
  const calculationButton = document.getElementById("calculation-btn");

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

  calculationButton.addEventListener("click", async (e) => {
    e.preventDefault();
    const calc = calculationInput.value;
    if (!calc) {
      alert("Please enter a calculation.");
      return;
    }

    responseContainer.innerHTML = "Processing...";

    const result = await submitCalculation(currentToken, calc, currentKeyPair);

    if (result && !result.error) {
      // Display the result
      responseContainer.innerHTML = `Calculation Result: ${result.result}`;

      // Optionally add to history
      const historyEntry = document.createElement("div");
      historyEntry.className = "history-entry";
      historyEntry.textContent = `Calculation: ${calc} = ${result.result}`;
      taskHistoryContainer.appendChild(historyEntry);
    } else {
      responseContainer.innerHTML = `Error: ${result?.error || "Unknown error"}`;
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
});
