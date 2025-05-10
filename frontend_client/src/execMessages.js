// Funkcja do odbierania wiadomości
export async function receiveMessage() {
  try {
    const accessToken = sessionStorage.getItem("accessToken");

    if (!accessToken) {
      console.error("Brak tokenu dostępu w pamięci.");
      return;
    }

    // Wysyłamy token w nagłówkach autentykacji
    const response = await fetch("http://localhost:8080/get-message", {
      method: "GET", // Możesz użyć POST, jeśli musisz wysłać dodatkowe dane
      headers: {
        "Authorization": `Bearer ${accessToken}`
      }
    });

    if (response.ok) {
      const data = await response.json();
      console.log("Otrzymana wiadomość:", data.message);

      // Wyświetlamy wiadomość w interfejsie
      document.getElementById("resultContent").innerText = data.message;
    } else {
      console.error("Błąd pobierania wiadomości:", response.status);
    }
  } catch (error) {
    console.error("Błąd podczas odbierania wiadomości:", error);
  }
}

// Uruchomienie cyklicznego odbierania wiadomości
export async function startReceivingMessages() {
  setInterval(() => {
    receiveMessage();
  }, 5000); // Co 5 sekund pobieraj nowe wiadomości
}
