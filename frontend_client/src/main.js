const backendUrl = "http://localhost:8080";

function showRegister() {
  document.getElementById("registerForm").style.display = "block";
  document.getElementById("loginForm").style.display = "none";
}

function showLogin() {
  document.getElementById("registerForm").style.display = "none";
  document.getElementById("loginForm").style.display = "block";
}

document.getElementById("formRegister").addEventListener("submit", async (e) => {
  e.preventDefault();

  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;
  const msg = document.getElementById("registerMessage");

  try {
    const keyPair = await window.crypto.subtle.generateKey(
      {
        name: "RSA-OAEP",
        modulusLength: 2048,
        publicExponent: new Uint8Array([1, 0, 1]),
        hash: "SHA-256",
      },
      true,
      ["encrypt", "decrypt"]
    );

    const publicKeyData = await window.crypto.subtle.exportKey("spki", keyPair.publicKey);
    const privateKeyData = await window.crypto.subtle.exportKey("pkcs8", keyPair.privateKey);

    const publicKeyPem = convertToPem(publicKeyData, "PUBLIC KEY");
    const privateKeyPem = convertToPem(privateKeyData, "PRIVATE KEY");

    const response = await fetch(`${backendUrl}/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        username,
        password,
        public_key: publicKeyPem
      })
    });

    if (response.ok) {
      const data = await response.json();
      msg.innerText = data.msg;
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
});


// Funkcja logowania
document.getElementById("formLogin").addEventListener("submit", async (e) => {
  e.preventDefault();

  const username = document.getElementById("loginUsername").value;
  const password = document.getElementById("loginPassword").value;
  const privateKeyPem = document.getElementById("loginPrivateKey").value; // Klucz prywatny
  const msg = document.getElementById("loginMessage");

  try {
    const response = await fetch(`${backendUrl}/login-db`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        username,
        password
      })
    });

    if (response.ok) {
      const data = await response.json();
      msg.innerText = "Zalogowano pomyślnie (dane zaszyfrowane)";
      msg.style.color = "green";

      // Zapisujemy klucz prywatny w pamięci (localStorage lub sessionStorage)
      sessionStorage.setItem("privateKey", privateKeyPem);

      // Możesz zapisać token zaszyfrowany do localStorage (opcjonalnie):
      localStorage.setItem("encryptedResponse", JSON.stringify(data));

      // Odszyfrowywanie danych po zalogowaniu
      decryptData(data.encryptedMessage);
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
});

// Funkcja odszyfrowywania danych
async function decryptData(encryptedData) {
  const privateKeyPem = sessionStorage.getItem("privateKey"); // Pobieramy klucz prywatny z pamięci
  if (!privateKeyPem) {
    console.error("Brak klucza prywatnego w pamięci.");
    return;
  }

  // Załaduj prywatny klucz z PEM
  const privateKeyData = convertPemToArrayBuffer(privateKeyPem);
  
  const privateKey = await window.crypto.subtle.importKey(
    "pkcs8",
    privateKeyData,
    {
      name: "RSA-OAEP",
      hash: { name: "SHA-256" },
    },
    false,
    ["decrypt"]
  );

  // Odszyfruj dane
  const encryptedArrayBuffer = Uint8Array.from(atob(encryptedData), c => c.charCodeAt(0));
  const decryptedData = await window.crypto.subtle.decrypt(
    {
      name: "RSA-OAEP",
    },
    privateKey,
    encryptedArrayBuffer
  );

  const decoder = new TextDecoder();
  const decryptedMessage = decoder.decode(decryptedData);

  console.log("Odszyfrowana wiadomość:", decryptedMessage);
}

// Konwersja PEM na ArrayBuffer
function convertPemToArrayBuffer(pem) {
  const lines = pem.split("\n").slice(1, -1).join("");
  const binaryString = atob(lines);
  const length = binaryString.length;
  const arrayBuffer = new ArrayBuffer(length);
  const view = new Uint8Array(arrayBuffer);
  for (let i = 0; i < length; i++) {
    view[i] = binaryString.charCodeAt(i);
  }
  return arrayBuffer;
}


function convertToPem(buffer, label) {
  const base64 = window.btoa(String.fromCharCode(...new Uint8Array(buffer)));
  const lines = base64.match(/.{1,64}/g).join("\n");
  return `-----BEGIN ${label}-----\n${lines}\n-----END ${label}-----`;
}

function downloadPrivateKey() {
  const privateKey = document.getElementById("generatedPrivateKey").value;
  const blob = new Blob([privateKey], { type: "application/x-pem-file" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "private_key.pem";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
