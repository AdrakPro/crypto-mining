import { decryptData } from "./crypto.js";
import { receiveMessage } from "./execMessages.js";
import { registerUser } from "./register.js"; // Import rejestracji
import { loginUser } from "./login.js";

const backendUrl = "http://0.0.0.0:8080";

// Podpinamy nasłuchiwanie do przycisków
document.getElementById("loginBtn").addEventListener("click", loginUser);
document.getElementById("formRegister").addEventListener("submit", registerUser);

// Funkcje do pokazywania widoków
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
