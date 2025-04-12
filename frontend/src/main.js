import { authenticate, getTask, submitResult } from './index.js';

document.addEventListener("DOMContentLoaded", () => {
  const loginButton = document.getElementById("login-btn");
  const usernameInput = document.getElementById("username");
  const passwordInput = document.getElementById("password");
  const loginForm = document.getElementById("login-form");
  const taskDashboard = document.getElementById("task-dashboard");

  const getTaskButton = document.getElementById("get-task");
  const submitButton = document.getElementById("submit-result");
  const responseContainer = document.getElementById("response");
  const taskHistoryContainer = document.getElementById("task-history");

  let currentTask = null;
  let token = null;

  loginButton.addEventListener("click", async () => {
    const username = usernameInput.value;
    const password = passwordInput.value;

    if (!username || !password) {
      alert("Please enter both username and password.");
      return;
    }

    // Authenticate user
    token = await authenticate(username, password);
    if (!token) return;

    // Hide login form and show task dashboard
    loginForm.style.display = "none";
    taskDashboard.style.display = "block";
  });

  getTaskButton.addEventListener("click", async () => {
    if (!token) return;

    // Fetch a new task
    currentTask = await getTask(token);
    if (!currentTask) return;

    // Display task
    const taskContainer = document.getElementById("task-container");
    taskContainer.innerHTML = `Solve the following task: ${currentTask.a} + ${currentTask.b}`;

    // Show Submit Result button after getting a task
    submitButton.style.display = "inline-block";
    getTaskButton.style.display = "none";
  });

  submitButton.addEventListener("click", async () => {
    if (!currentTask) return;

    const result = currentTask.a + currentTask.b;
    const resultResponse = await submitResult(token, result);

    if (resultResponse) {
      // Display server response
      responseContainer.innerHTML = `Server response: ${JSON.stringify(resultResponse)}`;

      // Add task and result to history
      const historyItem = document.createElement("div");
      historyItem.innerHTML = `Task: ${currentTask.a} + ${currentTask.b} = ${result}, Server response: ${JSON.stringify(resultResponse)}`;
      taskHistoryContainer.appendChild(historyItem);

      // Show Get Task button again after submission
      getTaskButton.style.display = "inline-block";
      submitButton.style.display = "none";
    }
  });
});
