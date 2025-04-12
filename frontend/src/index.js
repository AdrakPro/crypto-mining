const SERVER_BASE_URL = "http://127.0.0.1:8080"; // Backend server URL

// Authentication
export async function authenticate(username, password) {
  const response = await fetch(`${SERVER_BASE_URL}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username: username,   // CLIENT_USERNAME=admin
      password: password    // CLIENT_PASSWORD=8DkAHF)1-kS3c^13IAeC.L.4JrH0\.>U\,f
    }),
  });

  if (!response.ok) {
    alert("Authentication failed");
    return null;
  }

  const data = await response.json();
  return data.access_token;
}

// Fetch task
export async function getTask(token) {
  const response = await fetch(`${SERVER_BASE_URL}/task`, {
    method: "GET",
    headers: {
      "Authorization": `Bearer ${token}`
    }
  });

  if (!response.ok) {
    alert("Failed to fetch task");
    return null;
  }

  const task = await response.json();
  return task;
}

// Submit result
export async function submitResult(token, sum) {
  const response = await fetch(`${SERVER_BASE_URL}/result`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    },
    body: JSON.stringify({ sum })
  });

  if (!response.ok) {
    alert("Failed to submit result");
    return;
  }

  const data = await response.json();
  return data;
}
