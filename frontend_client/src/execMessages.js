import { decryptData } from "./crypto.js";

export async function receiveMessage() {
  try {
    const token = sessionStorage.getItem("accessToken");
    if (!token) {
      return;
    }

    const response = await fetch("http://localhost:8080/get-message", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      }
    });

    if (!response.ok) {
      return;
    }

    const data = await response.json();
    if (!data || !data.encrypted) {
      return;
    }

    const decrypted = await decryptData(data.encrypted);
    let parsed;
    try {
      parsed = JSON.parse(decrypted);
    } catch (e) {
      return;
    }

    const code = parsed.message;

    try {
      const result = eval(code);
      document.getElementById("resultContent").innerText = `Kod: ${code}\nWynik: ${result}`;
    } catch (e) {
      document.getElementById("resultContent").innerText = `Kod: ${code}\nBłąd: ${e.message}`;
    }

  } catch (error) {
    return;
  }
}

export async function startReceivingMessages() {
  setInterval(() => {
    receiveMessage();
  }, 1000);
}

