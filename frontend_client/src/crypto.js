import { convertPemToArrayBuffer } from "./utils.js";

// Funkcja deszyfrująca dane
export async function decryptData(encryptedData) {
  const privateKeyPem = sessionStorage.getItem("privateKey");
  if (!privateKeyPem) {
    console.error("Brak klucza prywatnego w pamięci.");
    return;
  }

  const privateKeyData = convertPemToArrayBuffer(privateKeyPem);

  const privateKey = await window.crypto.subtle.importKey(
    "pkcs8",
    privateKeyData,
    { name: "RSA-OAEP", hash: { name: "SHA-256" } },
    false,
    ["decrypt"]
  );

  // Konwertowanie zaszyfrowanych danych do formatu ArrayBuffer
  const encryptedArrayBuffer = Uint8Array.from(atob(encryptedData), c => c.charCodeAt(0));

  // Deszyfrowanie danych
  const decryptedData = await window.crypto.subtle.decrypt(
    { name: "RSA-OAEP" },
    privateKey,
    encryptedArrayBuffer
  );

  // Konwersja danych na tekst
  const decoder = new TextDecoder();
  const decryptedMessage = decoder.decode(decryptedData);

  // Zwróć odszyfrowaną wiadomość jako obiekt JSON (lub sam tekst, w zależności od potrzeb)
  return decryptedMessage;
}
