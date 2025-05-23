const SERVER_BASE_URL = "http://127.0.0.1:8080";

async function sha256(message) {
  const msgBuffer = new TextEncoder().encode(message);
  const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

async function generateKeyPair() {
  return await window.crypto.subtle.generateKey(
    {
      name: "RSA-OAEP",
      modulusLength: 2048,
      publicExponent: new Uint8Array([0x01, 0x00, 0x01]),
      hash: "SHA-256",
    },
    true,
    ["encrypt", "decrypt"]
  );
}

async function exportPublicKey(key) {
  const exported = await window.crypto.subtle.exportKey("spki", key);
  const exportedAsBuffer = new Uint8Array(exported);
  const base64 = btoa(String.fromCharCode.apply(null, exportedAsBuffer));
  return `-----BEGIN PUBLIC KEY-----\n${base64}\n-----END PUBLIC KEY-----`;
}

async function decryptData(encryptedData, privateKey) {
  const encryptedArray = Uint8Array.from(atob(encryptedData), c => c.charCodeAt(0));
  return await window.crypto.subtle.decrypt(
    { name: "RSA-OAEP" },
    privateKey,
    encryptedArray
  );
}

export async function authenticate(username, password) {
  try {
    const passwordHash = await sha256(password);
    const keyPair = await generateKeyPair();
    const publicKey = await exportPublicKey(keyPair.publicKey);

    const response = await fetch(`${SERVER_BASE_URL}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: username,
        password: passwordHash,
        public_key: publicKey
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Authentication failed");
    }

    const encryptedResponse = await response.json();
    const decryptedData = await decryptData(encryptedResponse.encrypted, keyPair.privateKey);
    const tokenData = JSON.parse(new TextDecoder().decode(decryptedData));

    return {
      access_token: tokenData.access_token,
      keyPair: keyPair
    };
  } catch (error) {
    console.error("Authentication error:", error);
    return null;
  }
}

export async function getTask(token, keyPair) {
  try {
    const response = await fetch(`${SERVER_BASE_URL}/task`, {
      method: "GET",
      headers: { "Authorization": `Bearer ${token}` }
    });

    const encryptedResponse = await response.json();
    const decryptedData = await decryptData(encryptedResponse.encrypted, keyPair.privateKey);
    return JSON.parse(new TextDecoder().decode(decryptedData));
  } catch (error) {
    console.error("Task fetch error:", error);
    return null;
  }
}

export async function submitResult(token, sum, keyPair) {
  try {
    const response = await fetch(`${SERVER_BASE_URL}/result`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify({ sum })
    });

    const encryptedResponse = await response.json();
    const decryptedData = await decryptData(encryptedResponse.encrypted, keyPair.privateKey);
    return JSON.parse(new TextDecoder().decode(decryptedData));
  } catch (error) {
    console.error("Result submission error:", error);
    return null;
  }
}

export async function submitCalculation(token, calc, keyPair) {
  try {
    const response = await fetch(`${SERVER_BASE_URL}/calculation`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify({ calculation: calc })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Calculation failed");
    }

    const responseData = await response.json();

    // Handle encrypted response
    if (responseData.encrypted) {
      const decryptedData = await decryptData(responseData.encrypted, keyPair.privateKey);
      return JSON.parse(new TextDecoder().decode(decryptedData));
    }

    return responseData;

  } catch (error) {
    console.error("Calculation Error:", error);
    return { error: error.message };
  }
}
