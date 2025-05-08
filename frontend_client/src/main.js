const backendUrl = "http://localhost:8080"; // Zakładamy, że backend działa tu

function showRegister() {
  document.getElementById("registerForm").style.display = "block";
}

function showLogin() {
  alert("Funkcja logowania będzie dodana później.");
}

// Obsługa rejestracji
document.getElementById("formRegister").addEventListener("submit", async (e) => {
  e.preventDefault();

  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;
  const publicKey = document.getElementById("publicKey").value;

  const response = await fetch(`${backendUrl}/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      username,
      password,
      public_key: publicKey
    })
  });

  const msg = document.getElementById("registerMessage");
  if (response.ok) {
    const data = await response.json();
    msg.innerText = data.msg;
    msg.style.color = "green";
  } else {
    const error = await response.json();
    msg.innerText = error.detail;
    msg.style.color = "red";
  }
});

