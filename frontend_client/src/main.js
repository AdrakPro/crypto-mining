import { decryptData } from "./crypto.js";
import { receiveMessage } from "./execMessages.js";
import { registerUser } from "./register.js"; // Import rejestracji
import { loginUser } from "./login.js";

const backendUrl = "http://0.0.0.0:8080";
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

document.getElementById("loginBtn").addEventListener("click", withCooldown(loginUser, "loginBtn"));
document.getElementById("formRegister").addEventListener("submit", withCooldown(registerUser, "formRegister"));

window.showLogin = function () {
  document.getElementById("loginForm").style.display = "block";
  document.getElementById("registerForm").style.display = "none";
  document.getElementById("resultDisplay").style.display = "none";
};

window.showRegister = function () {
  document.getElementById("loginForm").style.display = "none";
  document.getElementById("registerForm").style.display = "block";
  document.getElementById("resultDisplay").style.display = "none";
};
