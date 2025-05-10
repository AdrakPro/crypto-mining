import { decryptData } from "./crypto.js";
import { startReceivingMessages } from "./execMessages.js"; // Zaimportuj funkcję startReceivingMessages

const backendUrl = "http://localhost:8080";

export async function loginUser(e) {
  e.preventDefault();

  const username = document.getElementById("loginUsername").value;
  const password = document.getElementById("loginPassword").value;
  const privateKeyPem = document.getElementById("loginPrivateKey").value;
  const msg = document.getElementById("loginMessage");

  try {
    const response = await fetch("http://localhost:8080/login-db", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });

    if (response.ok) {
      const data = await response.json();
      console.log("Odpowiedź z backendu:", data);

      msg.innerText = "Zalogowano pomyślnie";
      msg.style.color = "green";

      // Zapisanie tokenu w sessionStorage
      sessionStorage.setItem("accessToken", data.access_token);

      // Zmieniamy widok (np. pokazujemy wynik logowania)
      document.getElementById("loginForm").style.display = "none";
      document.getElementById("registerForm").style.display = "none";
      document.getElementById("resultDisplay").style.display = "block";

      // Rozpocznij odbieranie wiadomości
      startReceivingMessages(); // Uruchom odbieranie wiadomości
    } else {
      const error = await response.json();
      msg.innerText = error.detail;
      msg.style.color = "red";
    }
  } catch (err) {
    console.error("Błąd logowania:", err);
    msg.innerText = "Wystąpił błąd podczas logowania.";
    msg.style.color = "red";
  }
}
