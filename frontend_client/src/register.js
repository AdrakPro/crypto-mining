import { convertToPem } from "./utils.js";

const backendUrl = "http://localhost:8080";

export async function registerUser(e) {
  e.preventDefault();

  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;
  const msg = document.getElementById("registerMessage");

  try {
    const keyPair = await window.crypto.subtle.generateKey({
      name: "RSA-OAEP",
      modulusLength: 2048,
      publicExponent: new Uint8Array([1, 0, 1]),
      hash: "SHA-256",
    }, true, ["encrypt", "decrypt"]);

    const publicKeyData = await window.crypto.subtle.exportKey("spki", keyPair.publicKey);
    const privateKeyData = await window.crypto.subtle.exportKey("pkcs8", keyPair.privateKey);

    const publicKeyPem = convertToPem(publicKeyData, "PUBLIC KEY");
    const privateKeyPem = convertToPem(privateKeyData, "PRIVATE KEY");

    const response = await fetch(`${backendUrl}/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password, public_key: publicKeyPem })
    });

    if (response.ok) {
      const data = await response.json();
      msg.innerText = data.status;
      msg.style.color = "green";

      document.getElementById("generatedPublicKey").value = publicKeyPem;
      document.getElementById("generatedPrivateKey").value = privateKeyPem;
      document.getElementById("keysDisplay").style.display = "block";

      alert("Zapisz swój klucz prywatny – nie będzie już dostępny!");
    } else {
      const error = await response.json();
      msg.innerText = error.detail;
      msg.style.color = "red";
    }
  } catch (err) {
    console.error("Błąd rejestracji:", err);
    msg.innerText = "Wystąpił błąd podczas rejestracji.";
    msg.style.color = "red";
  }
}
window.downloadPrivateKey = function () {
  const privateKey = document.getElementById("generatedPrivateKey").value;

  if (!privateKey) {
    alert("Brak klucza prywatnego do pobrania!");
    return;
  }

  const blob = new Blob([privateKey], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = "private_key.pem";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);

  URL.revokeObjectURL(url);
};
