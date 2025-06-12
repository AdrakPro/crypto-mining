import { decryptData } from "./crypto.js";
import { startReceivingMessages } from "./execMessages.js";
import CONFIG from "./config.js"

const backendUrl = CONFIG.BACKEND_URL; 

export async function loginUser(e) {
  e.preventDefault();

  const username = document.getElementById("loginUsername").value;
  const password = document.getElementById("loginPassword").value;
  const privateKeyPem = document.getElementById("loginPrivateKey").value;
  
  sessionStorage.setItem("privateKey", privateKeyPem);
  sessionStorage.setItem("username", username);

  const msg = document.getElementById("loginMessage");

  try {
    const response = await fetch(`${backendUrl}/login-db`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });

    if (response.ok) {
      const data = await response.json();
      console.log("Odpowiedź z backendu:", data);  // Sprawdźmy, co zawiera odpowiedź

      // Sprawdźmy, czy odpowiedź zawiera dane zaszyfrowane
      if (data.encrypted) {
        console.log("Zaszyfrowana odpowiedź:", data.encrypted);

        // Odszyfrowanie danych
        const decrypted = await decryptData(data.encrypted);
        console.log("Odszyfrowana odpowiedź:", decrypted);

        // Przekształć dane na obiekt, jeżeli jest to JSON
        try {
          const parsedData = JSON.parse(decrypted);
          console.log("Dane po deszyfrowaniu:", parsedData);
          
          // Sprawdź token
          if (parsedData.access_token) {
            sessionStorage.setItem("accessToken", parsedData.access_token);
            console.log("Token zapisany w sessionStorage:", sessionStorage.getItem("accessToken"));
          } else {
            console.error("Brak tokenu w odpowiedzi z serwera.");
          }
          
          // Zmieniamy widok
          document.getElementById("loginForm").style.display = "none";
          document.getElementById("registerForm").style.display = "none";
          document.getElementById("menu").style.display = "none";
          document.getElementById("resultDisplay").style.display = "block";
          
          // Rozpocznij odbieranie wiadomości
          startReceivingMessages();

        } catch (err) {
          console.error("Błąd przy deszyfrowaniu danych:", err);
          msg.innerText = "Błąd przy deszyfrowywaniu danych.";
          msg.style.color = "red";
        }
      } else {
        console.error("Brak zaszyfrowanych danych w odpowiedzi.");
        msg.innerText = "Brak zaszyfrowanych danych.";
        msg.style.color = "red";
      }

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
