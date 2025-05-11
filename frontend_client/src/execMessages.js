import { decryptData } from "./crypto.js";

export async function receiveMessage() {
  try {
    const token = sessionStorage.getItem("accessToken")
    if (!token) {
      console.error("Brak tokenu dostępu.");
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
      const errorData = await response.json();
      console.error("Błąd pobierania wiadomości:", errorData.detail || response.status);
      return;
    }

    const data = await response.json();
    const encryptedMessage = data.encrypted;

    if (!encryptedMessage) {
      console.error("Brak danych zaszyfrowanych w odpowiedzi.");
      return;
    }

    const decrypted = await decryptData(encryptedMessage);
    document.getElementById("resultContent").innerText = decrypted;

    console.log("Odebrana wiadomość:", decrypted);


  try {
    const result = eval(decrypted); // ⚠️ Uwaga: używaj tylko jeśli masz 100% kontroli nad wiadomościami
    console.log("Wynik wykonania kodu:", result);
    document.getElementById("resultContent").innerText = `Kod: ${decrypted}\nWynik: ${result}`;
  } catch (e) {
    console.error("Błąd wykonania kodu:", e);
    document.getElementById("resultContent").innerText = `Kod: ${decrypted}\nBłąd: ${e.message}`;
  }


  } catch (error) {
    console.error("Błąd podczas odbierania wiadomości:", error);
  }
}




// Uruchomienie cyklicznego odbierania wiadomości
export async function startReceivingMessages() {
  setInterval(() => {
    receiveMessage();
  }, 1000); // Co 5 sekund pobieraj nowe wiadomości
}
